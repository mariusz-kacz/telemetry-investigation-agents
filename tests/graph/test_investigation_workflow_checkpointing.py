from pathlib import Path

import pytest

from telemetry_agents.app.workflow_runner import (
    WorkflowRunRequest,
    WorkflowStateUnavailable,
    build_workflow_service,
)
from telemetry_agents.domain import (
    HypothesisCategory,
    IncidentImpact,
    InvestigationHypothesis,
)
from telemetry_agents.domain.models import (
    EvidenceSource,
    HypothesisCritiqueResult,
    Incident,
    TelemetryEvidence,
)
from telemetry_agents.graph.investigation_workflow import build_investigation_workflow
from telemetry_agents.infrastructure.checkpointing import create_sqlite_checkpointer
from telemetry_agents.infrastructure.run_registry import (
    InvestigationRunRecord,
    create_investigation_run,
    get_investigation_run,
    initialize_run_registry,
    InvestigationRunStatus,
)
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_critic import HypothesisCritiqueRequest
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
)
from telemetry_agents.shared.paths import SAMPLE_DATA_DIR


class FakeHypothesisGenerator:
    def __init__(self, hypotheses: list[InvestigationHypothesis]) -> None:
        self.hypotheses = hypotheses

    def generate(
        self, request: HypothesisGenerationRequest
    ) -> list[InvestigationHypothesis]:
        return self.hypotheses


class FakeHypothesisCritic:
    def __init__(self, result: HypothesisCritiqueResult) -> None:
        self.result = result
        self.request: HypothesisCritiqueRequest | None = None

    def critique(
        self,
        request: HypothesisCritiqueRequest,
    ) -> HypothesisCritiqueResult:
        self.request = request
        return self.result


def _incident() -> Incident:
    return Incident.model_validate(
        {
            "incident_id": "inc-001",
            "title": "Checkout API latency spike",
            "service": "checkout-api",
            "impact": IncidentImpact.MEDIUM,
            "reported_at": "2026-05-11T10:05:00Z",
            "investigation_window": {
                "start": "2026-05-11T09:40:00Z",
                "end": "2026-05-11T10:10:00Z",
            },
            "retrieval": {"query_terms": ["timeout"], "trace_id": "trace-001"},
        }
    )


def _retrieved_evidence() -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence=TelemetryEvidence(
            evidence_id="log-001",
            source=EvidenceSource.LOG,
            summary="Checkout API reports database timeout errors.",
            citation="sample_data/logs/checkout-api.log:1",
            service="checkout-api",
        ),
        citation=CitationMetadata(
            source_file="sample_data/logs/checkout-api.log",
            line_number=1,
            service="checkout-api",
            selection_reason="Matched incident query terms.",
        ),
        strength=EvidenceStrength.STRONG,
        relevance_score=1.0,
    )


def build_sqlite_checkpointed_investigation_workflow_graph(db_path: Path):
    checkpointer = create_sqlite_checkpointer(db_path)
    fake_generator = FakeHypothesisGenerator([])
    fake_critic = FakeHypothesisCritic(HypothesisCritiqueResult())

    return build_investigation_workflow(
        generator=fake_generator,
        critic=fake_critic,
        checkpointer=checkpointer,
    )


def test_checkpointed_graph_requires_thread_id_and_can_be_invoked(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "checkpoints.sqlite"
    graph = build_sqlite_checkpointed_investigation_workflow_graph(db_path)

    result = graph.invoke(
        {
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        },
        config={"configurable": {"thread_id": "run-001"}},
    )

    assert result["validation_result"] is not None


def test_registered_run_id_is_used_as_checkpoint_thread_id(tmp_path: Path) -> None:
    db_path = tmp_path / "checkpoints.sqlite"
    graph = build_sqlite_checkpointed_investigation_workflow_graph(db_path)

    initialize_run_registry(db_path)
    create_investigation_run(
        db_path,
        run_id="run-001",
        case_id="case-001",
        incident_id="incident-checkout-timeout",
    )

    graph.invoke(
        {
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        },
        config={"configurable": {"thread_id": "run-001"}},
    )

    stored = get_investigation_run(db_path, run_id="run-001")
    assert stored == InvestigationRunRecord(
        run_id="run-001",
        case_id="case-001",
        incident_id="incident-checkout-timeout",
        status=InvestigationRunStatus.PENDING,
        demo_provider="unknown",
    )

    state = graph.get_state(
        config={"configurable": {"thread_id": "run-001"}},
    )
    assert state.values["validation_result"] is not None


def test_checkpointed_state_can_be_read_by_new_graph_instance(tmp_path: Path) -> None:
    db_path = tmp_path / "checkpoints.sqlite"
    graph_old = build_sqlite_checkpointed_investigation_workflow_graph(db_path)

    initialize_run_registry(db_path)
    create_investigation_run(
        db_path,
        run_id="run-001",
        case_id="case-001",
        incident_id="incident-checkout-timeout",
    )

    graph_old.invoke(
        {
            "normalized_incident": _incident(),
            "collected_evidence": [_retrieved_evidence()],
        },
        config={"configurable": {"thread_id": "run-001"}},
    )

    state = graph_old.get_state(
        config={"configurable": {"thread_id": "run-001"}},
    )

    assert state.values["validation_result"] is not None

    graph_new = build_sqlite_checkpointed_investigation_workflow_graph(db_path)

    state = graph_new.get_state(
        config={"configurable": {"thread_id": "run-001"}},
    )

    assert state.values["validation_result"] is not None


def test_workflow_restore_raises_clear_error_for_missing_checkpoint_state(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "checkpoints.sqlite"
    checkpointer = create_sqlite_checkpointer(db_path)
    workflow = build_workflow_service(
        generator=FakeHypothesisGenerator([]),
        critic=FakeHypothesisCritic(HypothesisCritiqueResult()),
        checkpointer=checkpointer,
    )

    with pytest.raises(
        WorkflowStateUnavailable,
        match="Workflow state for run missing-run is unavailable or incomplete.",
    ):
        workflow.read_state("missing-run")


def test_workflow_run_result_includes_final_report_for_completed_run(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "checkpoints.sqlite"
    checkpointer = create_sqlite_checkpointer(db_path)
    workflow = build_workflow_service(
        generator=FakeHypothesisGenerator(
            [
                InvestigationHypothesis(
                    hypothesis_id="hyp-001",
                    statement="Database timeouts are causing checkout latency.",
                    category=HypothesisCategory.DATABASE_FAILURE,
                    supporting_evidence_ids=["log-checkout-api-1"],
                    confidence=0.9,
                )
            ]
        ),
        critic=FakeHypothesisCritic(HypothesisCritiqueResult()),
        checkpointer=checkpointer,
    )

    result = workflow.run(
        WorkflowRunRequest(
            run_id="run-final-report-001",
            case_id="checkout-database-timeout",
            incident=_incident(),
            data_root=SAMPLE_DATA_DIR,
        )
    )

    assert result.report_ready is True
    assert result.final_report is not None
    assert (
        result.final_report.summary == "Database timeouts are causing checkout latency."
    )
    assert result.final_report.selected_hypothesis_id == "hyp-001"
    assert [
        citation.evidence_id for citation in result.final_report.evidence_citations
    ] == ["log-checkout-api-1"]
