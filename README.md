# obsidian-concat

Crawl an Obsidian vault starting from a given entry-point file, follow `[[wikilinks]]` in BFS order, and concatenate all reachable notes into a single markdown file.

## Features

- **Link-graph crawl** — follows `[[wikilinks]]` (BFS), not just a flat directory listing
- **Obsidian-aware resolution** — handles `[[Page]]`, `[[Page|alias]]`, `[[Page#heading]]`, `[[folder/Page]]` and duplicate basenames
- **Cycle-safe** — tracks visited files, never processes a note twice
- **Zero dependencies** — stdlib only, Python 3.12+

## Install globally (isolated)

```bash
uv tool install /path/to/obsidian-concat
```

This makes `obsidian-concat` available everywhere without polluting your global Python.

## Usage

```bash
obsidian-concat <start_file> [-o OUTPUT] [-d VAULT_DIR]
```

| Argument | Description | Default |
|---|---|---|
| `start_file` | Entry-point `.md` file (required) | — |
| `-o`, `--output` | Output file path | `combined.md` |
| `-d`, `--vault-dir` | Vault root to search for linked notes | directory of `start_file` |

### Examples

```bash
# Crawl from root, output to combined.md
obsidian-concat WPROWADZENIE.md

# Specify output and vault root
obsidian-concat WPROWADZENIE.md -o full_notes.md -d /path/to/vault

# Start from a nested index file
obsidian-concat "LISTA NOTATEK/5.10 - czym jest NLP/WPROWADZENIE.md" -d .
```

## Development

```bash
uv sync
uv run pytest -v
```
