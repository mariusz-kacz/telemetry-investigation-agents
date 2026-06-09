import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class InvestigationRunStatus(StrEnum):
    PENDING = "PENDING"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class InvestigationRunUpdateFailed(Exception):
    pass


@dataclass(frozen=True)
class InvestigationRunRecord:
    """Small SQL row model for workflow execution metadata."""

    run_id: str
    incident_id: str
    status: InvestigationRunStatus


def initialize_run_registry(db_path: Path) -> None:
    """Create the minimal SQLite schema needed for Phase 11."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS investigation_runs(
                run_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)


def create_investigation_run(
    db_path: Path,
    *,
    run_id: str,
    incident_id: str,
    status: InvestigationRunStatus = InvestigationRunStatus.PENDING,
) -> InvestigationRunRecord:
    """Insert one investigation run into SQLite and return the stored record."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO investigation_runs (run_id, incident_id, status)
            VALUES (?, ?, ?)
            """,
            (run_id, incident_id, status.value),
        )

        conn.commit()

        return InvestigationRunRecord(
            run_id=run_id, incident_id=incident_id, status=status
        )


def update_investigation_run(
    db_path: Path,
    *,
    run_id: str,
    incident_id: str,
    status: InvestigationRunStatus,
) -> InvestigationRunRecord:
    """Update one investigation run status and return the stored record."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE investigation_runs SET status = ?
            where run_id = ? and incident_id = ?
            """,
            (status.value, run_id, incident_id),
        )
        if cursor.rowcount == 0:
            raise InvestigationRunUpdateFailed(
                f"Investigation run {run_id} for incident {incident_id} was not found"
            )

        conn.commit()

        return InvestigationRunRecord(
            run_id=run_id, incident_id=incident_id, status=status
        )


def get_resumable_investigation_run(
    db_path: Path, *, run_id: str
) -> InvestigationRunRecord | None:
    """Read one investigation run from SQLite by run id."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT run_id, incident_id, status FROM investigation_runs WHERE run_id = ? and status = ?",
            (run_id, InvestigationRunStatus.AWAITING_REVIEW.value),
        ).fetchone()

        if row is None:
            return None

        run_id, incident_id, status = row
        return InvestigationRunRecord(
            run_id=run_id,
            incident_id=incident_id,
            status=InvestigationRunStatus(status),
        )


def get_investigation_run(
    db_path: Path,
    *,
    run_id: str,
) -> InvestigationRunRecord | None:
    """Read one investigation run from SQLite by run id."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT run_id, incident_id, status FROM investigation_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        if row is None:
            return None

        run_id, incident_id, status = row
        return InvestigationRunRecord(
            run_id=run_id,
            incident_id=incident_id,
            status=InvestigationRunStatus(status),
        )
