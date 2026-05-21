from pathlib import Path

from telemetry_agents.infrastructure.checkpointing import create_sqlite_checkpointer


def test_create_sqlite_checkpointer_creates_parent_directory(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "checkpoints.sqlite"

    checkpointer = create_sqlite_checkpointer(db_path)

    assert db_path.parent.exists()
    assert checkpointer is not None
