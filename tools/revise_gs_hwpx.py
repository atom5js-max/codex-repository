from __future__ import annotations

import copy
import os
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
}

ROOT_NS_DECLS = [
    'xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app"',
    'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"',
    'xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph"',
    'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"',
    'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"',
    'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"',
    'xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history"',
    'xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page"',
    'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf"',
    'xmlns:dc="http://purl.org/dc/elements/1.1/"',
    'xmlns:opf="http://www.idpf.org/2007/opf/"',
    'xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart"',
    'xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar"',
    'xmlns:epub="http://www.idpf.org/2007/ops"',
    'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"',
]

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)
ET.register_namespace("ha", "http://www.hancom.co.kr/hwpml/2011/app")
ET.register_namespace("hp10", "http://www.hancom.co.kr/hwpml/2016/paragraph")
ET.register_namespace("hhs", "http://www.hancom.co.kr/hwpml/2011/history")
ET.register_namespace("hm", "http://www.hancom.co.kr/hwpml/2011/master-page")
ET.register_namespace("hpf", "http://www.hancom.co.kr/schema/2011/hpf")
ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
ET.register_namespace("opf", "http://www.idpf.org/2007/opf/")
ET.register_namespace("ooxmlchart", "http://www.hancom.co.kr/hwpml/2016/ooxmlchart")
ET.register_namespace("hwpunitchar", "http://www.hancom.co.kr/hwpml/2016/HwpUnitChar")
ET.register_namespace("epub", "http://www.idpf.org/2007/ops")
ET.register_namespace("config", "urn:oasis:names:tc:opendocument:xmlns:config:1.0")


def q(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"


def lname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def iter_paragraphs(root: ET.Element):
    idx = 0
    parents: dict[ET.Element, ET.Element] = {}

    def walk(elem: ET.Element):
        nonlocal idx
        for child in elem:
            parents[child] = elem
            if lname(child.tag) == "p":
                idx += 1
                yield idx, child
            yield from walk(child)

    return list(walk(root)), parents


def build_paragraph_index(root: ET.Element):
    rows, parents = iter_paragraphs(root)
    index = {idx: elem for idx, elem in rows}
    return index, parents


def max_numeric_id(root: ET.Element) -> int:
    max_id = 0
    for elem in root.iter():
        value = elem.attrib.get("id")
        if value and value.isdigit():
            max_id = max(max_id, int(value))
    return max_id


class StyleManager:
    def __init__(self, header: ET.Element):
        self.header = header
        self.char_props = header.find(".//hh:charProperties", NS)
        if self.char_props is None:
            raise RuntimeError("charProperties not found")
        self.char_by_id = {
            char.attrib["id"]: char
            for char in self.char_props.findall("hh:charPr", NS)
            if "id" in char.attrib
        }
        self.next_id = max(int(cid) for cid in self.char_by_id if cid.isdigit()) + 1
        self.blue_cache: dict[str, str] = {}

    def blue(self, char_id: str | None) -> str:
        if "175" in self.char_by_id:
            return "175"
        source_id = char_id if char_id in self.char_by_id else "14"
        source = self.char_by_id[source_id]
        if source.attrib.get("textColor", "").lower() == "#0000ff":
            return source_id
        if source_id in self.blue_cache:
            return self.blue_cache[source_id]

        new = copy.deepcopy(source)
        new_id = str(self.next_id)
        self.next_id += 1
        new.attrib["id"] = new_id
        new.attrib["textColor"] = "#0000FF"
        self.char_props.append(new)
        self.char_by_id[new_id] = new
        self.blue_cache[source_id] = new_id
        self.char_props.attrib["itemCnt"] = str(len(self.char_props.findall("hh:charPr", NS)))
        return new_id


def direct_runs(p: ET.Element) -> list[ET.Element]:
    return [child for child in p if lname(child.tag) == "run"]


def first_text_node(run: ET.Element) -> ET.Element:
    for node in run.iter():
        if lname(node.tag) == "t":
            return node
    node = ET.Element(q("hp", "t"))
    run.append(node)
    return node


def set_paragraph_text(p: ET.Element, text: str, styles: StyleManager | None = None) -> None:
    runs = direct_runs(p)
    if not runs:
        run = ET.Element(q("hp", "run"), {"charPrIDRef": "14"})
        run.append(ET.Element(q("hp", "t")))
        p.append(run)
        runs = [run]

    first = True
    touched_text_node = False
    for run in runs:
        if styles is not None and text:
            run.attrib["charPrIDRef"] = styles.blue(run.attrib.get("charPrIDRef"))
        for node in run.iter():
            if lname(node.tag) == "t":
                touched_text_node = True
                node.text = text if first else ""
                first = False
    if first and text:
        first_text_node(runs[0]).text = text
    elif first and not touched_text_node:
        return


def delete_paragraphs(index: dict[int, ET.Element], parents: dict[ET.Element, ET.Element], ids: set[int]) -> int:
    cleared = 0
    for idx in sorted(ids):
        p = index.get(idx)
        if p is None:
            continue
        if p.find(".//hp:tbl", NS) is not None:
            clear_all_table_text(p)
        else:
            set_paragraph_text(p, "", None)
        cleared += 1
    return cleared


def table_rows(table_p: ET.Element) -> list[ET.Element]:
    tbl = table_p.find(".//hp:tbl", NS)
    if tbl is None:
        raise RuntimeError("table not found")
    return [child for child in tbl if lname(child.tag) == "tr"]


def table_cells(row: ET.Element) -> list[ET.Element]:
    return [child for child in row if lname(child.tag) == "tc"]


def first_cell_paragraph(cell: ET.Element) -> ET.Element:
    p = cell.find(".//hp:p", NS)
    if p is None:
        raise RuntimeError("cell paragraph not found")
    return p


def clear_cell(cell: ET.Element) -> ET.Element:
    paragraphs = cell.findall(".//hp:p", NS)
    if not paragraphs:
        raise RuntimeError("cell paragraph not found")
    for p in paragraphs:
        set_paragraph_text(p, "", None)
    return paragraphs[0]


def set_table(table_p: ET.Element, rows: list[list[str]], styles: StyleManager) -> None:
    tbl = table_p.find(".//hp:tbl", NS)
    if tbl is None:
        raise RuntimeError("table not found")
    tr_list = [child for child in tbl if lname(child.tag) == "tr"]
    for row_index, row in enumerate(tr_list):
        values = rows[row_index] if row_index < len(rows) else []
        cells = table_cells(row)
        for cell_index, cell in enumerate(cells):
            value = values[cell_index] if cell_index < len(values) else ""
            set_paragraph_text(clear_cell(cell), value, styles)


def clear_all_table_text(table_p: ET.Element) -> None:
    for row in table_rows(table_p):
        for cell in table_cells(row):
            set_paragraph_text(first_cell_paragraph(cell), "", None)


def remap_ids(elem: ET.Element, next_id: int) -> int:
    for node in elem.iter():
        value = node.attrib.get("id")
        if value and value.isdigit():
            node.attrib["id"] = str(next_id)
            next_id += 1
    return next_id


def insert_competition_table(section: ET.Element, index: dict[int, ET.Element], parents: dict[ET.Element, ET.Element], styles: StyleManager) -> None:
    anchor = index[2104]
    source = index[1950]
    new_table = copy.deepcopy(source)
    next_id = max_numeric_id(section) + 1
    remap_ids(new_table, next_id)

    set_table(
        new_table,
        [
            ["구분", "전문기반 확보", "본 사업 적용", "확산 가능성", "관리 방향"],
            [
                "계측·제어 기반",
                "산업자동화, PLC·HMI, 현장통신 구축 경험",
                "계측기·제어반·Gateway 연계 구축",
                "유사 제조현장 FEMS+ 구축모델 적용",
                "시운전·점검 표준화",
            ],
            [
                "데이터 관리 기반",
                "Raw/Processed Data, DB, 이상값 탐지 체계",
                "FEMS+ 대시보드와 MRV 연계 기초자료 관리",
                "탄소관리·MRV 대응 서비스 확장",
                "데이터 품질 관리",
            ],
            [
                "섬유공정 특화",
                "텐터·보일러·스팀·용수 설비 이해",
                "벽진BIO텍 공정별 계측 포인트와 수집체계 구축",
                "섬유 염색·후가공 기업 확산",
                "동종 공정 적용",
            ],
        ],
        styles,
    )

    parent = parents[anchor]
    pos = list(parent).index(anchor)
    parent.insert(pos + 1, new_table)


def paragraph_text(p: ET.Element) -> str:
    return "".join((node.text or "") for node in p.iter() if lname(node.tag) == "t")


def clean_compressed_air(index: dict[int, ET.Element], styles: StyleManager) -> int:
    replacements = {
        "전력, LNG, 스팀, 용수, 압축공기 등": "전력, LNG, 스팀, 용수 등",
        "전력, 스팀, LNG, 용수, 압축공기": "전력, 스팀, LNG, 용수",
        "전력, LNG, 스팀, 용수, 압축공기": "전력, LNG, 스팀, 용수",
        "전력, 스팀, 용수, LNG, 압축공기": "전력, 스팀, 용수, LNG",
        "스팀, 용수, 압축공기 등": "스팀, 용수 등",
        "스팀, 용수, 압축공기": "스팀, 용수",
        "피크부하, 대기전력, 스팀누설, 압축공기 누설 등 손실요인 개선": "피크부하, 대기전력, 스팀누설 등 손실요인 개선",
        "스팀누설 보수, 압축공기 누설 개선, 계측기 추가 설치": "스팀누설 보수, 계측기 추가 설치",
        "압축공기 절감방안": "계측데이터 기반 절감방안",
    }
    clear_values = {
        "압축공기",
        "압축공기 계통",
        "컴프레서 전력",
        "컴프레서 전력, 압력, 공기 사용량",
        "공기 사용량",
        "압축공기 사용량 및 누설관리",
        "누설, 고압운전, 불필요 운전",
        "누설점검, 압력 최적화, 불필요 운전 방지",
        "누설점검, 압력 최적화, 컴프레서 운전관리",
        "전력 절감, 설비 효율 향상",
        "유전력",
        "유량계·전력계",
    }
    changed = 0
    for p in index.values():
        if p.find(".//hp:tbl", NS) is not None:
            continue
        text = paragraph_text(p)
        if not text:
            continue
        if text.strip() in clear_values:
            set_paragraph_text(p, "", None)
            changed += 1
            continue
        if "압축공기" not in text:
            continue
        new_text = text
        for old, new in replacements.items():
            new_text = new_text.replace(old, new)
        if "압축공기" in new_text:
            new_text = new_text.replace(", 압축공기", "").replace("압축공기, ", "").replace("압축공기 등", "").replace("압축공기", "")
            new_text = new_text.replace("  ", " ").replace(", 등", " 등")
        if new_text != text:
            set_paragraph_text(p, new_text.strip(), styles if new_text.strip() else None)
            changed += 1
    return changed


def write_hwpx(src: Path, dst: Path, header_xml: bytes, section_xml: bytes) -> None:
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(dst, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "Contents/header.xml":
                data = header_xml
            elif info.filename == "Contents/section0.xml":
                data = section_xml
            new_info = zipfile.ZipInfo(info.filename, info.date_time)
            new_info.compress_type = info.compress_type
            new_info.external_attr = info.external_attr
            zout.writestr(new_info, data)


def serialize_hwpx_xml(elem: ET.Element) -> bytes:
    text = ET.tostring(elem, encoding="unicode", xml_declaration=False)
    root_match = re.match(r"<[^>]+>", text)
    if root_match:
        root_tag = root_match.group(0)
        inserts = []
        for decl in ROOT_NS_DECLS:
            key = decl.split("=", 1)[0]
            if key not in root_tag:
                inserts.append(decl)
        if inserts:
            text = text[: root_match.end() - 1] + " " + " ".join(inserts) + text[root_match.end() - 1 :]
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' + text).encode("utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: revise_gs_hwpx.py <input.hwpx> <output.hwpx>")
        return 2

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    with zipfile.ZipFile(src, "r") as zf:
        header = ET.fromstring(zf.read("Contents/header.xml"))
        section = ET.fromstring(zf.read("Contents/section0.xml"))

    styles = StyleManager(header)
    index, parents = build_paragraph_index(section)

    replacements = {
        # Role table summary.
        221: "ㆍ전력·LNG·스팀·용수 계측 포인트 검토 및 설치",
        222: "",
        223: "ㆍ계측장비·통신모듈 구성 및 현장 시공",
        224: "ㆍ배선·결선·통신 환경 점검",
        226: "FEMS+ 연계 기반 구축",
        227: "ㆍPLC·HMI·통신장비와 데이터 수집장치 연계",
        228: "ㆍRS-485, Modbus, Ethernet 기반 수집 체계 구축",
        229: "ㆍFEMS+·MRV 연계용 항목·단위·주기·태그 정리",
        230: "ㆍ누락·이상값·통신불량 점검",
        231: "시운전·유지보수",
        232: "ㆍ계측기·통신상태·데이터 수집상태 시운전",
        233: "ㆍ장애 대응, 계측기·통신장비 점검",
        234: "ㆍ수요기업 담당자 운영교육",
        235: "ㆍ성과활용기간 정기점검 및 유지보수 관리",
        # General status.
        356: "- 본 사업에서는 계측 인프라 구축, PLC·HMI·통신 연계, 데이터 수집·점검 및 시운전·유지보수를 수행함.",
        496: "2) 참여-공급기관",
        498: " GS시스템 기술역량은 본 사업 수행범위에 맞춰 다음 6개 항목으로 요약함.",
        622: " GS시스템 기술역량 요약표",
        # Participant 1 goal/content/deliverables.
        1889: "① 추진목표",
        1890: "- 계측 인프라와 PLC·HMI·통신 연계를 구축하여 수요기업의 전력·LNG·스팀·용수 데이터를 수집함.",
        1891: "- 수집데이터를 DB, FEMS+ 대시보드, MRV 연계 기초자료로 관리함.",
        1892: "- 시운전, 운영교육, 장애 대응 및 정기점검으로 성과활용기간 운영 안정성을 확보함.",
        1908: "② 수행내용",
        2012: "③ 주요 산출물",
        2013: "- 현장조사표, 계측 포인트 검토표, 계측기 목록 및 설치확인표",
        2014: "- 통신 구성도, 통신주소표, 태그 리스트",
        2015: "- 수집항목 정의서, DB 항목표, 데이터 매핑표",
        2016: "- FEMS+·MRV 연계 기초자료 및 정상 수집 데이터 샘플",
        2017: "- 시운전 결과서, 운영교육자료, 유지보수 점검보고서",
        # Competition strategy.
        2104: " GS시스템 경쟁력 확보 전략",
    }
    for idx, text in replacements.items():
        set_paragraph_text(index[idx], text, styles if text else None)

    # Existing summary table in the technical capability section.
    set_table(
        index[623],
        [
            ["구분", "기술역량", "본 사업 적용내용"],
            ["1", "계측 인프라 구축", "전력·LNG·스팀·용수 계측 포인트 검토, 계측기 설치, 배선·결선 점검"],
            ["2", "PLC·HMI·통신 연계", "PLC·HMI·Gateway, RS-485/Modbus/Ethernet 통신 연계 구축"],
            ["3", "데이터 수집·DB 구성", "현장 계측 Raw Data 수집, DB 저장구조 및 이상값 탐지·분석 대시보드 구축"],
            ["4", "FEMS+·MRV 연계", "FEMS+ 활용 항목과 MRV 연계용 데이터 매핑·전송자료 관리"],
            ["5", "섬유공정 특화", "텐터·보일러·스팀·용수 등 섬유가공 설비 특성을 반영한 계측 위치 선정"],
            ["6", "시운전·유지보수", "계측기·통신·수집상태 점검, 운영교육, 장애 대응 및 정기점검 관리"],
        ],
        styles,
    )

    # Participant content table.
    set_table(
        index[1950],
        [
            ["구분", "추진단계", "주요 추진내용", "GS시스템 수행내용", "주요 산출물"],
            ["1", "계측 인프라 구축", "현장 에너지원별 계측지점 도출", "계측기 선정·설치·배선·결선 수행", "현장조사표, 계측 포인트 검토표, 설치확인표"],
            ["2", "PLC·HMI·통신 연계", "계측기와 제어·통신장비 연결", "PLC·HMI·Gateway 통신 설정 및 점검", "통신 구성도, 주소표, 태그 리스트"],
            ["3", "데이터 수집·DB 구성", "Raw/Processed Data 수집 구조 구성", "DB 항목, 단위, 수집주기, 이상값 탐지 기준 관리", "수집항목표, DB 항목표, 점검표"],
            ["4", "FEMS+·MRV 연계", "FEMS+ 대시보드 및 MRV 기초자료 연계", "데이터 매핑, 전송자료, 정상 수집 샘플 정리", "데이터 매핑표, MRV 연계 기초자료"],
            ["5", "섬유공정 특화", "텐터·보일러·스팀·용수 설비 반영", "공정별 계측 위치와 설비코드 정리", "계측 위치도, 설비코드표"],
            ["6", "시운전·유지보수", "구축 후 운영 안정화", "계측·통신·수집상태 점검, 교육, 장애 대응", "시운전 결과서, 교육자료, 점검보고서"],
        ],
        styles,
    )

    if os.environ.get("SKIP_COMPETITION_TABLE") != "1":
        insert_competition_table(section, index, parents, styles)
    compressed_air_changes = clean_compressed_air(index, styles)

    delete_ids = set()
    delete_ids.update(range(357, 363))
    delete_ids.update([497])
    delete_ids.update(range(499, 622))
    delete_ids.update(range(1893, 1908))
    delete_ids.update(range(1909, 1950))
    delete_ids.update(range(2018, 2031))
    delete_ids.update(range(2032, 2042))
    delete_ids.update(range(2105, 2169))
    deleted = delete_paragraphs(index, parents, delete_ids)

    header_xml = serialize_hwpx_xml(header)
    section_xml = serialize_hwpx_xml(section)
    write_hwpx(src, dst, header_xml, section_xml)

    print(f"wrote={dst}")
    print(f"deleted_paragraphs={deleted}")
    print(f"blue_style_clones={len(styles.blue_cache)}")
    print(f"compressed_air_changes={compressed_air_changes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
