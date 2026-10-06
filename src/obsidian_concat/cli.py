"""CLI entry point for obsidian-concat."""

import argparse
import sys
from pathlib import Path

from obsidian_concat.concat import concat
from obsidian_concat.crawl import crawl
from obsidian_concat.index import build_index


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="obsidian-concat",
        description="Crawl an Obsidian vault from a start file and concatenate all reachable notes.",
    )
    parser.add_argument(
        "start_file",
        help="Entry-point markdown file.",
    )
    parser.add_argument(
        "-o", "--output",
        default="combined.md",
        help="Output file path (default: combined.md).",
    )
    parser.add_argument(
        "-d", "--vault-dir",
        default=None,
        help="Vault root directory to search for notes (default: directory of start_file).",
    )
    args = parser.parse_args(argv)

    start = Path(args.start_file)
    if not start.is_file():
        print(f"Error: start file not found: {start}", file=sys.stderr)
        sys.exit(1)

    vault_dir = Path(args.vault_dir).resolve() if args.vault_dir else start.resolve().parent
    output = Path(args.output)

    index = build_index(vault_dir)
    order = crawl(start, index)
    concat(order, output, vault_dir)

    print(f"✅ Concatenated {len(order)} file(s) → {output}")
    for f in order:
        try:
            print(f"  {f.relative_to(vault_dir)}")
        except ValueError:
            print(f"  {f}")
