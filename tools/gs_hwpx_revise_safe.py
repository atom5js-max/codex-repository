from __future__ import annotations

import html
import re
import struct
import zipfile
from pathlib import Path

from gs_hwpx_revise import REPLACEMENTS, DELETE_INDICES, SUMMARY_NAME


WORKSPACE = Path(__file__).resolve().parents[1]
OUTPUT_NAME = "(벽진바이오텍)_FEMS플러스_사업계획서_GS시스템_중복정리본.hwpx"
SOURCE_MARKER = "v3.1"
BLUE_CHARPR_ID = "175"


P_START_RE = re.compile(r"<hp:p(?=[\s>])")
P_END = "</hp:p>"
RUN_RE = re.compile(r"<hp:run\b(?P<attrs>[^>]*)>(?P<body>.*?)</hp:run>", re.DOTALL)
T_RE = re.compile(r"<hp:t(?P<attrs>[^>]*)>.*?</hp:t>|<hp:t(?P<attrs_empty>[^>]*)/>", re.DOTALL)
CHARPR_RE = re.compile(r'charPrIDRef="[^"]*"')
LINESEGARRAY_RE = re.compile(r"<hp:linesegarray>.*?</hp:linesegarray>", re.DOTALL)


def find_paragraph_spans(xml: str) -> dict[int, tuple[int, int]]:
    spans: dict[int, tuple[int, int]] = {}
    stack: list[tuple[int, int]] = []
    idx = 0
    pos = 0
    while True:
        start_match = P_START_RE.search(xml, pos)
        end_pos = xml.find(P_END, pos)
        if start_match is None and end_pos == -1:
            break
        if start_match is not None and (end_pos == -1 or start_match.start() < end_pos):
            stack.append((idx, start_match.start()))
            idx += 1
            pos = start_match.end()
        else:
            if not stack:
                raise RuntimeError("Unbalanced hp:p end tag")
            p_idx, start = stack.pop()
            end = end_pos + len(P_END)
            spans[p_idx] = (start, end)
            pos = end
    if stack:
        raise RuntimeError("Unbalanced hp:p start tag")
    return spans


def set_run_blue(run_open_attrs: str) -> str:
    if CHARPR_RE.search(run_open_attrs):
        return CHARPR_RE.sub(f'charPrIDRef="{BLUE_CHARPR_ID}"', run_open_attrs, count=1)
    return run_open_attrs + f' charPrIDRef="{BLUE_CHARPR_ID}"'


def replace_first_text_run(block: str, text: str) -> str:
    replacement_text = html.escape(text, quote=False)

    def run_repl(match: re.Match[str]) -> str:
        attrs = set_run_blue(match.group("attrs"))
        body = match.group("body")

        def t_repl(t_match: re.Match[str]) -> str:
            attrs_t = t_match.group("attrs")
            if attrs_t is None:
                attrs_t = t_match.group("attrs_empty") or ""
            return f"<hp:t{attrs_t}>{replacement_text}</hp:t>"

        new_body, count = T_RE.subn(t_repl, body, count=1)
        if count == 0:
            return match.group(0)
        return f"<hp:run{attrs}>{new_body}</hp:run>"

    replaced = RUN_RE.sub(run_repl, block, count=1)
    return LINESEGARRAY_RE.sub("", replaced)


def blank_first_text_run(block: str) -> str:
    return replace_first_text_run(block, "")


def patch_section_xml(section_xml: str) -> tuple[str, int, int]:
    spans = find_paragraph_spans(section_xml)
    patches: list[tuple[int, int, str]] = []

    for idx, text in REPLACEMENTS.items():
        if idx not in spans:
            raise RuntimeError(f"Paragraph index not found: {idx}")
        start, end = spans[idx]
        patches.append((start, end, replace_first_text_run(section_xml[start:end], text)))

    for idx in DELETE_INDICES:
        if idx not in spans:
            raise RuntimeError(f"Paragraph index not found: {idx}")
        start, end = spans[idx]
        patches.append((start, end, blank_first_text_run(section_xml[start:end])))

    patched = section_xml
    for start, end, new_block in sorted(patches, reverse=True):
        patched = patched[:start] + new_block + patched[end:]

    return patched, len(REPLACEMENTS), len(DELETE_INDICES)


def patch_zip_flags(zip_path: Path, flag_map: dict[str, int]) -> None:
    data = bytearray(zip_path.read_bytes())
    pos = 0
    while pos + 30 <= len(data):
        sig = data[pos : pos + 4]
        if sig == b"PK\x03\x04":
            name_len = struct.unpack_from("<H", data, pos + 26)[0]
            extra_len = struct.unpack_from("<H", data, pos + 28)[0]
            comp_size = struct.unpack_from("<I", data, pos + 18)[0]
            name = data[pos + 30 : pos + 30 + name_len].decode("utf-8")
            if name in flag_map:
                struct.pack_into("<H", data, pos + 6, flag_map[name])
            pos = pos + 30 + name_len + extra_len + comp_size
            continue
        if sig in (b"PK\x01\x02", b"PK\x05\x06"):
            break
        pos += 1

    pos = data.find(b"PK\x01\x02")
    while pos != -1 and pos + 46 <= len(data) and data[pos : pos + 4] == b"PK\x01\x02":
        name_len = struct.unpack_from("<H", data, pos + 28)[0]
        extra_len = struct.unpack_from("<H", data, pos + 30)[0]
        comment_len = struct.unpack_from("<H", data, pos + 32)[0]
        name = data[pos + 46 : pos + 46 + name_len].decode("utf-8")
        if name in flag_map:
            struct.pack_into("<H", data, pos + 8, flag_map[name])
        pos = pos + 46 + name_len + extra_len + comment_len

    zip_path.write_bytes(data)


def main() -> None:
    source = next(path for path in WORKSPACE.glob("*.hwpx") if SOURCE_MARKER in path.name)
    output = WORKSPACE / OUTPUT_NAME

    with zipfile.ZipFile(source, "r") as zin:
        infos = zin.infolist()
        payloads = {info.filename: zin.read(info.filename) for info in infos}
        flag_map = {info.filename: info.flag_bits for info in infos}

    original_section = payloads["Contents/section0.xml"].decode("utf-8")
    patched_section, changed, blanked = patch_section_xml(original_section)
    payloads["Contents/section0.xml"] = patched_section.encode("utf-8")

    with zipfile.ZipFile(output, "w") as zout:
        for info in infos:
            new_info = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            new_info.comment = info.comment
            new_info.extra = info.extra
            new_info.internal_attr = info.internal_attr
            new_info.external_attr = info.external_attr
            new_info.create_system = info.create_system
            new_info.create_version = info.create_version
            new_info.extract_version = info.extract_version
            new_info.flag_bits = info.flag_bits
            new_info.volume = info.volume
            new_info.compress_type = info.compress_type
            zout.writestr(new_info, payloads[info.filename])

    patch_zip_flags(output, flag_map)

    summary = f"""수정본: {output.name}
원본: {source.name}

재생성 방식
- 원본 ZIP 엔트리 순서, 압축 방식, header.xml을 그대로 유지함
- Contents/section0.xml의 대상 문단 텍스트와 charPrIDRef만 최소 수정함
- 수정 텍스트는 문서 내 기존 파란색 글자속성 charPrIDRef={BLUE_CHARPR_ID}를 사용함

수정 결과
- 파란색 표시 적용 문단/셀: {changed}개
- 중복 축약을 위해 빈 문단으로 처리한 본문 문단: {blanked}개

수정한 목차 목록
- 제1장 제1절 추진체계 및 역할분담
- 제1장 제2절 컨소시엄 세부 역량
- 제2장 제1절 세부사업 기획 및 설계
- 제2장 제2절 추진일정
- 제2장 제3절 세부 추진계획 및 방법
- 제6장 기대효과 및 성과활용

중복 제거한 주요 표현
- 전력, LNG, 스팀, 용수 계측 반복 나열
- 계측기 설치, 배선·결선, 통신 설정 반복 설명
- PLC, HMI, Edge Gateway, 데이터 수집장치 연계 반복 설명
- RS-485, Modbus RTU/TCP, Ethernet 및 외부 연계 프로토콜 반복 나열
- FEMS+ 및 산업단지 MRV 플랫폼 연계 반복 문장
- 데이터 항목·단위·수집주기·태그 체계 반복 문장
- 시운전, 운영자 교육, 장애 대응, 정기점검, 유지보수 반복 문장

유지한 핵심 기술 키워드
- 전력, LNG, 스팀, 용수 계측
- 설비별·공정별 에너지 사용량
- 계측 포인트 선정
- PLC·HMI·Edge Gateway 연계
- RS-485, Modbus RTU/TCP, Ethernet
- Raw Data / Processed Data
- FEMS+ 대시보드
- 산업단지 MRV 플랫폼 연계
- 데이터 항목·단위·수집주기·태그 체계
- EnPI
- 제품 단위 탄소배출량 산정
- 시운전
- 운영자 교육
- 정기점검 및 유지보수

추가 검토가 필요한 부분
- 벽진 작성 요청, 벽진 확인 필요, 작성 예정 표시는 GS시스템 영역 외 문구이므로 유지
- 일부 표의 세부 수량·금액·참여율은 원자료 확인 필요
"""
    (WORKSPACE / SUMMARY_NAME).write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
