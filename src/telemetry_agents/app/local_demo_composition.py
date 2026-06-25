from telemetry_agents.app.config import Settings
from telemetry_agents.app.demo_investigation_service import (
    DemoInvestigationService,
    build_demo_investigation_service,
)
from telemetry_agents.app.workflow_runner import build_workflow_service
from telemetry_agents.domain import (
    HypothesisCategory,
    HypothesisCritiqueResult,
    Incident,
    InvestigationHypothesis,
)
from telemetry_agents.infrastructure.checkpointing import create_sqlite_checkpointer
from telemetry_agents.infrastructure.run_registry import initialize_run_registry
from telemetry_agents.investigation.evidence_retrieval import RetrievedEvidence
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.investigation.hypothesis_critic import HypothesisCritiqueRequest
from telemetry_agents.investigation.hypothesis_generation import (
    HypothesisGenerationRequest,
)


class LocalDemoHypothesisGenerator:
    """Deterministic demo generator for running the API/UI without live LLM calls."""

    def generate(
        self,
        request: HypothesisGenerationRequest,
    ) -> list[InvestigationHypothesis]:
        return [
            _hypothesis_for_incident(
                incident=request.incident,
                evidence=request.evidence,
            )
        ]


class LocalDemoHypothesisCritic:
    """Deterministic no-op critic for local portfolio demos."""

    def critique(
        self,
        request: HypothesisCritiqueRequest,
    ) -> HypothesisCritiqueResult:
        return HypothesisCritiqueResult()


def build_local_demo_investigation_service(
    settings: Settings,
) -> DemoInvestigationService:
    checkpointer = create_sqlite_checkpointer(settings.checkpoint_db_path)
    workflow = build_workflow_service(
        generator=LocalDemoHypothesisGenerator(),
        critic=LocalDemoHypothesisCritic(),
        checkpointer=checkpointer,
    )

    initialize_run_registry(settings.run_registry_db_path)

    return build_demo_investigation_service(
        run_workflow=workflow.run,
        resume_workflow=workflow.resume,
        read_workflow_state=workflow.read_state,
        demo_data_root=settings.data_root,
        run_registry_db_path=settings.run_registry_db_path,
        demo_provider="fake",
    )


def _hypothesis_for_incident(
    *,
    incident: Incident,
    evidence: list[RetrievedEvidence],
) -> InvestigationHypothesis:
    supporting_evidence_ids = _usable_evidence_ids(evidence)
    incident_id = incident.incident_id

    if "downstream" in incident_id:
        return InvestigationHypothesis(
            hypothesis_id="local-hyp-downstream-dependency",
            statement=(
                "Checkout latency is most consistent with the downstream "
                "shipping-rate-service path being slow during the incident window."
            ),
            category=HypothesisCategory.DOWNSTREAM_DEPENDENCY_FAILURE,
            supporting_evidence_ids=supporting_evidence_ids,
            confidence=0.86,
        )

    if "conflicting" in incident_id:
        return InvestigationHypothesis(
            hypothesis_id="local-hyp-conflicting-evidence",
            statement=(
                "The retrieved telemetry supports multiple plausible explanations, "
                "so the root cause should remain uncertain pending human review."
            ),
            category=HypothesisCategory.UNCERTAIN_ROOT_CAUSE,
            supporting_evidence_ids=supporting_evidence_ids,
            confidence=0.62,
            uncertainty=(
                "The local demo provider found mixed signals and is not allowed "
                "to choose a single root cause without stronger evidence."
            ),
        )

    if "insufficient" in incident_id:
        return InvestigationHypothesis(
            hypothesis_id="local-hyp-insufficient-evidence",
            statement=(
                "The available telemetry shows checkout symptoms, but it does not "
                "provide enough direct evidence to support a concrete root cause."
            ),
            category=HypothesisCategory.INSUFFICIENT_EVIDENCE,
            supporting_evidence_ids=supporting_evidence_ids,
            confidence=0.4,
            uncertainty=(
                "Additional direct dependency, configuration, deployment, or code "
                "evidence is needed before assigning a root cause."
            ),
        )

    return InvestigationHypothesis(
        hypothesis_id="local-hyp-database-timeout",
        statement=(
            "Checkout failures are most consistent with database timeout behavior "
            "observed in the retrieved log, trace, and metric evidence."
        ),
        category=HypothesisCategory.DATABASE_FAILURE,
        supporting_evidence_ids=supporting_evidence_ids,
        confidence=0.88,
    )


def _usable_evidence_ids(evidence: list[RetrievedEvidence]) -> list[str]:
    return [
        item.evidence.evidence_id
        for item in evidence
        if item.strength is not EvidenceStrength.MISSING
    ][:4]
