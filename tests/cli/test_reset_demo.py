from pathlib import Path
from types import SimpleNamespace

import pytest

from telemetry_agents.demo_cli import reset_demo


def test_reset_demo_state_removes_configured_sqlite_files_and_sidecars(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(reset_demo, "PROJECT_ROOT", project_root)
    checkpoint_db_path = project_root / ".local" / "checkpoints.sqlite"
    run_registry_db_path = project_root / ".local" / "runs.sqlite"
    checkpoint_db_path.parent.mkdir()

    expected_removed_paths = [
        checkpoint_db_path,
        Path(f"{checkpoint_db_path}-wal"),
        Path(f"{checkpoint_db_path}-shm"),
        run_registry_db_path,
    ]
    for path in expected_removed_paths:
        path.write_text("sqlite state", encoding="utf-8")

    removed_paths = reset_demo.reset_demo_state(
        checkpoint_db_path=checkpoint_db_path,
        run_registry_db_path=run_registry_db_path,
    )

    assert removed_paths == sorted(expected_removed_paths)
    assert all(not path.exists() for path in expected_removed_paths)


def test_reset_demo_state_dry_run_keeps_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(reset_demo, "PROJECT_ROOT", project_root)
    checkpoint_db_path = project_root / "checkpoints.sqlite"
    run_registry_db_path = project_root / "runs.sqlite"
    checkpoint_db_path.write_text("checkpoint", encoding="utf-8")
    run_registry_db_path.write_text("run registry", encoding="utf-8")

    removed_paths = reset_demo.reset_demo_state(
        checkpoint_db_path=checkpoint_db_path,
        run_registry_db_path=run_registry_db_path,
        dry_run=True,
    )

    assert removed_paths == [checkpoint_db_path, run_registry_db_path]
    assert checkpoint_db_path.exists()
    assert run_registry_db_path.exists()


def test_reset_demo_state_refuses_paths_outside_project_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(reset_demo, "PROJECT_ROOT", project_root)

    with pytest.raises(reset_demo.UnsafeResetPathError, match="project root"):
        reset_demo.reset_demo_state(
            checkpoint_db_path=tmp_path / "checkpoints.sqlite",
            run_registry_db_path=project_root / "runs.sqlite",
        )


def test_reset_demo_state_refuses_non_sqlite_suffix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(reset_demo, "PROJECT_ROOT", project_root)

    with pytest.raises(reset_demo.UnsafeResetPathError, match="SQLite"):
        reset_demo.reset_demo_state(
            checkpoint_db_path=project_root / "notes.txt",
            run_registry_db_path=project_root / "runs.sqlite",
        )


def test_main_prints_removed_relative_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(reset_demo, "PROJECT_ROOT", project_root)
    checkpoint_db_path = project_root / "checkpoints.sqlite"
    run_registry_db_path = project_root / "runs.sqlite"
    checkpoint_db_path.write_text("checkpoint", encoding="utf-8")
    run_registry_db_path.write_text("run registry", encoding="utf-8")
    monkeypatch.setattr(
        reset_demo,
        "get_settings",
        lambda: SimpleNamespace(
            checkpoint_db_path=checkpoint_db_path,
            run_registry_db_path=run_registry_db_path,
        ),
    )

    exit_code = reset_demo.main([])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Removed: checkpoints.sqlite" in output
    assert "Removed: runs.sqlite" in output
