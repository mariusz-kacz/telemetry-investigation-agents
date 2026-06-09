import json
from pathlib import Path

from telemetry_agents.app.config import Settings
from telemetry_agents.domain import Incident


def get_demo_cases(
    settings: Settings,
) -> list[str]:
    if settings.eval_data_root:
        cases_dir = settings.data_root / "cases"
        case_names: list[str] = []
        for eval_case_file in cases_dir.glob("*.json"):
            case_names.append(eval_case_file.stem)
        return case_names

    raise ValueError("Settings miss data_root")


def load_incident_file(incident_file_path: Path) -> Incident:
    with incident_file_path.open(encoding="utf-8") as file:
        data = json.load(file)
    return Incident.model_validate(data)
