import argparse
from collections.abc import Sequence
import json
from pathlib import Path

from telemetry_agents.app.config import get_settings
from telemetry_agents.evaluation import EvaluationScorecard, EvalCase
from telemetry_agents.evaluation.evaluator import run_batch_evaluation
from telemetry_agents.evaluation_cli.azure_composition import (
    build_azure_evaluation_composition,
)
from telemetry_agents.shared.logging_config import configure_observability_logging
from telemetry_agents.shared.tracing import configure_local_tracing


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run telemetry investigation evaluation cases."
    )
    parser.add_argument(
        "--provider",
        choices=["azure"],
        required=True,
        help="Evaluation provider to use. Azure runs require configured Azure OpenAI access.",
    )
    return parser.parse_args(argv)


def print_report(scorecards: list[EvaluationScorecard]) -> None:
    passed_count = sum(scorecard.passed for scorecard in scorecards)
    total_count = len(scorecards)
    print(f"Evaluation summary: {passed_count}/{total_count} passed")

    for scorecard in scorecards:
        status = _status(scorecard.passed)
        print(f"\n[{status}] {scorecard.case_id}")
        print(
            "  evidence sources: "
            f"{_status(scorecard.expected_evidence_sources_score.passed)}"
        )
        print(f"  category: {_status(scorecard.expected_category_score.passed)}")
        print(
            f"  human review: {_status(scorecard.expected_human_review_score.passed)}"
        )
        print(
            "  citation correctness: "
            f"{_status(scorecard.citation_correctness_score.passed)}"
        )
        print(
            f"  unsupported claims: {_status(scorecard.unsupported_claim_score.passed)}"
        )

        _print_failure_details(scorecard)


def _status(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def _print_failure_details(scorecard: EvaluationScorecard) -> None:
    evidence_score = scorecard.expected_evidence_sources_score
    if evidence_score.missing_expected_sources:
        missing_sources = [
            f"{source.source.value}:{source.source_file}"
            for source in evidence_score.missing_expected_sources
        ]
        print(f"  missing evidence sources: {', '.join(missing_sources)}")

    category_score = scorecard.expected_category_score
    if not category_score.passed:
        print(f"  expected category: {category_score.expected_category}")

    human_review_score = scorecard.expected_human_review_score
    if not human_review_score.passed:
        print(
            "  expected human review: "
            f"{human_review_score.expected_human_review_required}, "
            f"actual: {human_review_score.actual_human_review_required}"
        )

    citation_score = scorecard.citation_correctness_score
    if citation_score.hypotheses_without_citations:
        hypothesis_ids = ", ".join(citation_score.hypotheses_without_citations)
        print(f"  hypotheses without citations: {hypothesis_ids}")
    if citation_score.unknown_evidence_references:
        print(
            "  unknown evidence references: "
            f"{citation_score.unknown_evidence_references}"
        )
    if citation_score.missing_evidence_references:
        print(
            "  missing evidence references: "
            f"{citation_score.missing_evidence_references}"
        )

    unsupported_claim_score = scorecard.unsupported_claim_score
    for finding in unsupported_claim_score.findings:
        print(f"  unsupported claim in {finding.hypothesis_id}: {finding.reason}")


def _load_eval_cases(data_root: Path) -> list[EvalCase]:
    eval_cases_dir = data_root / "cases"
    eval_cases: list[EvalCase] = []
    for eval_case_file in eval_cases_dir.glob("*.json"):
        with eval_case_file.open(encoding="utf-8") as file:
            data = json.load(file)
        eval_cases.append(EvalCase.model_validate(data))
    return eval_cases


def main(argv: Sequence[str] | None = None) -> int:
    _parse_args(argv)

    configure_observability_logging()
    settings = get_settings()

    configure_local_tracing(tracing_enabled=settings.tracing_enabled)
    cases = _load_eval_cases(settings.eval_data_root)
    evaluation_composition = build_azure_evaluation_composition(settings)
    scorecards = run_batch_evaluation(
        cases=cases,
        run_case=evaluation_composition.run_case,
        reviewer=evaluation_composition.reviewer,
    )
    print_report(scorecards)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
