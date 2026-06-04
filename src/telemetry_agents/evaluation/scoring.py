from collections import defaultdict
from pathlib import Path

from telemetry_agents.domain import HypothesisReviewStatus
from telemetry_agents.evaluation.unsupported_claim_review import (
    GuardedUnsupportedClaimReviewer,
    UnsupportedClaimReviewRequest,
)
from telemetry_agents.evaluation.models import (
    CitationCorrectnessScore,
    EvalCase,
    EvaluationRunOutput,
    ExpectedEvidenceSourceDetail,
    ExpectedEvidenceSourcesScore,
    ExpectedHumanReviewScore,
    ExpectedHypothesisCategoryScore,
    UnsupportedClaimScore,
)
from telemetry_agents.investigation.evidence_scoring import EvidenceStrength
from telemetry_agents.shared.paths import PROJECT_ROOT


def score_unsupported_claims(
    *,
    output: EvaluationRunOutput,
    reviewer: GuardedUnsupportedClaimReviewer,
) -> UnsupportedClaimScore:
    """Score whether accepted hypotheses contain unsupported causal claims."""
    reviewed_accepted_hypotheses = [
        h.hypothesis
        for h in output.review_result.reviewed_hypotheses
        if h.status == HypothesisReviewStatus.ACCEPTED
    ]

    if not reviewed_accepted_hypotheses:
        return UnsupportedClaimScore(passed=True)

    request = UnsupportedClaimReviewRequest(
        reviewed_accepted_hypotheses=reviewed_accepted_hypotheses,
        evidence=output.retrieved_evidence,
    )
    review_result = reviewer.review(request=request)

    return UnsupportedClaimScore(
        passed=not bool(review_result.findings), findings=review_result.findings
    )


def score_citation_correctness(
    *,
    output: EvaluationRunOutput,
) -> CitationCorrectnessScore:
    """Score whether validated hypotheses cite usable retrieved evidence."""
    if output.validation_result is None:
        return CitationCorrectnessScore(passed=True)

    hypotheses_without_citations: list[str] = []
    unknown_evidence_references: defaultdict[str, list[str]] = defaultdict(list)
    missing_evidence_references: defaultdict[str, list[str]] = defaultdict(list)
    evidence_by_id = {
        evidence.evidence.evidence_id: evidence
        for evidence in output.retrieved_evidence
    }

    for hypothesis in output.validation_result.validated_hypotheses:
        if not hypothesis.supporting_evidence_ids:
            hypotheses_without_citations.append(hypothesis.hypothesis_id)
            continue

        for supporting_evidence_id in hypothesis.supporting_evidence_ids:
            retrieved_evidence = evidence_by_id.get(supporting_evidence_id)
            if retrieved_evidence is None:
                unknown_evidence_references[hypothesis.hypothesis_id].append(
                    supporting_evidence_id
                )
            elif retrieved_evidence.strength == EvidenceStrength.MISSING:
                missing_evidence_references[hypothesis.hypothesis_id].append(
                    retrieved_evidence.evidence.evidence_id
                )

    overall_score = not (
        hypotheses_without_citations
        or unknown_evidence_references
        or missing_evidence_references
    )
    return CitationCorrectnessScore(
        passed=overall_score,
        hypotheses_without_citations=hypotheses_without_citations,
        unknown_evidence_references=unknown_evidence_references,
        missing_evidence_references=missing_evidence_references,
    )


def score_expected_evidence_sources(
    *,
    case: EvalCase,
    output: EvaluationRunOutput,
) -> ExpectedEvidenceSourcesScore:
    """Score whether retrieved evidence cites the expected source files."""
    expected_sources_by_key = {
        (_canonical_source_file(item.source_file), item.source): item
        for item in case.expected_evidence_sources
    }
    expected_sources = {
        (_canonical_source_file(item.source_file), item.source)
        for item in case.expected_evidence_sources
    }
    output_sources = {
        (_canonical_source_file(item.citation.source_file), item.evidence.source)
        for item in output.retrieved_evidence
    }

    matched_expected_sources = sorted(output_sources & expected_sources)
    missing_expected_sources = sorted(expected_sources - output_sources)

    return ExpectedEvidenceSourcesScore(
        passed=not bool(missing_expected_sources),
        matched_expected_sources=[
            ExpectedEvidenceSourceDetail(
                source_file=expected_sources_by_key[(source_file, source)].source_file,
                source=source,
            )
            for (source_file, source) in matched_expected_sources
        ],
        missing_expected_sources=[
            ExpectedEvidenceSourceDetail(
                source_file=expected_sources_by_key[(source_file, source)].source_file,
                source=source,
            )
            for (source_file, source) in missing_expected_sources
        ],
    )


def _canonical_source_file(source_file: str) -> str:
    source_path = Path(source_file)
    if not source_path.is_absolute():
        return source_path.as_posix()

    try:
        return source_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return source_path.as_posix()


def score_expected_category(
    *,
    case: EvalCase,
    output: EvaluationRunOutput,
) -> ExpectedHypothesisCategoryScore:
    expected_category = case.expected_category
    matched_hypothesis_ids = []
    accepted_reviewed_hypothesis = [h for h in output.review_result.reviewed_hypotheses if h.status == HypothesisReviewStatus.ACCEPTED]
    for accepted_hypothesis in accepted_reviewed_hypothesis:
        if expected_category == accepted_hypothesis.hypothesis.category:
            matched_hypothesis_ids.append(accepted_hypothesis.hypothesis.hypothesis_id)

    return ExpectedHypothesisCategoryScore(
        passed=bool(matched_hypothesis_ids),
        expected_category=expected_category,
        matched_hypothesis_ids=matched_hypothesis_ids,
    )


def score_expected_human_review(
    *,
    case: EvalCase,
    output: EvaluationRunOutput,
) -> ExpectedHumanReviewScore:
    """Score whether the workflow produced the expected human-review decision."""
    if output.human_review_assessment is None:
        return ExpectedHumanReviewScore(
            passed=False,
            expected_human_review_required=case.expected_human_review_required,
            actual_human_review_required=None,
        )

    actual_human_review_required = output.human_review_assessment.human_review_required

    return ExpectedHumanReviewScore(
        passed=case.expected_human_review_required == actual_human_review_required,
        expected_human_review_required=case.expected_human_review_required,
        actual_human_review_required=actual_human_review_required,
    )
