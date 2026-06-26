import argparse
from collections.abc import Sequence
from pathlib import Path

from telemetry_agents.app.config import get_settings
from telemetry_agents.shared.paths import PROJECT_ROOT

SQLITE_SIDE_SUFFIXES = ("", "-wal", "-shm", "-journal")
ALLOWED_DB_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


class UnsafeResetPathError(ValueError):
    pass


def _resolve_safe_demo_db_path(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(PROJECT_ROOT):
        raise UnsafeResetPathError(
            f"Demo reset only removes SQLite files inside the project root: {resolved}"
        )
    if resolved.suffix not in ALLOWED_DB_SUFFIXES:
        raise UnsafeResetPathError(
            f"Demo reset only removes SQLite database files, got: {resolved}"
        )
    return resolved


def _sqlite_related_paths(db_path: Path) -> list[Path]:
    return [Path(f"{db_path}{suffix}") for suffix in SQLITE_SIDE_SUFFIXES]


def reset_demo_state(
    *,
    checkpoint_db_path: Path,
    run_registry_db_path: Path,
    dry_run: bool = False,
) -> list[Path]:
    """Remove local SQLite state used by the portfolio demo."""
    candidate_paths = {
        related_path
        for db_path in {
            _resolve_safe_demo_db_path(checkpoint_db_path),
            _resolve_safe_demo_db_path(run_registry_db_path),
        }
        for related_path in _sqlite_related_paths(db_path)
    }

    removed_paths: list[Path] = []
    for path in sorted(candidate_paths):
        if not path.exists():
            continue
        if not path.is_file():
            raise UnsafeResetPathError(f"Demo reset refuses to remove non-file: {path}")
        removed_paths.append(path)
        if not dry_run:
            path.unlink()

    return removed_paths


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset local SQLite state for the telemetry investigation demo."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print files that would be removed without deleting them.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    settings = get_settings()
    removed_paths = reset_demo_state(
        checkpoint_db_path=settings.checkpoint_db_path,
        run_registry_db_path=settings.run_registry_db_path,
        dry_run=args.dry_run,
    )

    action = "Would remove" if args.dry_run else "Removed"
    if not removed_paths:
        print("No local demo SQLite state found.")
        return 0

    for path in removed_paths:
        print(f"{action}: {path.relative_to(PROJECT_ROOT)}")
    return 0
