from collections import defaultdict

from pydantic import BaseModel

from telemetry_agents.domain import (
    HypothesisCritiqueFinding,
    CritiqueFindingType,
    InvestigationHypothesis,
    HypothesisReviewResult,
    HypothesisReviewStatus,
    ReviewedHypothesis,
)

BLOCKED_FINDINGS = {
    CritiqueFindingType.CONTRADICTION,
    CritiqueFindingType.UNSUPPORTED_CAUSAL_LEAP,
}

DISPUTED_FINDINGS = {
    CritiqueFindingType.ALTERNATIVE_INTERPRETATION,
    CritiqueFindingType.OVERSTATED_CONFIDENCE,
}


class HypothesisReviewRequest(BaseModel):
    validated_hypotheses: list[InvestigationHypothesis]
    critique_findings: list[HypothesisCritiqueFinding]


def review_hypotheses(
    request: HypothesisReviewRequest,
) -> HypothesisReviewResult:
    reviewed_hypotheses: list[ReviewedHypothesis] = []

    findings_by_hypothesis_id: dict[str, list[HypothesisCritiqueFinding]] = defaultdict(
        list
    )
    for finding in request.critique_findings:
        findings_by_hypothesis_id[finding.hypothesis_id].append(finding)

    for hypothesis in request.validated_hypotheses:
        findings = findings_by_hypothesis_id[hypothesis.hypothesis_id]
        status: HypothesisReviewStatus = _review_status_for(findings=findings)

        reviewed_hypotheses.append(
            ReviewedHypothesis(
                hypothesis=hypothesis,
                status=status,
                critique_findings=findings,
            )
        )

    return HypothesisReviewResult(reviewed_hypotheses=reviewed_hypotheses)


def _review_status_for(findings: list[HypothesisCritiqueFinding]):
    finding_types = {item.finding_type for item in findings}
    if finding_types & BLOCKED_FINDINGS:
        return HypothesisReviewStatus.BLOCKED
    if finding_types & DISPUTED_FINDINGS:
        return HypothesisReviewStatus.DISPUTED

    return HypothesisReviewStatus.ACCEPTED
