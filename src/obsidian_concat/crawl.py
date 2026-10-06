"""Extract Obsidian [[wikilinks]] and crawl the link graph via BFS."""

import re
from collections import deque
from pathlib import Path, PurePosixPath

WIKILINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")


def extract_links(filepath: Path) -> list[str]:
    """Return the raw targets from all ``[[wikilinks]]`` in *filepath*.

    Handles ``[[Page]]``, ``[[Page|alias]]``, ``[[Page#heading]]``,
    and ``[[folder/Page]]``.  Returns the cleaned target string as-is
    (may contain path separators).
    """
    text = filepath.read_text(encoding="utf-8", errors="replace")
    targets: list[str] = []
    for match in WIKILINK_RE.finditer(text):
        raw = match.group(1)
        raw = raw.split("|", 1)[0]          # strip alias
        raw = raw.split("#", 1)[0].strip()  # strip heading anchor
        if raw:
            targets.append(raw)
    return targets


def resolve_link(
    link: str,
    relpath_index: dict[str, Path],
    basename_index: dict[str, list[Path]],
    visited: set[Path],
) -> Path | None:
    """Resolve a wikilink target to a file path.

    Strategy (mirrors Obsidian):
    1. Try exact relative path match (lowercased, no .md).
    2. Fall back to basename match — pick the first unvisited entry,
       then fall back to the first entry overall.
    """
    key = str(PurePosixPath(link)).lower()

    # 1. Exact relative path
    if key in relpath_index:
        return relpath_index[key]

    # 2. Basename fallback
    base_key = PurePosixPath(link).name.lower()
    candidates = basename_index.get(base_key)
    if not candidates:
        return None

    # Prefer an unvisited candidate
    for c in candidates:
        if c not in visited:
            return c
    return candidates[0]


def crawl(
    start: Path,
    index: tuple[dict[str, Path], dict[str, list[Path]]],
) -> list[Path]:
    """BFS from *start*, following wikilinks via *index*. Returns ordered file list."""
    relpath_index, basename_index = index
    visited: set[Path] = set()
    order: list[Path] = []
    queue: deque[Path] = deque()

    start_abs = start.resolve()
    queue.append(start_abs)
    visited.add(start_abs)

    while queue:
        current = queue.popleft()
        order.append(current)
        for link_target in extract_links(current):
            resolved = resolve_link(link_target, relpath_index, basename_index, visited)
            if resolved and resolved not in visited:
                visited.add(resolved)
                queue.append(resolved)

    return order
