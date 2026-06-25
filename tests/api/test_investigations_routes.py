from dataclasses import dataclass

from starlette.testclient import TestClient

from telemetry_agents.api.app import create_app
from telemetry_agents.api.dependencies import get_demo_investigation_service
from telemetry_agents.app.demo_investigation_service import (
    DemoInvestigationResult,
    InvestigationRunResult,
)
from telemetry_agents.domain import (
    EvidenceSource,
    HypothesisCategory,
    HypothesisReviewStatus,
    Incident,
    InvestigationHypothesis,
    ReviewedHypothesis,
    TelemetryEvidence,
)
from telemetry_agents.infrastructure.run_registry import InvestigationRunStatus
from telemetry_agents.investigation.evidence_retrieval import (
    CitationMetadata,
    RetrievedEvidence,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength


@dataclass
class FakeDemoInvestigationService:
    start_result: DemoInvestigationResult
    review_result: DemoInvestigationResult | None = None
    read_result: DemoInvestigationResult | None = None
    runs_result: list[InvestigationRunResult] | None = None
    read_run_id: str | None = None
    reviewed_run_id: str | None = None
    reviewed_approved: bool | None = None

    def start(self, case_id: str) -> DemoInvestigationResult:
        return self.start_result

    def review(self, run_id: str, approved: bool) -> DemoInvestigationResult:
        self.reviewed_run_id = run_id
        self.reviewed_approved = approved
        if self.review_result is None:
            raise AssertionError("review_result was not configured")
        return self.review_result

    def read(self, run_id: str) -> DemoInvestigationResult:
        self.read_run_id = run_id
        if self.read_result is None:
            raise AssertionError("read_result was not configured")
        return self.read_result

    def list_runs(self) -> list[InvestigationRunResult]:
        if self.runs_result is None:
            raise AssertionError("runs_result was not configured")
        return self.runs_result


def test_start_investigation_returns_no_human_review_response() -> None:
    service = FakeDemoInvestigationService(
        start_result=_result(human_review_required=False, review_reasons=[])
    )
    app = create_app()
    app.dependency_overrides[get_demo_investigation_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/investigations",
            json={"case_id": "checkout-database-timeout"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["human_review_required"] is False
    assert body["review_reasons"] == []
    assert body["status"] == "completed"
    assert body["warnings"] == []
    assert body["report_ready"] is True
    assert body["hypotheses"][0]["status"] == "accepted"


def test_start_investigation_returns_ui_oriented_incident_hypothesis_and_evidence() -> (
    None
):
    service = FakeDemoInvestigationService(
        start_result=_result(human_review_required=False, review_reasons=[])
    )
    app = create_app()
    app.dependency_overrides[get_demo_investigation_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/investigations",
            json={"case_id": "checkout-database-timeout"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["case_id"] == "checkout-database-timeout"
    assert body["incident"] == {
        "id": "inc-checkout-001",
        "title": "Checkout API latency spike",
        "service": "checkout-api",
        "impact": "medium",
    }
    assert body["top_hypothesis"] == {
        "id": "hyp-001",
        "statement": "Database timeouts are causing checkout latency.",
        "category": "database_failure",
        "confidence": 0.9,
        "review_status": "accepted",
        "evidence_ids": ["log-001"],
    }
    assert body["evidence"] == [
        {
            "evidence_id": "log-001",
            "source": "log",
            "summary": "Checkout API reports database timeout errors.",
            "citation": "sample_data/logs/checkout-api.log:1",
            "strength": "strong",
        }
    ]


def test_review_investigation_delegates_human_approval_decision() -> None:
    service = FakeDemoInvestigationService(
        start_result=_result(human_review_required=True),
        review_result=_result(
            run_id="run-review-001",
            human_review_required=True,
            review_reasons=["high incident impact"],
        ),
    )
    app = create_app()
    app.dependency_overrides[get_demo_investigation_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/investigations/run-review-001/review",
            json={"approved": True},
        )

    assert response.status_code == 202
    assert service.reviewed_run_id == "run-review-001"
    assert service.reviewed_approved is True
    body = response.json()
    assert body["run_id"] == "run-review-001"
    assert body["human_review_required"] is True
    assert body["review_reasons"] == ["high incident impact"]
    assert body["status"] == "completed"
    assert body["report_ready"] is True


def test_get_investigation_delegates_to_read_model() -> None:
    service = FakeDemoInvestigationService(
        start_result=_result(human_review_required=False),
        read_result=_result(
            run_id="run-read-001",
            human_review_required=True,
            review_reasons=["blocked hypothesis"],
            status=InvestigationRunStatus.AWAITING_REVIEW,
            warnings=["critic unavailable"],
            report_ready=False,
        ),
    )
    app = create_app()
    app.dependency_overrides[get_demo_investigation_service] = lambda: service

    with TestClient(app) as client:
        response = client.get("/api/v1/investigations/run-read-001")

    assert response.status_code == 200
    assert service.read_run_id == "run-read-001"
    body = response.json()
    assert body["run_id"] == "run-read-001"
    assert body["human_review_required"] is True
    assert body["review_reasons"] == ["blocked hypothesis"]
    assert body["status"] == "awaiting_review"
    assert body["warnings"] == ["critic unavailable"]
    assert body["report_ready"] is False


def test_list_investigations_returns_run_summaries() -> None:
    service = FakeDemoInvestigationService(
        start_result=_result(human_review_required=False),
        runs_result=[
            InvestigationRunResult(
                run_id="run-history-001",
                case_id="conflicting-evidence",
                demo_provider="fake",
                incident_id="inc-conflicting-evidence-001",
                status=InvestigationRunStatus.AWAITING_REVIEW,
            ),
            InvestigationRunResult(
                run_id="run-history-002",
                case_id="checkout-database-timeout",
                demo_provider="azure",
                incident_id="inc-checkout-001",
                status=InvestigationRunStatus.COMPLETED,
            ),
        ],
    )
    app = create_app()
    app.dependency_overrides[get_demo_investigation_service] = lambda: service

    with TestClient(app) as client:
        response = client.get("/api/v1/investigations")

    assert response.status_code == 200
    assert response.json() == {
        "runs": [
            {
                "run_id": "run-history-001",
                "case_id": "conflicting-evidence",
                "demo_provider": "fake",
                "incident_id": "inc-conflicting-evidence-001",
                "status": "awaiting_review",
            },
            {
                "run_id": "run-history-002",
                "case_id": "checkout-database-timeout",
                "demo_provider": "azure",
                "incident_id": "inc-checkout-001",
                "status": "completed",
            },
        ]
    }


def test_start_investigation_returns_null_top_hypothesis_without_hypotheses() -> None:
    service = FakeDemoInvestigationService(
        start_result=_result(human_review_required=True, hypotheses=[])
    )
    app = create_app()
    app.dependency_overrides[get_demo_investigation_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/investigations",
            json={"case_id": "checkout-database-timeout"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["hypotheses"] == []
    assert body["top_hypothesis"] is None


def _result(
    *,
    run_id: str = "run-001",
    human_review_required: bool,
    hypotheses: list[ReviewedHypothesis] | None = None,
    evidence: list[RetrievedEvidence] | None = None,
    review_reasons: list[str] | None = None,
    status: InvestigationRunStatus = InvestigationRunStatus.COMPLETED,
    warnings: list[str] | None = None,
    report_ready: bool = True,
) -> DemoInvestigationResult:
    return DemoInvestigationResult(
        run_id=run_id,
        case_id="checkout-database-timeout",
        demo_provider="fake",
        incident=Incident.model_validate(
            {
                "incident_id": "inc-checkout-001",
                "title": "Checkout API latency spike",
                "service": "checkout-api",
                "impact": "medium",
                "reported_at": "2026-05-11T10:05:00Z",
                "investigation_window": {
                    "start": "2026-05-11T09:40:00Z",
                    "end": "2026-05-11T10:10:00Z",
                },
                "retrieval": {"query_terms": ["timeout"], "trace_id": "trace-001"},
            }
        ),
        status=status,
        hypotheses=hypotheses
        if hypotheses is not None
        else [
            ReviewedHypothesis(
                hypothesis=InvestigationHypothesis(
                    hypothesis_id="hyp-001",
                    statement="Database timeouts are causing checkout latency.",
                    category=HypothesisCategory.DATABASE_FAILURE,
                    supporting_evidence_ids=["log-001"],
                    confidence=0.9,
                ),
                status=HypothesisReviewStatus.ACCEPTED,
            )
        ],
        evidence=evidence if evidence is not None else [_retrieved_evidence()],
        human_review_required=human_review_required,
        review_reasons=review_reasons or [],
        warnings=warnings or [],
        report_ready=report_ready,
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
