from __future__ import annotations

import html
import re
import sys
import zipfile
from pathlib import Path


BLUE_CHAR = "175"


def paragraph_spans(xml: str) -> dict[int, tuple[int, int]]:
    token_re = re.compile(r"<hp:p\b[^>]*>|</hp:p>")
    stack: list[tuple[int, int]] = []
    spans: dict[int, tuple[int, int]] = {}
    idx = 0
    for match in token_re.finditer(xml):
        token = match.group(0)
        if token.startswith("<hp:p"):
            idx += 1
            stack.append((idx, match.start()))
        else:
            if not stack:
                raise RuntimeError("unbalanced hp:p")
            p_idx, start = stack.pop()
            spans[p_idx] = (start, match.end())
    if stack:
        raise RuntimeError("unclosed hp:p")
    return spans


def set_text_in_para(fragment: str, text: str, blue: bool = True) -> str:
    escaped = html.escape(text, quote=False)
    if blue and text:
        fragment = re.sub(r'(<hp:run\b[^>]*\bcharPrIDRef=")[^"]+(")', rf"\g<1>{BLUE_CHAR}\2", fragment)

    changed = False

    def repl_full(match: re.Match[str]) -> str:
        nonlocal changed
        if changed:
            return f"{match.group(1)}{match.group(3)}"
        changed = True
        return f"{match.group(1)}{escaped}{match.group(3)}"

    fragment = re.sub(r"(<hp:t\b[^>]*>)(.*?)(</hp:t>)", repl_full, fragment, count=0, flags=re.S)
    if changed:
        return fragment

    def repl_empty(match: re.Match[str]) -> str:
        nonlocal changed
        if changed:
            return match.group(0)
        changed = True
        return f"{match.group(1)}>{escaped}</hp:t>"

    fragment = re.sub(r"(<hp:t\b[^/>]*)/>", repl_empty, fragment, count=1)
    return fragment


def patch_paragraphs(xml: str, patches: dict[int, str]) -> str:
    spans = paragraph_spans(xml)
    edits: list[tuple[int, int, str]] = []
    for idx, text in patches.items():
        if idx not in spans:
            continue
        start, end = spans[idx]
        old = xml[start:end]
        edits.append((start, end, set_text_in_para(old, text, blue=bool(text))))
    for start, end, new in sorted(edits, reverse=True):
        xml = xml[:start] + new + xml[end:]
    return xml


def replace_text_everywhere(xml: str, replacements: dict[str, str]) -> str:
    for old, new in replacements.items():
        xml = xml.replace(html.escape(old, quote=False), html.escape(new, quote=False))
        xml = xml.replace(old, new)
    return xml


def build_patches() -> dict[int, str]:
    patches: dict[int, str] = {
        # 제1장 역할분담 표: GS시스템 장문 축소
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
        # 수행기관 일반현황
        356: "- 본 사업에서는 계측 인프라 구축, PLC·HMI·통신 연계, 데이터 수집·점검 및 시운전·유지보수를 수행함.",
        357: "",
        358: "",
        359: "",
        360: "",
        361: "",
        362: "",
        # 기술역량
        496: "2) 참여-공급기관",
        497: "",
        498: " GS시스템 기술역량은 본 사업 수행범위에 맞춰 다음 6개 항목으로 요약함.",
        499: "",
        500: "",
        501: "",
        521: "",
        522: "",
        523: "",
        524: "",
        525: "",
        526: "",
        527: "",
        528: "",
        530: "",
        531: "",
        532: "",
        533: "",
        534: "",
        535: "",
        536: "",
        556: "",
        557: "",
        558: "",
        559: "",
        560: "",
        561: "",
        563: "",
        564: "",
        565: "",
        566: "",
        567: "",
        568: "",
        569: "",
        570: "",
        571: "",
        572: "",
        573: "",
        575: "",
        576: "",
        577: "",
        578: "",
        579: "",
        580: "",
        581: "",
        582: "",
        583: "",
        599: "",
        600: "",
        602: "",
        603: "",
        604: "",
        605: "",
        606: "",
        607: "",
        608: "",
        609: "",
        610: "",
        611: "",
        613: "",
        614: "",
        615: "",
        616: "",
        617: "",
        618: "",
        619: "",
        620: "",
        622: " GS시스템 기술역량 요약표",
        627: "1",
        628: "계측 인프라 구축",
        629: "전력·LNG·스팀·용수 계측 포인트 검토, 계측기 설치, 배선·결선 점검",
        630: "2",
        631: "PLC·HMI·통신 연계",
        632: "PLC·HMI·Gateway, RS-485/Modbus/Ethernet 통신 연계 구축",
        633: "3",
        634: "데이터 수집·DB 구성",
        635: "현장 계측 Raw Data 수집, DB 저장구조 및 이상값 탐지·분석 대시보드 구축",
        636: "4",
        637: "FEMS+·MRV 연계",
        638: "FEMS+ 활용 항목과 MRV 연계용 데이터 매핑·전송자료 관리",
        639: "5",
        640: "섬유공정 특화",
        641: "텐터·보일러·스팀·용수 등 섬유가공 설비 특성을 반영한 계측 위치 선정",
        642: "6",
        643: "시운전·유지보수",
        644: "계측기·통신·수집상태 점검, 운영교육, 장애 대응 및 정기점검 관리",
    }

    for idx in range(645, 663):
        patches[idx] = ""

    # 참여기관 1 목표 및 내용: 순서 재작성
    patches.update(
        {
            1889: "① 추진목표",
            1890: "- 계측 인프라와 PLC·HMI·통신 연계를 구축하여 수요기업의 전력·LNG·스팀·용수 데이터를 수집함.",
            1891: "- 수집데이터를 DB, FEMS+ 대시보드, MRV 연계 기초자료로 관리함.",
            1892: "- 시운전, 운영교육, 장애 대응 및 정기점검으로 성과활용기간 운영 안정성을 확보함.",
            1903: "",
            1904: "",
            1905: "",
            1907: "",
            1908: "② 수행내용",
            1956: "1",
            1957: "계측 인프라 구축",
            1958: "현장 에너지원별 계측지점 도출",
            1959: "계측기 선정·설치·배선·결선 수행",
            1960: "현장조사표, 계측 포인트 검토표, 설치확인표",
            1961: "2",
            1962: "PLC·HMI·통신 연계",
            1963: "계측기와 제어·통신장비 연결",
            1964: "PLC·HMI·Gateway 통신 설정 및 점검",
            1965: "통신 구성도, 주소표, 태그 리스트",
            1966: "3",
            1967: "데이터 수집·DB 구성",
            1968: "Raw/Processed Data 수집 구조 구성",
            1969: "DB 항목, 단위, 수집주기, 이상값 탐지 기준 관리",
            1970: "수집항목표, DB 항목표, 점검표",
            1971: "4",
            1972: "FEMS+·MRV 연계",
            1973: "FEMS+ 대시보드 및 MRV 기초자료 연계",
            1974: "데이터 매핑, 전송자료, 정상 수집 샘플 정리",
            1975: "데이터 매핑표, MRV 연계 기초자료",
            1976: "5",
            1977: "섬유공정 특화",
            1978: "텐터·보일러·스팀·용수 설비 반영",
            1979: "공정별 계측 위치와 설비코드 정리",
            1980: "계측 위치도, 설비코드표",
            1981: "6",
            1982: "시운전·유지보수",
            1983: "구축 후 운영 안정화",
            1984: "계측·통신·수집상태 점검, 교육, 장애 대응",
            1985: "시운전 결과서, 교육자료, 점검보고서",
            2012: "③ 주요 산출물",
            2013: "- 현장조사표, 계측 포인트 검토표, 계측기 목록 및 설치확인표",
            2014: "- 통신 구성도, 통신주소표, 태그 리스트",
            2015: "- 수집항목 정의서, DB 항목표, 데이터 매핑표",
            2016: "- FEMS+·MRV 연계 기초자료 및 정상 수집 데이터 샘플",
            2017: "- 시운전 결과서, 운영교육자료, 유지보수 점검보고서",
            2032: "",
            2033: "",
        }
    )
    for idx in list(range(1893, 1902)) + list(range(1909, 1950)) + list(range(1986, 2011)) + list(range(2018, 2031)) + list(range(2034, 2042)):
        patches[idx] = ""

    # 경쟁력 확보 전략: 표 형식 텍스트로 축소
    patches.update(
        {
            2104: " GS시스템 경쟁력 확보 전략",
            2105: "구분 | 전문기반 확보 | 본 사업 적용 | 확산 가능성",
            2106: "계측·제어 기반 | 산업자동화, PLC·HMI, 현장통신 구축 경험 | 계측기·제어반·Gateway 연계 구축 | 유사 제조현장 FEMS+ 구축모델 적용",
            2107: "데이터 관리 기반 | Raw/Processed Data, DB, 이상값 탐지 체계 | FEMS+ 대시보드와 MRV 연계 기초자료 관리 | 탄소관리·MRV 대응 서비스 확장",
            2108: "섬유공정 특화 | 텐터·보일러·스팀·용수 설비 이해 | 벽진BIO텍 공정별 계측 포인트와 수집체계 구축 | 섬유 염색·후가공 기업 확산",
        }
    )
    for idx in range(2110, 2169):
        patches[idx] = ""

    return patches


def write_zip_like(src: Path, dst: Path, section_xml: str) -> None:
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(dst, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "Contents/section0.xml":
                data = section_xml.encode("utf-8")
            out_info = zipfile.ZipInfo(info.filename, info.date_time)
            out_info.compress_type = info.compress_type
            out_info.external_attr = info.external_attr
            zout.writestr(out_info, data)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: revise_gs_hwpx_raw.py <input.hwpx> <output.hwpx>")
        return 2
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    with zipfile.ZipFile(src) as zf:
        section = zf.read("Contents/section0.xml").decode("utf-8")

    section = patch_paragraphs(section, build_patches())
    section = replace_text_everywhere(
        section,
        {
            "전력, LNG, 스팀, 용수, 압축공기 등": "전력, LNG, 스팀, 용수 등",
            "전력, LNG, 스팀, 용수, 압축공기": "전력, LNG, 스팀, 용수",
            "스팀, 용수, 압축공기 등": "스팀, 용수 등",
            "압축공기 계통": "",
            "압축공기": "",
            "AI 기반 분석": "이상값 탐지 및 분석 대시보드",
        },
    )
    section = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", section, flags=re.S)
    write_zip_like(src, dst, section)
    print(f"wrote={dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
