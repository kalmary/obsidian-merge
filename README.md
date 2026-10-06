# obsidian-concat

Crawl an [Obsidian](https://obsidian.md) vault starting from a given entry-point file, follow `[[wikilinks]]` in BFS order, and concatenate all reachable notes into a single markdown file.

## Features

- **Link-graph crawl** — follows `[[wikilinks]]` via BFS, not just a flat directory listing — only reachable notes are included
- **Obsidian-aware resolution** — handles `[[Page]]`, `[[Page|alias]]`, `[[Page#heading]]`, `[[folder/Page]]`, and duplicate basenames (shortest-path-first heuristic, matching Obsidian's behaviour)
- **Cycle-safe** — tracks visited files so circular links never cause infinite loops
- **Zero dependencies** — stdlib only, Python ≥ 3.12

## Installation

### With `uv` (recommended)

```bash
# Install globally as an isolated tool
uv tool install /path/to/obsidian-concat

# Or install from the repo directory
uv tool install .
```

This makes `obsidian-concat` available everywhere without polluting your global Python.

### With `pip`

```bash
pip install /path/to/obsidian-concat
```

## Usage

```bash
obsidian-concat <start_file> [-o OUTPUT] [-d VAULT_DIR]
```

| Argument | Description | Default |
|---|---|---|
| `start_file` | Entry-point `.md` file (required) | — |
| `-o`, `--output` | Output file path | `combined.md` |
| `-d`, `--vault-dir` | Vault root directory to search for linked notes | directory of `start_file` |

### Examples

```bash
# Crawl from an entry point, output to combined.md
obsidian-concat WPROWADZENIE.md

# Specify output and vault root
obsidian-concat WPROWADZENIE.md -o full_notes.md -d /path/to/vault

# Start from a nested index file
obsidian-concat "LISTA NOTATEK/5.10 - czym jest NLP/WPROWADZENIE.md" -d .
```

## How It Works

The tool runs a three-stage pipeline:

```
1. Index  →  2. Crawl  →  3. Concat
```

### 1. Index

Recursively scans the vault directory for all `*.md` files and builds two lookup tables:

- **Relative-path index** — maps the lowercased relative path (without `.md`) to the resolved file path (e.g. `"notes/topic/intro"` → `/vault/notes/topic/INTRO.md`)
- **Basename index** — maps the lowercased stem to a list of matching files, sorted shortest-path-first (to replicate Obsidian's resolution heuristic)

### 2. Crawl

Starting from the entry-point file, performs a **breadth-first search** over the wikilink graph:

1. Parse `[[wikilinks]]` from the current file using a regex, stripping aliases (`|…`) and heading anchors (`#…`)
2. Resolve each link target against the index — first by exact relative path, then by basename (preferring unvisited files)
3. Enqueue any newly discovered files
4. Repeat until the queue is empty

### 3. Concat

Writes all discovered files into a single output file in BFS visitation order. Each note is separated by a horizontal rule and an HTML comment identifying the source:

```markdown
---
<!-- source: path/to/note.md -->
---

(note content here)

---
<!-- source: path/to/another-note.md -->
---

(another note content here)
```

## Project Structure

```
src/obsidian_concat/
├── __init__.py   # Package docstring
├── cli.py        # argparse entry point
├── index.py      # Vault file indexer (build_index)
├── crawl.py      # Wikilink extraction + BFS crawl
└── concat.py     # Ordered file concatenation
tests/
└── test_integration.py   # Pytest suite (index, links, crawl, concat)
```

## Development

```bash
# Install dependencies (including dev group)
uv sync

# Run the test suite
uv run pytest -v
```

## License

No license specified.
