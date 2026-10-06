"""Build a lookup index of all markdown files in a vault directory."""

from pathlib import Path, PurePosixPath


def build_index(vault_dir: Path) -> tuple[dict[str, Path], dict[str, list[Path]]]:
    """Build two lookup structures for resolving Obsidian wikilinks.

    Returns:
        (relpath_index, basename_index) where:
        - relpath_index: maps lowercased relative path (no .md) → resolved path.
          e.g. ``"lista notatek/5.10 - czym jest nlp/wprowadzenie"`` → ``Path(...)``
        - basename_index: maps lowercased basename (no .md) → list of resolved paths
          sorted shortest-first (Obsidian's "shortest path" heuristic).
    """
    relpath_index: dict[str, Path] = {}
    basename_groups: dict[str, list[Path]] = {}

    for md_file in vault_dir.rglob("*.md"):
        resolved = md_file.resolve()

        # Relative path key (forward slashes, no extension, lowered)
        try:
            rel = md_file.relative_to(vault_dir)
        except ValueError:
            continue
        rel_key = str(PurePosixPath(rel.with_suffix(""))).lower()
        relpath_index[rel_key] = resolved

        # Basename key
        base_key = md_file.stem.lower()
        basename_groups.setdefault(base_key, []).append(resolved)

    # Sort each basename group by path length (shortest first)
    for paths in basename_groups.values():
        paths.sort(key=lambda p: len(str(p)))

    return relpath_index, basename_groups
