# CLAUDE.md — Codex Repository

## What This Repository Is

A document-editing toolkit for programmatically revising **HWPX** (Hangul Word Processor XML) files. The primary artifact is the 2026 Smart Energy Platform FEMS+ business proposal for 벽진바이오텍 (Byukjin BioTech), and the tools here automate repetitive text revisions across that multi-thousand-paragraph document.

The consortium behind the proposal:
- **벽진바이오텍** (demand enterprise) — provides site data and self-operates FEMS+
- **GS시스템** (supply partner) — builds on-site measurement infrastructure, data collection, commissioning, maintenance
- **KOTITI시험연구원** (support partner) — performs LCA, product-level carbon emission calculation, verification

---

## Repository Layout

```
/
├── tools/                          # Python editing utilities (see below)
├── outputs/
│   └── project_tracker/            # Project management deliverables
│       ├── 2026년_지원사업_프로젝트_진행관리_개편본.xlsx
│       └── *.png                   # Dashboard screenshots
├── *.hwpx / *.hwp                  # Source and intermediate HWPX documents
├── 최종_*.docx / *.pdf             # Final output documents (Word / PDF)
└── 2026년_지원사업 견적_통합관리.xlsx  # Quotation management spreadsheet
```

### Source Document Versions

| File | Role |
|---|---|
| `*_v3.1.hwpx` | Original source for GS Systems revision scripts |
| `*_v4.1.hwpx` | Later source used by `hwpx_gs_edit.py` and `revise_gs_hwpx.py` |
| `260604(취합본)_*_v1.1.hwpx` | Consolidated draft |
| `최종_*_v4.1.docx / .pdf` | Final outputs |

---

## HWPX Format Internals

HWPX is a **ZIP archive** containing XML files (similar to OOXML / DOCX).

Key internal paths:
- `Contents/header.xml` — document styles, including character properties (`<hh:charPr>`)
- `Contents/section0.xml` — all body content: paragraphs, tables, runs, text nodes

### XML Structure

```
<hs:sec>                        ← section root
  <hp:p id="..." paraPrIDRef="...">    ← paragraph (1-based index across the whole section)
    <hp:run charPrIDRef="14">          ← text run referencing a char style
      <hp:t>content here</hp:t>        ← actual text
    </hp:run>
  </hp:p>
  <hp:tbl>                       ← table
    <hp:tr>                      ← row
      <hp:tc>                    ← cell
        <hp:subList>
          <hp:p>...</hp:p>
        </hp:subList>
      </hp:tc>
    </hp:tr>
  </hp:tbl>
</hs:sec>
```

### Namespaces

| Prefix | URI | Used for |
|---|---|---|
| `hp` | `http://www.hancom.co.kr/hwpml/2011/paragraph` | Body content |
| `hh` | `http://www.hancom.co.kr/hwpml/2011/head` | Styles/header |
| `hs` | `http://www.hancom.co.kr/hwpml/2011/section` | Section wrapper |
| `hc` | `http://www.hancom.co.kr/hwpml/2011/core` | Core metadata |
| `ha` | `http://www.hancom.co.kr/hwpml/2011/app` | App metadata |
| `hp10` | `http://www.hancom.co.kr/hwpml/2016/paragraph` | 2016 paragraph extensions |

### Blue Highlight Convention

Changed/revised text is marked blue (`#0000FF`) by updating `charPrIDRef` on the `<hp:run>` element. Char style ID **175** is reused when it exists in the header; otherwise a new `<hh:charPr>` entry is cloned from the base style and given `textColor="#0000FF"`.

---

## Tools Reference (`tools/`)

All scripts use only the Python standard library **except** `hwpx_gs_edit.py` which requires `lxml`.

### Inspection / Read-only

| Script | Purpose | Usage |
|---|---|---|
| `inspect_hwpx.py` | List files inside an HWPX ZIP | `python inspect_hwpx.py <file.hwpx>` |
| `root_ns.py` | Print namespace declarations from `section0.xml` and `header.xml` | `python root_ns.py <file.hwpx>` |
| `hwpx_text_index.py` | Search/index paragraphs by text, style ID, color, or index range | `python hwpx_text_index.py <file.hwpx> [options]` |

`hwpx_text_index.py` options:
- `--pattern REGEX` — filter paragraphs by text match
- `--context N` — show N paragraphs before/after each hit
- `--styles` — list char styles; combine with `--color #RRGGBB` to filter by color
- `--style-id ID[,ID2]` — show paragraphs using specific charPr IDs
- `--from-idx N --to-idx N` — show paragraphs in a numeric range

### Editing Tools

#### `gs_hwpx_revise.py` (ET-based, targets v3.1)
Reads `REPLACEMENTS: dict[int, str]` and `DELETE_INDICES: set[int]` (paragraph-index → new text mappings), applies them via `xml.etree.ElementTree`, creates a new charPr in `header.xml` for blue styling.
- Input determined automatically by scanning workspace for `v3.1` in filename
- Output: `(벽진바이오텍)_FEMS플러스_사업계획서_GS시스템_중복정리본.hwpx`
- Also writes a Korean summary `.txt` file

#### `gs_hwpx_revise_safe.py` (regex-based, targets v3.1)
Implements the same revisions as `gs_hwpx_revise.py` but using **string/regex manipulation** instead of DOM parsing. Faster and avoids namespace-stripping issues. Exposes `patch_section_xml(xml_str)` returning `(patched_str, changed_count, blanked_count)`.

#### `gs_hwpx_inplace_patch.py` (binary in-place patch, targets v3.1)
Uses `gs_hwpx_revise_safe.patch_section_xml` then **patches the original ZIP bytes** rather than repacking — preserving the exact original ZIP entry metadata. Pads the patched XML with XML comments to fit within the original compressed stream length.
- Output: `*_원본ZIP패치.hwpx`

#### `hwpx_gs_edit.py` (lxml-based, targets v4.1, **Windows path hardcoded**)
More structural editing: inserts/replaces whole paragraph blocks, removes table rows, performs string substitutions across all `<hp:t>` text nodes.
- Hardcoded `ROOT = r"C:\Users\atom5\Desktop\codex storage"` — must be updated for other environments
- Modes via `sys.argv[1]`: `scan`, `around <idx>...`, `table <idx>...`, `red`, `terms`, `edit`
- Default mode is `edit`

#### `revise_gs_hwpx.py` (ET-based, generic, targets v4.1)
General-purpose revision tool with a `StyleManager` class (handles blue charPr creation/lookup), `set_paragraph_text()`, `set_table()`, `delete_paragraphs()`, and `insert_competition_table()`.
- Usage: `python revise_gs_hwpx.py <input.hwpx> <output.hwpx>`

#### `revise_gs_hwpx_raw.py` (regex-based, generic, targets v4.1)
Pure string-manipulation approach — no XML parsing at all. Uses `patch_paragraphs()` for indexed replacements and `replace_text_everywhere()` for global substitutions.
- Usage: `python revise_gs_hwpx_raw.py <input.hwpx> <output.hwpx>`
- Also strips `<hp:linesegarray>` blocks which hold cached layout data

#### `roundtrip_hwpx.py` (utility)
Reads an HWPX, re-serializes `header.xml` and `section0.xml`, writes back out. Useful for verifying that the XML serializer doesn't corrupt the file.
- Usage: `python roundtrip_hwpx.py <input.hwpx> <output.hwpx>`

---

## Paragraph Indexing

All tools share a **1-based, document-order** paragraph index. Paragraphs inside tables are included; the index counts every `<hp:p>` encountered in a depth-first walk of `section0.xml`.

When modifying paragraphs by index:
1. Use `hwpx_text_index.py --from-idx N --to-idx M` to verify the target text before editing.
2. Blanking (setting text to `""`) is preferred over deleting `<hp:p>` nodes to avoid shifting all subsequent indices.
3. The `linesegarray` child of a paragraph is cached layout data — it can be removed after text edits without affecting content.

---

## Development Conventions

- All Python files start with `from __future__ import annotations`.
- Standard library only, no third-party dependencies, **except** `hwpx_gs_edit.py` requires `lxml`.
- No type stubs or package configuration files — this is a standalone scripts collection.
- Scripts in `tools/` resolve the workspace root via `Path(__file__).resolve().parents[1]` (one level up from `tools/`).
- `hwpx_gs_edit.py` has a hardcoded Windows path; port it by changing `ROOT` or replacing the path logic before use on Linux/macOS.
- Outputs are written to the workspace root, never to `tools/`.

---

## Gitignore Patterns

```
.codex-tools/
codex PR/
docx_render_check/
*_hwpx_unpacked/
__pycache__/
*.pyc
```

Unpacked HWPX directories (created for inspection) and Python caches are excluded.

---

## Common Workflows

### Inspect a document's paragraph content
```bash
python tools/hwpx_text_index.py "(벽진바이오텍)_2026년_스마트에너지플랫폼_FEMS플러스_구축사업_사업계획서_v4.1.hwpx" \
    --pattern "GS시스템" --context 2
```

### Find paragraphs by index range
```bash
python tools/hwpx_text_index.py <file.hwpx> --from-idx 220 --to-idx 240
```

### List char styles and find blue-colored ones
```bash
python tools/hwpx_text_index.py <file.hwpx> --styles --color "#0000ff"
```

### Apply GS Systems revisions to v4.1 source
```bash
python tools/revise_gs_hwpx.py \
    "(벽진바이오텍)_2026년_스마트에너지플랫폼_FEMS플러스_구축사업_사업계획서_v4.1.hwpx" \
    output.hwpx
```

### Verify a roundtrip doesn't corrupt the file
```bash
python tools/roundtrip_hwpx.py input.hwpx roundtrip_check.hwpx
```

---

## Adding New Text Revisions

1. Run `hwpx_text_index.py --pattern "..." --context 2` to locate the target paragraph index.
2. Confirm the surrounding paragraphs with `--from-idx` / `--to-idx`.
3. Add the index → new text entry to `REPLACEMENTS` in `gs_hwpx_revise.py` (or the equivalent dict in `revise_gs_hwpx_raw.py`).
4. To blank a paragraph entirely, add its index to `DELETE_INDICES` (v3.1 tools) or set its value to `""` in the patches dict (v4.1 tools).
5. Re-run the revision script and open the output in Hancom Office to verify blue-highlighted changes.

---

## Important Notes for AI Assistants

- **Do not guess paragraph indices.** Always verify with `hwpx_text_index.py` first; indices shift whenever paragraphs are inserted or deleted.
- **Blanking is safer than deletion.** Setting text to `""` leaves the `<hp:p>` node in place, preventing index drift for all subsequent paragraphs.
- **`linesegarray` is safe to remove.** It contains cached typesetting layout and is regenerated by Hancom Office on next open.
- **Blue text marks AI/tool edits.** New or revised text should use charPr ID 175 (or a clone with `textColor="#0000FF"`) so human reviewers can see what changed.
- **The v3.1 and v4.1 tools target different source files.** `gs_hwpx_revise*.py` and `gs_hwpx_inplace_patch.py` expect a `v3.1` marker in the source filename. `revise_gs_hwpx.py`, `revise_gs_hwpx_raw.py`, and `hwpx_gs_edit.py` take explicit `<input> <output>` arguments or use `v4.1`.
- **`hwpx_gs_edit.py` is Windows-only as written.** The `ROOT` constant must be updated before running on any other platform.
