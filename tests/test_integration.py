"""Integration tests for obsidian-concat."""

from pathlib import Path

from obsidian_concat.concat import concat
from obsidian_concat.crawl import crawl, extract_links
from obsidian_concat.index import build_index


def _make_vault(tmp_path: Path, files: dict[str, str]) -> Path:
    """Create a mini vault under tmp_path from {relative_path: content}."""
    for relpath, content in files.items():
        p = tmp_path / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return tmp_path


# ── index ───────────────────────────────────────────────────────────


def test_build_index_finds_all_files(tmp_path):
    vault = _make_vault(tmp_path, {
        "root.md": "",
        "sub/child.md": "",
    })
    relpath_idx, basename_idx = build_index(vault)
    assert "root" in basename_idx
    assert "child" in basename_idx
    assert "root" in relpath_idx
    assert "sub/child" in relpath_idx


def test_build_index_basename_sorted_shortest_first(tmp_path):
    vault = _make_vault(tmp_path, {
        "A.md": "short",
        "deep/nested/folder/A.md": "long",
    })
    _, basename_idx = build_index(vault)
    paths = basename_idx["a"]
    assert len(paths) == 2
    assert paths[0] == (vault / "A.md").resolve()


def test_build_index_relpath_distinguishes_duplicates(tmp_path):
    vault = _make_vault(tmp_path, {
        "INTRO.md": "root",
        "notes/topic/INTRO.md": "nested",
    })
    relpath_idx, _ = build_index(vault)
    assert relpath_idx["intro"] == (vault / "INTRO.md").resolve()
    assert relpath_idx["notes/topic/intro"] == (vault / "notes/topic/INTRO.md").resolve()


# ── extract_links ──────────────────────────────────────────────────


def test_extract_simple_link(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("See [[Target]] for details.", encoding="utf-8")
    assert extract_links(f) == ["Target"]


def test_extract_alias_link(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("See [[Target|display name]].", encoding="utf-8")
    assert extract_links(f) == ["Target"]


def test_extract_heading_anchor(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("See [[Target#section]].", encoding="utf-8")
    assert extract_links(f) == ["Target"]


def test_extract_path_link_preserves_path(tmp_path):
    """extract_links now returns full path, not just basename."""
    f = tmp_path / "test.md"
    f.write_text("See [[folder/Sub/Target]].", encoding="utf-8")
    assert extract_links(f) == ["folder/Sub/Target"]


def test_extract_combined(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("See [[folder/Target#h|alias]].", encoding="utf-8")
    assert extract_links(f) == ["folder/Target"]


def test_extract_multiple(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("[[A]] and [[B]] and [[C|see C]]", encoding="utf-8")
    assert extract_links(f) == ["A", "B", "C"]


# ── crawl ──────────────────────────────────────────────────────────


def test_crawl_single_file(tmp_path):
    vault = _make_vault(tmp_path, {"start.md": "no links here"})
    idx = build_index(vault)
    order = crawl(vault / "start.md", idx)
    assert len(order) == 1


def test_crawl_follows_links(tmp_path):
    vault = _make_vault(tmp_path, {
        "start.md": "go to [[A]] and [[B]]",
        "A.md": "leaf A",
        "B.md": "leaf B links to [[A]]",
    })
    idx = build_index(vault)
    order = crawl(vault / "start.md", idx)
    assert len(order) == 3
    assert order[0] == (vault / "start.md").resolve()
    names = [p.stem for p in order]
    assert "A" in names
    assert "B" in names


def test_crawl_handles_cycles(tmp_path):
    vault = _make_vault(tmp_path, {
        "X.md": "[[Y]]",
        "Y.md": "[[X]]",
    })
    idx = build_index(vault)
    order = crawl(vault / "X.md", idx)
    assert len(order) == 2


def test_crawl_ignores_broken_links(tmp_path):
    vault = _make_vault(tmp_path, {
        "start.md": "[[nonexistent]] and [[real]]",
        "real.md": "hi",
    })
    idx = build_index(vault)
    order = crawl(vault / "start.md", idx)
    assert len(order) == 2


def test_crawl_deep_chain(tmp_path):
    vault = _make_vault(tmp_path, {
        "A.md": "[[B]]",
        "B.md": "[[C]]",
        "C.md": "[[D]]",
        "D.md": "end",
    })
    idx = build_index(vault)
    order = crawl(vault / "A.md", idx)
    assert [p.stem for p in order] == ["A", "B", "C", "D"]


def test_crawl_resolves_path_link_over_basename_collision(tmp_path):
    """When two files share a basename, a path-prefixed link resolves to the right one."""
    vault = _make_vault(tmp_path, {
        "ROOT.md": "[[notes/topic/ROOT]]",
        "notes/topic/ROOT.md": "nested content [[Leaf]]",
        "Leaf.md": "leaf",
    })
    idx = build_index(vault)
    order = crawl(vault / "ROOT.md", idx)
    assert len(order) == 3
    stems = [p.stem for p in order]
    assert stems.count("ROOT") == 2
    assert "Leaf" in stems


# ── concat ─────────────────────────────────────────────────────────


def test_concat_output_contains_all_sources(tmp_path):
    vault = _make_vault(tmp_path, {
        "one.md": "content one",
        "two.md": "content two",
    })
    files = [vault / "one.md", vault / "two.md"]
    out = tmp_path / "out.md"
    concat(files, out, vault)
    text = out.read_text(encoding="utf-8")
    assert "content one" in text
    assert "content two" in text
    assert "<!-- source: one.md -->" in text
    assert "<!-- source: two.md -->" in text


def test_concat_preserves_order(tmp_path):
    vault = _make_vault(tmp_path, {
        "first.md": "FIRST",
        "second.md": "SECOND",
    })
    files = [vault / "first.md", vault / "second.md"]
    out = tmp_path / "out.md"
    concat(files, out, vault)
    text = out.read_text(encoding="utf-8")
    assert text.index("FIRST") < text.index("SECOND")
