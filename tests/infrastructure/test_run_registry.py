from pathlib import Path
import sqlite3

from telemetry_agents.infrastructure.run_registry import (
    InvestigationRunRecord,
    InvestigationRunStatus,
    create_investigation_run,
    get_investigation_run,
    get_resumable_investigation_run,
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
        case_id="case-001",
        incident_id="incident-checkout-timeout",
    )

    assert stored == InvestigationRunRecord(
        run_id="run-001",
        case_id="case-001",
        incident_id="incident-checkout-timeout",
        status=InvestigationRunStatus.PENDING,
    )
    assert get_investigation_run(db_path, run_id="run-001") == stored


def test_initialize_run_registry_adds_case_id_to_existing_registry(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "checkpoints.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE investigation_runs(
                run_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO investigation_runs (run_id, incident_id, status)
            VALUES (?, ?, ?)
            """,
            (
                "run-001",
                "incident-checkout-timeout",
                InvestigationRunStatus.PENDING.value,
            ),
        )

    initialize_run_registry(db_path)

    assert get_investigation_run(db_path, run_id="run-001") == InvestigationRunRecord(
        run_id="run-001",
        case_id="unknown",
        incident_id="incident-checkout-timeout",
        status=InvestigationRunStatus.PENDING,
    )


def test_get_resumable_investigation_run_returns_awaiting_review_run(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "checkpoints.sqlite"

    initialize_run_registry(db_path)
    stored = create_investigation_run(
        db_path,
        run_id="run-001",
        case_id="case-001",
        incident_id="incident-checkout-timeout",
        status=InvestigationRunStatus.AWAITING_REVIEW,
    )

    assert get_resumable_investigation_run(db_path, run_id="run-001") == stored


def test_get_resumable_investigation_run_ignores_completed_run(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "checkpoints.sqlite"

    initialize_run_registry(db_path)
    create_investigation_run(
        db_path,
        run_id="run-001",
        case_id="case-001",
        incident_id="incident-checkout-timeout",
        status=InvestigationRunStatus.COMPLETED,
    )

    assert get_resumable_investigation_run(db_path, run_id="run-001") is None


def test_get_investigation_run_returns_none_for_unknown_run(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "checkpoints.sqlite"

    initialize_run_registry(db_path)

    assert get_investigation_run(db_path, run_id="missing-run") is None
