from fastapi import APIRouter, Depends, HTTPException, Request, status

from telemetry_agents.api.dependencies import get_demo_investigation_service
from telemetry_agents.api.schemas import (
    InvestigationRequest,
    InvestigationResponse,
    HypothesisResponse,
)
from telemetry_agents.app.demo_investigation_service import RunDemoInvestigation

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_investigation(
    body: InvestigationRequest,
    run_investigation: RunDemoInvestigation = Depends(
        get_demo_investigation_service
    ),
) -> InvestigationResponse:
    try:
        result = run_investigation(body.case_id)
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
