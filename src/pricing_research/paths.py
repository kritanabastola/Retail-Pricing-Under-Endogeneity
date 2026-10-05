"""Project paths that stay readable on another machine."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def portable_path(path: Path) -> str:
    """Return a project-relative POSIX path when the file lives in the project."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()
