from importlib.resources import files


def load_prompt(filename: str) -> str:
    return (
        files("telemetry_agents.infrastructure.prompts")
        .joinpath(filename)
        .read_text(encoding="utf-8")
    )
