from pathlib import Path

from telemetry_agents.app.config import Settings
from telemetry_agents.shared.paths import PROJECT_ROOT


def test_settings_loads_env_file_from_project_root() -> None:
    env_file = Settings.model_config["env_file"]

    assert Path(env_file) == PROJECT_ROOT / ".env"
