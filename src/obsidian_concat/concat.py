"""Write ordered files into a single concatenated output."""

import re
from pathlib import Path

_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (``---`` … ``---``) from the start of *text*."""
    return _FRONTMATTER_RE.sub("", text, count=1)


def concat(files: list[Path], output: Path, vault_dir: Path) -> None:
    """Concatenate *files* into *output* with no per-file headers."""
    with open(output, "w", encoding="utf-8") as out:
        for i, filepath in enumerate(files):
            if i > 0:
                out.write("\n")
            content = filepath.read_text(encoding="utf-8", errors="replace")
            content = _strip_frontmatter(content)
            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
