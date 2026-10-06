"""Write ordered files into a single concatenated output."""

import re
from pathlib import Path, PurePosixPath

from obsidian_concat.crawl import resolve_link

_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
_EMBED_OR_WIKILINK_RE = re.compile(r"(!?)\[\[([^\]]+?)\]\]")


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (``---`` … ``---``) from the start of *text*."""
    return _FRONTMATTER_RE.sub("", text, count=1)


def _make_anchor(filepath: Path, vault_dir: Path) -> str:
    """Generate a URL-safe anchor ID from the file's vault-relative path."""
    try:
        rel = filepath.relative_to(vault_dir)
    except ValueError:
        rel = Path(filepath.name)
    stem = str(PurePosixPath(rel.with_suffix("")))
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def _replace_wikilinks(
    text: str,
    anchor_map: dict[Path, str],
    relpath_index: dict[str, Path],
    basename_index: dict[str, list[Path]],
) -> str:
    """Replace ``[[wikilinks]]`` with markdown links to in-document anchors."""

    def _replacer(match: re.Match) -> str:
        embed_prefix = match.group(1)
        if embed_prefix:
            return match.group(0)  # Leave ![[embeds]] unchanged

        raw = match.group(2)

        # Parse alias  (e.g. [[Target|display]])
        parts = raw.split("|", 1)
        target_part = parts[0]
        alias = parts[1].strip() if len(parts) > 1 else None

        # Parse heading anchor  (e.g. [[Target#section]])
        heading_parts = target_part.split("#", 1)
        link_target = heading_parts[0].strip()
        heading = heading_parts[1].strip() if len(heading_parts) > 1 else None

        if not link_target:
            # Self-referencing heading link: [[#heading]]
            if heading:
                display = alias or heading
                slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
                return f"[{display}](#{slug})"
            return match.group(0)

        # Resolve to a file present in the merged document
        resolved = resolve_link(link_target, relpath_index, basename_index, set())
        if resolved and resolved in anchor_map:
            anchor = anchor_map[resolved]
            display = alias or link_target
            return f"[{display}](#{anchor})"

        # Unresolvable — degrade to plain text
        return alias or link_target

    return _EMBED_OR_WIKILINK_RE.sub(_replacer, text)


def concat(
    files: list[Path],
    output: Path,
    vault_dir: Path,
    index: tuple[dict[str, Path], dict[str, list[Path]]] | None = None,
) -> None:
    """Concatenate *files* into *output*, converting wikilinks to internal anchors."""
    # Build path → anchor mapping
    anchor_map: dict[Path, str] = {fp: _make_anchor(fp, vault_dir) for fp in files}

    relpath_index: dict[str, Path] = {}
    basename_index: dict[str, list[Path]] = {}
    if index:
        relpath_index, basename_index = index

    with open(output, "w", encoding="utf-8") as out:
        for i, filepath in enumerate(files):
            if i > 0:
                out.write("\n")

            # Anchor + heading for each note
            out.write(f'<a id="{anchor_map[filepath]}"></a>\n\n')
            out.write(f"# {filepath.stem}\n\n")

            content = filepath.read_text(encoding="utf-8", errors="replace")
            content = _strip_frontmatter(content)

            if index:
                content = _replace_wikilinks(
                    content, anchor_map, relpath_index, basename_index,
                )

            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
