import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
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
    case_id: str
    incident_id: str
    status: InvestigationRunStatus
    demo_provider: str


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def initialize_run_registry(db_path: Path) -> None:
    """Create the minimal SQLite schema needed for Phase 11."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS investigation_runs(
                run_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                status TEXT NOT NULL,
                demo_provider TEXT NOT NULL DEFAULT 'unknown',
                created_at TEXT NOT NULL
            )
        """)
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(investigation_runs)").fetchall()
        }
        if "case_id" not in columns:
            conn.execute(
                """
                ALTER TABLE investigation_runs
                ADD COLUMN case_id TEXT NOT NULL DEFAULT 'unknown'
                """
            )
        if "demo_provider" not in columns:
            conn.execute(
                """
                ALTER TABLE investigation_runs
                ADD COLUMN demo_provider TEXT NOT NULL DEFAULT 'unknown'
                """
            )
        if "created_at" not in columns:
            conn.execute(
                """
                ALTER TABLE investigation_runs
                ADD COLUMN created_at TEXT
                """
            )
        conn.execute(
            """
            UPDATE investigation_runs
            SET created_at = ?
            WHERE created_at IS NULL
            """,
            (_utc_now_iso(),),
        )


def create_investigation_run(
    db_path: Path,
    *,
    run_id: str,
    case_id: str,
    incident_id: str,
    demo_provider: str = "unknown",
    status: InvestigationRunStatus = InvestigationRunStatus.PENDING,
) -> InvestigationRunRecord:
    """Insert one investigation run into SQLite and return the stored record."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO investigation_runs (run_id, case_id, incident_id, status, demo_provider, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, case_id, incident_id, status.value, demo_provider, _utc_now_iso()),
        )

        conn.commit()

        return InvestigationRunRecord(
            run_id=run_id,
            case_id=case_id,
            incident_id=incident_id,
            status=status,
            demo_provider=demo_provider,
        )


def update_investigation_run(
    db_path: Path,
    *,
    run_id: str,
    status: InvestigationRunStatus,
) -> InvestigationRunRecord:
    """Update one investigation run status and return the stored record."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE investigation_runs SET status = ?
            where run_id = ?
            """,
            (status.value, run_id),
        )
        if cursor.rowcount == 0:
            raise InvestigationRunUpdateFailed(
                f"Investigation run {run_id} was not found"
            )

        row = conn.execute(
            """
            SELECT run_id, case_id, incident_id, status, demo_provider
            FROM investigation_runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        conn.commit()

    if row is None:
        raise InvestigationRunUpdateFailed(
            f"Investigation run {run_id} was not found after update"
        )

    stored_run_id, case_id, incident_id, stored_status, demo_provider = row
    return InvestigationRunRecord(
        run_id=stored_run_id,
        case_id=case_id,
        incident_id=incident_id,
        status=InvestigationRunStatus(stored_status),
        demo_provider=demo_provider,
    )


def get_resumable_investigation_run(
    db_path: Path, *, run_id: str
) -> InvestigationRunRecord | None:
    """Read one investigation run from SQLite by run id."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT run_id, case_id, incident_id, status, demo_provider FROM investigation_runs WHERE run_id = ? and status = ?",
            (run_id, InvestigationRunStatus.AWAITING_REVIEW.value),
        ).fetchone()

        if row is None:
            return None

        run_id, case_id, incident_id, status, demo_provider = row
        return InvestigationRunRecord(
            run_id=run_id,
            case_id=case_id,
            incident_id=incident_id,
            status=InvestigationRunStatus(status),
            demo_provider=demo_provider,
        )


def get_investigation_run(
    db_path: Path,
    *,
    run_id: str,
) -> InvestigationRunRecord | None:
    """Read one investigation run from SQLite by run id."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT run_id, case_id, incident_id, status, demo_provider FROM investigation_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        if row is None:
            return None

        run_id, case_id, incident_id, status, demo_provider = row
        return InvestigationRunRecord(
            run_id=run_id,
            case_id=case_id,
            incident_id=incident_id,
            status=InvestigationRunStatus(status),
            demo_provider=demo_provider,
        )


def list_investigation_runs(db_path: Path) -> list[InvestigationRunRecord]:
    """Read investigation runs from SQLite."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT run_id, case_id, incident_id, status, demo_provider
            FROM investigation_runs
            ORDER BY created_at DESC, run_id DESC
            """,
        ).fetchall()

    return [
        InvestigationRunRecord(
            run_id=run_id,
            case_id=case_id,
            incident_id=incident_id,
            status=InvestigationRunStatus(status),
            demo_provider=demo_provider,
        )
        for run_id, case_id, incident_id, status, demo_provider in rows
    ]
