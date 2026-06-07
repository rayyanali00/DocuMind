from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from app.pipelines.validators import is_supported


def scan_directory(root: Path) -> Iterator[Path]:
    """Recursively yield supported files from a directory.

    Folders themselves are never yielded (FR-005). Symlinks are not followed
    to avoid infinite loops on cyclic external drives.
    """
    if not root.exists() or not root.is_dir():
        return
    for entry in root.rglob("*"):
        try:
            if entry.is_symlink():
                continue
            if entry.is_file() and is_supported(entry.name):
                yield entry
        except OSError:
            # Permission denied, transient I/O, etc. — skip silently.
            continue


def build_hierarchy(path: Path, root: Path | None = None) -> str:
    """Return slash-joined parent hierarchy relative to root (or absolute if no root)."""
    if root is not None:
        try:
            rel = path.relative_to(root)
            return "/".join(rel.parent.parts)
        except ValueError:
            pass
    return "/".join(path.parent.parts)
