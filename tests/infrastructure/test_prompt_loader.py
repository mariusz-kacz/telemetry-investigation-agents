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
