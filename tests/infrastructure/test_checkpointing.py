from pathlib import Path

from telemetry_agents.infrastructure.checkpointing import (
    create_checkpoint_serializer,
    create_sqlite_checkpointer,
)


def test_create_checkpoint_serializer_uses_explicit_msgpack_allowlist() -> None:
    serializer = create_checkpoint_serializer()

    assert serializer._allowed_msgpack_modules is not True
    assert (
        "telemetry_agents.domain.models",
        "Incident",
    ) in serializer._allowed_msgpack_modules
    assert (
        "telemetry_agents.investigation.evidence_retrieval",
        "RetrievedEvidence",
    ) in serializer._allowed_msgpack_modules


def test_create_sqlite_checkpointer_creates_parent_directory(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "checkpoints.sqlite"

    checkpointer = create_sqlite_checkpointer(db_path)

    assert db_path.parent.exists()
    assert checkpointer is not None
