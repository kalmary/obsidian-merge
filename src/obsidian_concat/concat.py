"""Write ordered files into a single concatenated output."""

from pathlib import Path


def concat(files: list[Path], output: Path, vault_dir: Path) -> None:
    """Concatenate *files* into *output*, each preceded by a source comment header."""
    with open(output, "w", encoding="utf-8") as out:
        for i, filepath in enumerate(files):
            try:
                relpath = filepath.relative_to(vault_dir)
            except ValueError:
                relpath = filepath
            if i > 0:
                out.write("\n")
            out.write(f"---\n")
            out.write(f"<!-- source: {relpath} -->\n")
            out.write(f"---\n\n")
            out.write(filepath.read_text(encoding="utf-8", errors="replace"))
            if not filepath.read_text(encoding="utf-8", errors="replace").endswith("\n"):
                out.write("\n")
