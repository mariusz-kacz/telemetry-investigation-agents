from pathlib import Path

from telemetry_agents.infrastructure.run_registry import (
    InvestigationRunRecord,
    create_investigation_run,
    get_investigation_run,
    initialize_run_registry,
)


def test_initialize_run_registry_creates_run_registry(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "checkpoints.sqlite"

    initialize_run_registry(db_path)
    stored = create_investigation_run(
        db_path,
        run_id="run-001",
        incident_id="incident-checkout-timeout",
    )

    assert stored == InvestigationRunRecord(
        run_id="run-001",
        incident_id="incident-checkout-timeout",
    )
    assert get_investigation_run(db_path, run_id="run-001") == stored


def test_get_investigation_run_returns_none_for_unknown_run(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "checkpoints.sqlite"

    initialize_run_registry(db_path)

    assert get_investigation_run(db_path, run_id="missing-run") is None
