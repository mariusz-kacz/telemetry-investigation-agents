from dataclasses import dataclass

from starlette.testclient import TestClient

from telemetry_agents.api.app import create_app
from telemetry_agents.api.dependencies import get_demo_investigation_service
from telemetry_agents.app.demo_investigation_service import DemoInvestigationResult
from telemetry_agents.domain import (
    HypothesisCategory,
    HypothesisReviewStatus,
    InvestigationHypothesis,
    ReviewedHypothesis,
)


@dataclass
class FakeDemoInvestigationService:
    start_result: DemoInvestigationResult
    review_result: DemoInvestigationResult | None = None
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
    assert body["hypotheses"][0]["status"] == "accepted"


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


def _result(
    *,
    run_id: str = "run-001",
    human_review_required: bool,
    review_reasons: list[str] | None = None,
) -> DemoInvestigationResult:
    return DemoInvestigationResult(
        run_id=run_id,
        incident_id="inc-checkout-001",
        hypotheses=[
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
        human_review_required=human_review_required,
        review_reasons=review_reasons or [],
    )
