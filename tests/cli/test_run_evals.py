import pytest

from telemetry_agents.evaluation_cli import run_evals
from telemetry_agents.domain import EvidenceSource
from telemetry_agents.evaluation import (
    CitationCorrectnessScore,
    EvaluationScorecard,
    ExpectedEvidenceSourceDetail,
    ExpectedEvidenceSourcesScore,
    ExpectedHumanReviewScore,
    ExpectedHypothesisCategoryScore,
    UnsupportedClaimScore,
)


def test_help_exits_without_loading_config(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail_if_called() -> None:
        pytest.fail("get_settings should not be called for --help")

    monkeypatch.setattr(run_evals, "get_settings", fail_if_called)

    with pytest.raises(SystemExit) as exc_info:
        run_evals.main(["--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "Run telemetry investigation evaluation cases." in output


def test_print_report_outputs_readable_summary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    scorecard = _scorecard(case_id="checkout-database-timeout")

    run_evals.print_report([scorecard])

    output = capsys.readouterr().out
    assert "Evaluation summary: 1/1 passed" in output
    assert "[PASS] checkout-database-timeout" in output
    assert "evidence sources: PASS" in output
    assert "category: PASS" in output
    assert "case_id=" not in output


def test_print_report_outputs_failure_details(
    capsys: pytest.CaptureFixture[str],
) -> None:
    scorecard = _scorecard(
        passed=False,
        expected_evidence_sources_score=ExpectedEvidenceSourcesScore(
            passed=False,
            missing_expected_sources=[
                ExpectedEvidenceSourceDetail(
                    source=EvidenceSource.LOG,
                    source_file="eval_data/case/logs/checkout-api.log",
                )
            ],
        ),
        expected_category_score=ExpectedHypothesisCategoryScore(
            passed=False,
            expected_category="database_failure",
        ),
        expected_human_review_score=ExpectedHumanReviewScore(
            passed=False,
            expected_human_review_required=True,
            actual_human_review_required=False,
        ),
        citation_correctness_score=CitationCorrectnessScore(
            passed=False,
            hypotheses_without_citations=["hyp-1"],
        ),
    )

    run_evals.print_report([scorecard])

    output = capsys.readouterr().out
    assert "Evaluation summary: 0/1 passed" in output
    assert "[FAIL] case-1" in output
    assert (
        "missing evidence sources: log:eval_data/case/logs/checkout-api.log" in output
    )
    assert "expected category: database_failure" in output
    assert "expected human review: True, actual: False" in output
    assert "hypotheses without citations: hyp-1" in output


def _scorecard(
    *,
    case_id: str = "case-1",
    passed: bool = True,
    expected_evidence_sources_score: ExpectedEvidenceSourcesScore | None = None,
    expected_category_score: ExpectedHypothesisCategoryScore | None = None,
    expected_human_review_score: ExpectedHumanReviewScore | None = None,
    citation_correctness_score: CitationCorrectnessScore | None = None,
    unsupported_claim_score: UnsupportedClaimScore | None = None,
) -> EvaluationScorecard:
    return EvaluationScorecard(
        case_id=case_id,
        passed=passed,
        expected_evidence_sources_score=expected_evidence_sources_score
        or ExpectedEvidenceSourcesScore(passed=True),
        expected_category_score=expected_category_score
        or ExpectedHypothesisCategoryScore(
            passed=True,
            expected_category="database_failure",
            matched_hypothesis_ids=["hyp-1"],
        ),
        expected_human_review_score=expected_human_review_score
        or ExpectedHumanReviewScore(
            passed=True,
            expected_human_review_required=False,
            actual_human_review_required=False,
        ),
        citation_correctness_score=citation_correctness_score
        or CitationCorrectnessScore(passed=True),
        unsupported_claim_score=unsupported_claim_score
        or UnsupportedClaimScore(passed=True),
    )
