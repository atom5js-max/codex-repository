from __future__ import annotations

import argparse
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
}


def qname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def text_of(p: ET.Element) -> str:
    chunks: list[str] = []
    for node in p.iter():
        if qname(node.tag) == "t":
            chunks.append(node.text or "")
        elif qname(node.tag) == "lineBreak":
            chunks.append("\\n")
    return "".join(chunks).strip()


def run_styles(p: ET.Element) -> str:
    styles = []
    for run in p.findall("hp:run", NS):
        ref = run.attrib.get("charPrIDRef")
        if ref is not None:
            styles.append(ref)
    return ",".join(sorted(set(styles), key=lambda x: int(x) if x.isdigit() else x))


def table_depth(elem: ET.Element, stack: list[str]) -> int:
    return sum(1 for s in stack if s == "tbl")


def iter_paragraphs(root: ET.Element):
    idx = 0

    def walk(elem: ET.Element, stack: list[str]):
        nonlocal idx
        name = qname(elem.tag)
        new_stack = stack + [name]
        if name == "p":
            idx += 1
            yield idx, elem, table_depth(elem, stack)
        for child in elem:
            yield from walk(child, new_stack)

    yield from walk(root, [])


def char_colors(header_xml: bytes) -> dict[str, tuple[str | None, str | None]]:
    root = ET.fromstring(header_xml)
    colors: dict[str, tuple[str | None, str | None]] = {}
    for char_pr in root.findall(".//hh:charPr", NS):
        cid = char_pr.attrib.get("id")
        if cid is not None:
            colors[cid] = (
                char_pr.attrib.get("textColor"),
                char_pr.attrib.get("shadeColor"),
            )
    return colors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hwpx")
    parser.add_argument("--pattern")
    parser.add_argument("--context", type=int, default=0)
    parser.add_argument("--styles", action="store_true")
    parser.add_argument("--color")
    parser.add_argument("--style-id")
    parser.add_argument("--from-idx", type=int)
    parser.add_argument("--to-idx", type=int)
    args = parser.parse_args()

    path = Path(args.hwpx)
    with zipfile.ZipFile(path) as zf:
        section = ET.fromstring(zf.read("Contents/section0.xml"))
        colors = char_colors(zf.read("Contents/header.xml"))

    if args.styles:
        wanted = args.color.lower() if args.color else None
        for cid, (text_color, shade_color) in sorted(colors.items(), key=lambda kv: int(kv[0])):
            if wanted and wanted not in ((text_color or "").lower(), (shade_color or "").lower()):
                continue
            attrs = dict(char_pr.attrib) if False else None
            print(f"{cid}\ttext={text_color}\tshade={shade_color}")
        return 0

    rows = []
    pattern = re.compile(args.pattern) if args.pattern else None
    for idx, p, depth in iter_paragraphs(section):
        text = text_of(p)
        styles = run_styles(p)
        if text:
            rows.append((idx, depth, styles, text))

    if args.style_id:
        wanted = set(args.style_id.split(","))
        for idx, depth, styles, text in rows:
            if wanted.intersection(styles.split(",") if styles else []):
                print(f"{idx}\tdepth={depth}\tstyles={styles}\t{text}")
    elif args.from_idx is not None or args.to_idx is not None:
        from_idx = args.from_idx or 0
        to_idx = args.to_idx or 10**12
        for idx, depth, styles, text in rows:
            if from_idx <= idx <= to_idx:
                print(f"{idx}\tdepth={depth}\tstyles={styles}\t{text}")
    elif pattern:
        hit_positions = []
        for pos, row in enumerate(rows):
            if pattern.search(row[3]):
                hit_positions.append(pos)
        emitted = set()
        for pos in hit_positions:
            start = max(0, pos - args.context)
            end = min(len(rows), pos + args.context + 1)
            for out_pos in range(start, end):
                if out_pos in emitted:
                    continue
                emitted.add(out_pos)
                idx, depth, styles, text = rows[out_pos]
                print(f"{idx}\tdepth={depth}\tstyles={styles}\t{text}")
            print("---")
    else:
        style_counter = Counter()
        for idx, depth, styles, text in rows:
            style_counter.update(styles.split(",") if styles else [])
            print(f"{idx}\tdepth={depth}\tstyles={styles}\t{text}")
        print("STYLE_COUNTS", dict(style_counter), file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
