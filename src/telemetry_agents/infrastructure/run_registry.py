import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InvestigationRunRecord:
    """Small SQL row model for workflow execution metadata."""

    run_id: str
    incident_id: str


def initialize_run_registry(db_path: Path) -> None:
    """Create the minimal SQLite schema needed for Phase 11."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS investigation_runs(
                run_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL
            )
        """)


def create_investigation_run(
    db_path: Path,
    *,
    run_id: str,
    incident_id: str,
) -> InvestigationRunRecord:
    """Insert one investigation run into SQLite and return the stored record."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO investigation_runs (run_id, incident_id)
            VALUES (?, ?)
            """,
            (run_id, incident_id),
        )

        conn.commit()

        return InvestigationRunRecord(
            run_id=run_id,
            incident_id=incident_id,
        )


def get_investigation_run(
    db_path: Path,
    *,
    run_id: str,
) -> InvestigationRunRecord | None:
    """Read one investigation run from SQLite by run id."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT run_id, incident_id FROM investigation_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        if row is None:
            return None

        run_id, incident_id = row
        return InvestigationRunRecord(
            run_id=run_id,
            incident_id=incident_id,
        )
