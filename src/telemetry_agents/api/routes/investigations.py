from fastapi import APIRouter, Depends, HTTPException, status

from telemetry_agents.api.dependencies import get_demo_investigation_service
from telemetry_agents.api.schemas import (
    InvestigationRequest,
    InvestigationResponse,
    HypothesisResponse,
    HumanReviewRequest,
)
from telemetry_agents.app.demo_investigation_service import (
    DemoInvestigationService,
    RunNotFound,
    DemoInvestigationResult,
)

router = APIRouter(prefix="/investigations", tags=["investigations"])


def to_investigation_response(result: DemoInvestigationResult) -> InvestigationResponse:
    return InvestigationResponse(
        run_id=result.run_id,
        incident_id=result.incident_id,
        hypotheses=[
            HypothesisResponse(
                id=reviewed.hypothesis.hypothesis_id,
                summary=reviewed.hypothesis.statement,
                confidence=reviewed.hypothesis.confidence,
                status=reviewed.status,
                evidence_ids=list(reviewed.hypothesis.supporting_evidence_ids),
            )
            for reviewed in result.hypotheses
        ],
        human_review_required=result.human_review_required,
        review_reasons=list(result.review_reasons),
    )


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_investigation(
    body: InvestigationRequest,
    investigation_service: DemoInvestigationService = Depends(
        get_demo_investigation_service
    ),
) -> InvestigationResponse:
    try:
        result = investigation_service.start(body.case_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return to_investigation_response(result=result)


@router.post(
    "/{run_id}/review",
    response_model=InvestigationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def review_investigation(
    run_id: str,
    body: HumanReviewRequest,
    investigation_service: DemoInvestigationService = Depends(
        get_demo_investigation_service
    ),
) -> InvestigationResponse:
    try:
        result = investigation_service.review(run_id=run_id, approved=body.approved)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except RunNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return to_investigation_response(result=result)
