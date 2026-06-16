import copy
import os
import sys
import zipfile
from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\Users\atom5\Desktop\codex storage"
INPUT_MARK = "v4.1"
OUTPUT_NAME = "벽진BIO텍_FEMS플러스_사업계획서_v4.2_GS시스템_수정표시본.hwpx"

NS = {
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
}
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"


def find_input():
    matches = [
        os.path.join(ROOT, f)
        for f in os.listdir(ROOT)
        if f.endswith(".hwpx") and INPUT_MARK in f
    ]
    if not matches:
        raise FileNotFoundError("v4.1 hwpx file not found")
    return matches[0]


def text_of(el):
    return "".join(el.xpath(".//hp:t/text()", namespaces=NS))


def direct_text_of(p):
    parts = []
    for run in p.xpath("./hp:run", namespaces=NS):
        parts.extend(run.xpath("./hp:t/text()", namespaces=NS))
    return "".join(parts)


def get_section_children(sec):
    return [child for child in sec if isinstance(child.tag, str)]


def child_texts(sec):
    return [text_of(child) for child in get_section_children(sec)]


def find_child(sec, needle, start=0, after_text=None):
    texts = child_texts(sec)
    if after_text:
        for idx in range(start, len(texts)):
            if after_text in texts[idx]:
                start = idx + 1
                break
    for idx in range(start, len(texts)):
        if needle in texts[idx]:
            return idx
    raise ValueError(f"Cannot find child containing: {needle}")


def find_child_combo(sec, needles, start=0):
    texts = child_texts(sec)
    for idx in range(start, len(texts)):
        if all(n in texts[idx] for n in needles):
            return idx
    raise ValueError(f"Cannot find child containing all: {needles}")


def find_child_exact(sec, text, start=0):
    texts = child_texts(sec)
    for idx in range(start, len(texts)):
        if texts[idx].strip() == text:
            return idx
    raise ValueError(f"Cannot find exact child text: {text}")


def find_header_count(header):
    return len(header.xpath(".//hh:charPr", namespaces=NS))


def add_blue_charpr(header, base_id="0"):
    char_props = header.xpath(".//hh:charPr", namespaces=NS)
    blue_existing = [
        cp.get("id")
        for cp in char_props
        if cp.get("textColor", "").upper() == "#0000FF" and cp.get("height") == "1000"
    ]
    if blue_existing:
        return blue_existing[0]

    base = None
    for cp in char_props:
        if cp.get("id") == base_id:
            base = cp
            break
    if base is None:
        base = char_props[0]
    new = copy.deepcopy(base)
    new_id = str(max(int(cp.get("id")) for cp in char_props) + 1)
    new.set("id", new_id)
    new.set("textColor", "#0000FF")

    char_prs = header.xpath(".//hh:charProperties", namespaces=NS)
    if char_prs:
        char_prs[0].append(new)
    else:
        base.getparent().append(new)

    # Keep header counters in sync when the document stores them.
    for el in header.iter():
        for attr in ("charPrCnt", "charPropertiesCnt"):
            if attr in el.attrib:
                el.set(attr, str(int(el.get(attr)) + 1))
    return new_id


def get_max_id(sec):
    max_id = 1000000000
    for el in sec.iter():
        value = el.get("id")
        if value and value.isdigit():
            max_id = max(max_id, int(value))
    return max_id


class Builder:
    def __init__(self, sec, charpr):
        self.next_id = get_max_id(sec) + 1
        self.charpr = charpr

    def new_id(self):
        self.next_id += 1
        return str(self.next_id)

    def paragraph(self, text="", para="0", charpr=None):
        p = etree.Element(
            HP + "p",
            id=self.new_id(),
            paraPrIDRef=str(para),
            styleIDRef="0",
            pageBreak="0",
            columnBreak="0",
            merged="0",
        )
        run = etree.SubElement(p, HP + "run", charPrIDRef=str(charpr or self.charpr))
        etree.SubElement(run, HP + "t").text = text
        return p

    def lines(self, items, para="0"):
        return [self.paragraph(item, para=para) for item in items]

    def table_as_lines(self, title, headers, rows):
        out = [self.paragraph(title)]
        out.append(self.paragraph(" | ".join(headers)))
        for row in rows:
            out.append(self.paragraph(" | ".join(row)))
        return out


def insert_replace(sec, start, end, new_nodes):
    children = get_section_children(sec)
    anchor = children[start]
    parent = anchor.getparent()
    insert_at = parent.index(anchor)
    for child in children[start:end]:
        parent.remove(child)
    for offset, node in enumerate(new_nodes):
        parent.insert(insert_at + offset, node)


def replace_gs_history_cell(sec, builder):
    idx = find_child(sec, "2) 참여-공급기관 (GS시스템)")
    children = get_section_children(sec)
    table_child = children[idx + 1]
    tables = table_child.xpath(".//hp:tbl", namespaces=NS)
    if not tables:
        raise ValueError("GS general-status table not found")
    history_table = copy.deepcopy(tables[1]) if len(tables) > 1 else None

    target_cell = None
    for tr in tables[0].xpath("./hp:tr", namespaces=NS):
        cells = tr.xpath("./hp:tc", namespaces=NS)
        if len(cells) >= 2 and "업력" in text_of(cells[0]):
            target_cell = cells[1]
            break
    if target_cell is None:
        raise ValueError("GS history cell not found")

    sublist = target_cell.find("./hp:subList", namespaces=NS)
    if sublist is None:
        raise ValueError("GS history cell subList not found")

    removed = len(list(sublist))
    for child in list(sublist):
        sublist.remove(child)

    new_nodes = builder.lines([
        "- GS시스템은 1983년 설립 이후 산업용 자동제어, 계측제어, 섬유·염색가공 설비 자동화 및 에너지 계측·모니터링 분야를 수행해 온 현장 기반 자동화·계측 전문기업임.",
        "- 주요 보유역량은 전력·LNG·스팀·용수 계측, PLC·HMI 연계, 현장 통신 구성, 데이터 수집장치 구축, 시운전 및 유지보수임.",
        "- 본 사업에서는 FEMS+ 구축에 필요한 현장 계측 인프라와 데이터 수집·연계 기반 구축을 담당함.",
    ])
    for node in new_nodes:
        sublist.append(node)

    # Reattach the original history table after the general-status table.
    for tbl in tables[1:]:
        parent = tbl.getparent()
        if parent is not None:
            parent.remove(tbl)
    if history_table is not None:
        run = etree.Element(HP + "run", charPrIDRef=builder.charpr)
        run.append(history_table)
        table_child.append(run)
    return removed


def print_matches(sec):
    terms = [
        "GS시스템",
        "참여-공급기관",
        "KOTITI",
        "압축공기",
        "AI 분석 기능",
        "AI 기반 분석 기능",
        "10~12",
        "도전목표",
        "업력",
        "주요 연혁",
        "전문 기반 확보 방향",
    ]
    texts = child_texts(sec)
    print("top-level children", len(texts))
    for term in terms:
        print(f"\nTERM {term}")
        hits = [(i, t) for i, t in enumerate(texts) if term in t]
        print("count", len(hits))
        for idx, txt in hits[:30]:
            print(idx, txt.replace("\n", " ")[:220])


def surrounding(sec, indexes):
    texts = child_texts(sec)
    for idx in indexes:
        print(f"\n--- around {idx} ---")
        for j in range(max(0, idx - 6), min(len(texts), idx + 10)):
            print(j, texts[j].replace("\n", " ")[:260])


def inspect_child_tables(sec, indexes):
    children = get_section_children(sec)
    for idx in indexes:
        child = children[idx]
        print(f"\n=== child {idx}: {text_of(child)[:120]} ===")
        tables = child.xpath(".//hp:tbl", namespaces=NS)
        print("tables", len(tables))
        for ti, tbl in enumerate(tables):
            rows = tbl.xpath("./hp:tr", namespaces=NS)
            print("table", ti, "rows", len(rows))
            for ri, tr in enumerate(rows):
                cells = tr.xpath("./hp:tc", namespaces=NS)
                cell_texts = [text_of(tc).replace("\n", " ")[:160] for tc in cells]
                print(" row", ri, "cells", len(cells), cell_texts)
                for ci, tc in enumerate(cells):
                    ps = tc.xpath(".//hp:p", namespaces=NS)
                    if any("업력" in text_of(p) or "주요 연혁" in text_of(p) or "GS시스템" in text_of(p) for p in ps):
                        print("  cell", ci, "paragraphs")
                        for pi, p in enumerate(ps):
                            print("   ", pi, direct_text_of(p).replace("\n", " ")[:180])


def red_contexts(sec, header):
    red_ids = {
        cp.get("id")
        for cp in header.xpath(".//hh:charPr", namespaces=NS)
        if cp.get("textColor", "").upper() == "#FF0000"
    }
    children = get_section_children(sec)
    for idx, child in enumerate(children):
        snippets = []
        for run in child.xpath(".//hp:run", namespaces=NS):
            if run.get("charPrIDRef") in red_ids:
                txt = text_of(run).strip()
                if txt:
                    snippets.append(txt)
        if snippets:
            print(f"\nchild {idx}: {text_of(child)[:240].replace(chr(10), ' ')}")
            for snippet in snippets[:12]:
                print("  RED:", snippet[:180].replace("\n", " "))


def term_contexts(sec):
    terms = ["압축공기", "AI 분석 기능", "AI 기반 분석 기능", "10~12", "도전목표"]
    texts = child_texts(sec)
    for term in terms:
        print(f"\nTERM {term}")
        hits = [(i, t) for i, t in enumerate(texts) if term in t]
        print("count", len(hits))
        for idx, txt in hits[:30]:
            print(idx, txt.replace("\n", " ")[:260])


def make_replacements(sec, header):
    blue = add_blue_charpr(header)
    b = Builder(sec, blue)

    work1_removed = replace_gs_history_cell(sec, b)

    # Refresh after each structural edit.
    skill_heading = find_child_exact(sec, "3. 사업 추진 관련 수행기관별 기술역량")
    idx2_start = find_child(sec, "2) 참여-공급기관", start=skill_heading + 1)
    idx2_end = find_child(sec, "3) 참여-지원기관: KOTITI시험연구원", start=idx2_start + 1)
    repl2 = []
    repl2 += b.lines([
        "  2) 참여-공급기관: GS시스템",
        " GS시스템은 FEMS+ 구축을 위한 현장 계측, PLC·HMI·통신 연계, 데이터 수집·저장, FEMS+·MRV 연계자료 정리, 시운전 및 유지보수 역량을 보유한 공급기업임.",
    ])
    repl2 += b.table_as_lines(
        "[표] GS시스템 핵심 기술역량 요약",
        ["구분", "핵심 역량", "본 사업 적용내용"],
        [
            ["계측 인프라 구축", "전력·LNG·스팀·용수 계측기 선정 및 설치", "설비별·공정별 에너지 사용량 계측 기반 구축"],
            ["PLC·HMI·통신 연계", "RS-485, Modbus RTU/TCP, Ethernet 기반 통신 구성", "계측기와 PLC·HMI·Gateway 간 데이터 수집체계 구축"],
            ["데이터 수집·DB 구성", "Raw Data / Processed Data 분리 저장", "수집데이터 이력관리 및 분석용 데이터 구조 구성"],
            ["FEMS+ 연계", "데이터 항목·단위·수집주기·태그 체계 정리", "FEMS+ 대시보드 및 EnPI 산출용 데이터 기반 제공"],
            ["MRV 연계 지원", "계측기 목록, 데이터 매핑표, 정상 수집 데이터 샘플 정리", "산업단지 MRV 플랫폼 연계 기초자료 제공"],
            ["섬유공정 특화", "텐터기, 보일러, 스팀 계통 등 섬유공정 설비 이해", "공정 특성을 반영한 계측 포인트 선정"],
            ["시운전·유지보수", "계측값, 통신상태, 데이터 수집상태 점검", "장애 대응, 운영자 교육, 정기점검 수행"],
        ],
    )
    repl2 += b.lines([" 주요 계측 대상 및 활용 목적은 다음과 같음."])
    repl2 += b.table_as_lines(
        "[표] 에너지원별 계측 구성",
        ["구분", "주요 계측장비", "주요 측정항목", "활용 목적"],
        [
            ["전력", "전력량계, 전류센서", "전력사용량, 전압, 전류, 역률", "설비별 전력 사용량 및 피크관리"],
            ["LNG", "가스 유량계, 적산유량계", "LNG 사용량, 누적 사용량", "건조·열원설비 연료 사용량 관리"],
            ["스팀", "스팀 유량계, 압력계, 온도계", "스팀 사용량, 압력, 온도", "전처리·염색·수세 공정 열에너지 관리"],
            ["용수", "전자식 유량계, 적산유량계", "용수 사용량, 누적 사용량", "공정별 용수 원단위 및 과다사용 분석"],
            ["공정환경", "온도계, 압력계, 습도센서", "온도, 압력, 습도", "운전조건과 에너지 사용량 상관분석"],
        ],
    )
    repl2 += b.lines([
        " GS시스템은 본 사업에서 다음 업무를 수행함.",
        "- 현장조사 및 계측 포인트 선정",
        "- 계측기 사양 검토, 설치 위치 검토, 배선·결선 수행",
        "- PLC·HMI·Edge Gateway 기반 데이터 수집체계 구축",
        "- 데이터 항목, 단위, 수집주기, 태그, 설비코드 정리",
        "- FEMS+ 대시보드 및 MRV 연계용 데이터 매핑자료 제공",
        "- 계측값, 통신상태, 데이터 수집상태 시운전 수행",
        "- 운영자 교육, 장애 대응, 정기점검 및 유지보수 수행",
    ])
    insert_replace(sec, idx2_start, idx2_end, repl2)

    idx3_start = find_child(sec, "나. 참여기관 1 목표 및 내용: GS시스템")
    idx3_end = find_child(sec, "다. 참여기관 2 목표 및 내용", start=idx3_start + 1)
    repl3 = []
    repl3 += b.lines([
        "   나. 참여기관 1 목표 및 내용: GS시스템",
        " 추진목표",
        "- 전력·LNG·스팀·용수 사용량을 설비별·공정별로 수집할 수 있는 현장 계측 인프라를 구축함.",
        "- PLC·HMI·Edge Gateway 기반의 데이터 수집체계를 구축함.",
        "- FEMS+ 및 MRV 연계에 필요한 데이터 항목·단위·수집주기·태그 체계를 정리함.",
        "- 시운전, 운영자 교육, 장애 대응 및 성과활용기간 유지보수 체계를 운영함.",
        " 수행내용",
    ])
    repl3 += b.table_as_lines(
        "[표] GS시스템 세부 수행내용",
        ["구분", "수행내용", "주요 산출물"],
        [
            ["현장조사", "전력·LNG·스팀·용수 사용계통 및 기존 계측기 현황 확인", "현장조사표, 기존 계측기 현황표"],
            ["계측 포인트 선정", "설비별·공정별 계측 필요 지점 도출, 설치공간 및 배선경로 검토", "계측 포인트 검토표, 계측 위치도"],
            ["계측 인프라 구축", "전력량계, LNG 유량계, 스팀 유량계, 용수 유량계 설치 및 결선", "계측기 목록, 설치사진, 결선자료"],
            ["통신·데이터 수집", "PLC·HMI·Edge Gateway 연계, 통신주소·배율·단위·태그 설정", "통신 구성도, 주소표, 태그 리스트"],
            ["FEMS+ 연계", "데이터 항목, 단위, 수집주기, 설비코드, 데이터 매핑 정리", "데이터 매핑표, 연계항목표"],
            ["MRV 연계 지원", "계측기 목록, 데이터 항목표, 정상 수집 데이터 샘플 제공", "MRV 연계 기초자료"],
            ["시운전·교육", "계측값, 통신상태, 데이터 수집상태 점검 및 운영자 교육", "시운전 결과서, 교육자료"],
            ["유지보수", "계측기, PLC, Gateway, 통신장비 정기점검 및 장애 대응", "유지보수 이력, 점검보고서"],
        ],
    )
    repl3 += b.lines([
        " 주요 산출물",
        "- 현장조사표",
        "- 기존 계측기 현황표",
        "- 계측 포인트 검토표",
        "- 계측기 목록 및 사양서",
        "- 계측 위치도",
        "- 통신 구성도",
        "- 통신주소표",
        "- 데이터 태그 리스트",
        "- 수집항목 정의서",
        "- 데이터 단위표",
        "- 데이터 수집주기표",
        "- 데이터 매핑표",
        "- 정상 수집 데이터 샘플",
        "- 시운전 결과서",
        "- 운영자 교육자료",
        "- 유지보수 점검보고서",
    ])
    insert_replace(sec, idx3_start, idx3_end, repl3)

    idx4_start = find_child(sec, "GS시스템 전문 기반 확보 방향")
    idx4_end = find_child_combo(sec, ["KOTITI시험연구원", "본 사업"], start=idx4_start + 1)
    repl4 = []
    repl4 += b.lines([" GS시스템 전문기반 확보 및 특화 전략"])
    repl4 += b.table_as_lines(
        "[표] GS시스템 전문기반 확보 전략",
        ["구분", "전문기반", "본 사업 적용", "확산 가능성"],
        [
            ["현장 계측기술", "전력·LNG·스팀·용수 계측기 선정 및 설치 경험", "설비별·공정별 에너지 사용량 계측", "유사 섬유공정 계측모델로 확산"],
            ["자동제어·통신기술", "PLC·HMI·Gateway 및 산업용 통신 구성 경험", "계측데이터 수집 및 FEMS+ 연계", "타 제조현장 데이터 수집체계에 적용"],
            ["데이터 관리기술", "데이터 항목·단위·수집주기·태그 체계 정리", "EnPI 및 제품단위 탄소배출량 산정 기초자료 제공", "MRV·LCA 연계 데이터 표준화에 활용"],
            ["섬유공정 이해", "텐터기, 보일러, 스팀 계통 등 섬유가공 설비 이해", "공정 특성을 반영한 계측 포인트 선정", "염색·후가공 기업 대상 확산 가능"],
            ["유지보수 역량", "시운전, 장애 대응, 정기점검 수행", "성과활용기간 데이터 수집 안정성 확보", "지역 기반 사후관리 서비스 확장"],
        ],
    )
    repl4 += b.lines([
        "- GS시스템은 본 사업을 통해 섬유 염색·후가공 공정에 적용 가능한 FEMS+ 현장 계측 및 데이터 수집 모델을 확보함.",
        "- 계측기 설치, PLC·HMI·Gateway 연계, 데이터 매핑, 시운전 및 유지보수 절차를 표준화하여 후속 사업에 적용 가능한 구축모델로 정리함.",
        "- 지역 기반 공급기업으로서 구축 이후에도 현장 장애 대응과 정기점검을 수행하여 FEMS+ 운영 안정성 확보에 기여함.",
    ])
    insert_replace(sec, idx4_start, idx4_end, repl4)

    return blue, work1_removed


def replace_text_runs(sec, blue):
    replacements = [
        ("전력, LNG, 스팀, 용수, 압축공기", "전력, LNG, 스팀, 용수"),
        ("전력·LNG·스팀·용수·압축공기", "전력·LNG·스팀·용수"),
        ("스팀, 용수, 압축공기", "스팀, 용수"),
        ("스팀누설, 압축공기 누설", "스팀누설"),
        ("전력, 스팀, LNG, 용수, 압축공기", "전력, 스팀, LNG, 용수"),
        ("에너지전력, 스팀, LNG, 용수, 압축공기", "에너지전력, 스팀, LNG, 용수"),
        ("AI 기반 분석 기능", "이상값 탐지 및 분석 대시보드"),
        ("AI 분석 기능", "이상값 탐지 및 분석 대시보드"),
        ("AI가 자동으로 탐지", "수집데이터 기준으로 이상값, 과다 사용 구간, 비생산 시간대 사용량을 점검"),
        ("가능 시 탄소배출 절감률 10~12% 이상 도전목표 관리", "탄소배출 절감률은 기준기간 에너지 사용량과 구축 후 1개월 이상 실측데이터를 비교하여 산정하며, 최종 절감률은 생산량 보정값과 에너지원별 배출계수를 적용하여 산정함."),
    ]
    count = 0
    for t in sec.xpath(".//hp:t", namespaces=NS):
        if t.text is None:
            continue
        new_text = t.text
        for old, new in replacements:
            if old in new_text:
                new_text = new_text.replace(old, new)
        if new_text != t.text:
            t.text = new_text
            run = t.getparent()
            if run is not None and run.tag == HP + "run":
                run.set("charPrIDRef", blue)
            count += 1
    return count


def remove_or_mark_compressed_air_rows(sec, blue):
    removed = 0
    for tbl in list(sec.xpath(".//hp:tbl", namespaces=NS)):
        for tr in list(tbl.xpath("./hp:tr", namespaces=NS)):
            txt = text_of(tr)
            if "압축공기" in txt:
                tbl.remove(tr)
                removed += 1
    # Remove compressed-air wording from residual free text as well.
    for t in sec.xpath(".//hp:t", namespaces=NS):
        if t.text and "압축공기" in t.text:
            t.text = t.text.replace("압축공기 등", "")
            t.text = t.text.replace("압축공기", "")
            t.text = t.text.replace(",  ", ", ")
            t.text = t.text.replace(" ,", "")
            run = t.getparent()
            if run is not None and run.tag == HP + "run":
                run.set("charPrIDRef", blue)
    return removed


def validate(sec, header, blue):
    texts = child_texts(sec)
    checks = {
        "blue_charpr": blue,
        "red_runs_remaining": 0,
        "compressed_air_remaining": sum("압축공기" in t for t in texts),
        "ai_phrase_remaining": sum("AI 분석 기능" in t or "AI 기반 분석 기능" in t for t in texts),
        "challenge_phrase_remaining": sum("10~12% 이상 도전목표" in t for t in texts),
    }
    red_ids = {
        cp.get("id")
        for cp in header.xpath(".//hh:charPr", namespaces=NS)
        if cp.get("textColor", "").upper() == "#FF0000"
    }
    for run in sec.xpath(".//hp:run", namespaces=NS):
        if run.get("charPrIDRef") in red_ids and text_of(run).strip():
            checks["red_runs_remaining"] += 1
    return checks


def save_hwpx(src, dest, header_xml, section_xml):
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "Contents/header.xml":
                data = header_xml
            elif item.filename == "Contents/section0.xml":
                data = section_xml
            zi = zipfile.ZipInfo(item.filename, item.date_time)
            zi.compress_type = item.compress_type
            zi.external_attr = item.external_attr
            zout.writestr(zi, data)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "edit"
    src = find_input()
    if mode.startswith("out-"):
        src = os.path.join(ROOT, OUTPUT_NAME)
        mode = mode[4:]
    with zipfile.ZipFile(src) as z:
        header = etree.fromstring(z.read("Contents/header.xml"))
        sec = etree.fromstring(z.read("Contents/section0.xml"))

    if mode == "scan":
        print_matches(sec)
        return
    if mode == "around":
        surrounding(sec, [int(x) for x in sys.argv[2:]])
        return
    if mode == "table":
        inspect_child_tables(sec, [int(x) for x in sys.argv[2:]])
        return
    if mode == "red":
        red_contexts(sec, header)
        return
    if mode == "terms":
        term_contexts(sec)
        return

    before_children = len(get_section_children(sec))
    before_header_count = find_header_count(header)
    blue, work1_removed = make_replacements(sec, header)
    text_replace_count = replace_text_runs(sec, blue)
    removed_air_rows = remove_or_mark_compressed_air_rows(sec, blue)

    header_xml = etree.tostring(header, encoding="UTF-8", xml_declaration=True, standalone=None)
    section_xml = etree.tostring(sec, encoding="UTF-8", xml_declaration=True, standalone=None)
    dest = os.path.join(ROOT, OUTPUT_NAME)
    save_hwpx(src, dest, header_xml, section_xml)

    checks = validate(sec, header, blue)
    print("input:", src)
    print("output:", dest)
    print("top-level children:", before_children, "->", len(get_section_children(sec)))
    print("header charPr count:", before_header_count, "->", find_header_count(header))
    print("blue charPr:", blue)
    print("work1 history-cell items removed:", work1_removed)
    print("text replacements:", text_replace_count)
    print("compressed-air table rows removed:", removed_air_rows)
    print("checks:", checks)


if __name__ == "__main__":
    main()
