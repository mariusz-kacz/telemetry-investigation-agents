import pytest

from telemetry_agents.infrastructure.prompt_loader import load_prompt


@pytest.mark.parametrize(
    ("filename", "expected_start"),
    [
        (
            "hypothesis_generator.md",
            "Generate zero or more candidate investigation hypotheses",
        ),
        (
            "hypothesis_critic.md",
            "Review validated investigation hypotheses for semantic problems only.",
        ),
        (
            "unsupported_claim_reviewer.md",
            "Review validated investigation hypotheses for unsupported causal claims only.",
        ),
    ],
)
def test_load_prompt_reads_packaged_markdown_prompt(
    filename: str,
    expected_start: str,
) -> None:
    prompt = load_prompt(filename)

    assert prompt.startswith(expected_start)
    assert prompt.strip()


def test_load_prompt_raises_file_not_found_for_unknown_prompt() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("missing_prompt.md")


@pytest.mark.parametrize(
    "filename",
    [
        "hypothesis_generator.md",
        "hypothesis_critic.md",
        "unsupported_claim_reviewer.md",
    ],
)
def test_prompt_contracts_do_not_reference_eval_fixtures(filename: str) -> None:
    prompt = load_prompt(filename).lower()

    forbidden_fixture_terms = [
        "checkout-database-timeout",
        "downstream-dependency-latency",
        "conflicting-evidence",
        "insufficient-evidence",
        "checkout-api",
        "orders-db",
        "eval_data/",
        "sample_data/",
    ]

    assert not any(term in prompt for term in forbidden_fixture_terms)


def test_generator_prompt_avoids_case_shaped_output_commands() -> None:
    prompt = load_prompt("hypothesis_generator.md")

    assert "exactly one UNCERTAIN_ROOT_CAUSE hypothesis" not in prompt
    assert "exactly one INSUFFICIENT_EVIDENCE hypothesis" not in prompt
    assert "prefer a single uncertainty-focused hypothesis" in prompt
    assert "prefer a single evidence-gap hypothesis" in prompt
