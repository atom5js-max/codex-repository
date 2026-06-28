"""
result_writer.py
----------------
검색 결과를 Markdown 파일로 저장한다.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from keyword_search import SearchResult
from synonym_expander import ExpandedQuery


_CATEGORY_LABELS: dict[str, str] = {
    "inverter":    "인버터",
    "plc":         "PLC",
    "loadcell":    "로드셀",
    "instruments": "계측기",
    "labview":     "LabVIEW",
    "database":    "데이터베이스",
    "notes":       "현장메모",
    "unknown":     "기타",
}

_RULE_LABELS: dict[str, str] = {
    "speed_command_problem":   "속도지령 문제",
    "loadcell_noise":          "로드셀 노이즈",
    "modbus_comm_problem":     "Modbus 통신 문제",
    "labview_db_slow":         "LabVIEW DB 지연",
    "analog_input_issue":      "아날로그 입력 이상",
    "power_meter_pulse":       "전력량계 펄스",
    "inverter_trip":           "인버터 트립",
    "plc_io_check":            "PLC IO 이상",
    "pressure_sensor_issue":   "압력 센서 이상",
    "temperature_sensor_issue":"온도 센서 이상",
    "inverter_accel_problem":  "인버터 가속 문제",
    "hmi_comm_problem":        "HMI 통신 문제",
    "plc_program_error":       "PLC 프로그램 오류",
    "calibration_general":     "교정/캘리브레이션",
    "flowmeter_issue":         "유량계 이상",
    "inverter_speed_no_change":"인버터 속도 미변경",
    "plc_scan_slow":           "PLC 스캔 느림",
}


def _bold_terms(text: str, terms: list[str]) -> str:
    for term in sorted(terms, key=len, reverse=True):
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        text = pattern.sub(f"**{term}**", text)
    return text


def _format_location(result: SearchResult) -> str:
    chunk = result.chunk
    parts = []
    if chunk.page_number is not None:
        parts.append(f"p.{chunk.page_number}")
    parts.append(f"단락 #{chunk.chunk_index + 1}")
    return " / ".join(parts)


def _format_result_block(result: SearchResult, index: int, highlight: bool = True) -> str:
    doc = result.document
    chunk = result.chunk

    category_label = _CATEGORY_LABELS.get(doc.category, doc.category)
    file_name = doc.file_path.name
    location = _format_location(result)
    match_label = result.match_type_label
    matched_str = ", ".join(f"`{m.term}`" for m in result.matched_terms)

    excerpt = chunk.source_info.get("context_excerpt", chunk.text[:250])
    if highlight:
        excerpt = _bold_terms(excerpt, result.all_matched_term_strings)

    lines = [
        f"### [{index}] {category_label} — `{file_name}`",
        f"",
        f"| 항목 | 내용 |",
        f"|------|------|",
        f"| 제품군 | {category_label} |",
        f"| 파일 | `{file_name}` |",
        f"| 위치 | {location} |",
        f"| 매칭 키워드 | {matched_str} |",
        f"| 매칭 유형 | {match_label} |",
        f"| 점수 | {result.score:.1f} |",
        f"",
        f"**관련 내용:**",
        f"",
        f"> {excerpt.replace(chr(10), chr(10) + '> ')}",
        f"",
        f"---",
        f"",
    ]
    return "\n".join(lines)


def write_results(
    results: list[SearchResult],
    expanded_query: ExpandedQuery,
    output_path: Path,
    include_timestamp: bool = True,
    highlight: bool = True,
    summary: str | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []

    lines.append("# 기술자료 검색 결과")
    lines.append("")

    if include_timestamp:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"**검색 시각**: {ts}")
        lines.append("")

    lines.append("## 검색어 요약")
    lines.append("")
    lines.append(f"**입력 쿼리**: `{expanded_query.original_query}`")
    lines.append("")

    if expanded_query.matched_rules:
        rule_labels = [
            _RULE_LABELS.get(r, r) for r in expanded_query.matched_rules
        ]
        lines.append(f"**발동 규칙**: {', '.join(rule_labels)}")
        lines.append("")
        lines.append(f"**원본 키워드**: {', '.join(f'`{t}`' for t in expanded_query.original_terms)}")
        lines.append("")
        lines.append(f"**확장 키워드**: {', '.join(f'`{t}`' for t in expanded_query.expanded_terms)}")
    else:
        lines.append(f"**키워드**: {', '.join(f'`{t}`' for t in expanded_query.original_terms)}")
        lines.append("")
        lines.append(
            "> 현장어 규칙이 발동되지 않았습니다. "
            "원본 키워드로만 검색합니다. "
            "`rules/synonym_rules.yaml` 에 새 규칙을 추가하면 확장 검색이 활성화됩니다."
        )

    lines.append("")
    lines.append(f"**총 결과 수**: {len(results)}건")
    lines.append("")
    lines.append("---")
    lines.append("")

    if summary:
        lines.append("## AI 요약 (참고용)")
        lines.append("")
        lines.append(
            "> **주의**: 아래 요약은 참고용이며 원인 단정이 아닙니다. "
            "반드시 원문 검색 결과를 직접 확인하십시오."
        )
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## 검색 결과")
    lines.append("")

    if not results:
        lines.append("> 검색 결과가 없습니다.")
        lines.append("> - 검색어를 바꾸거나 synonym_rules.yaml 에 현장 표현을 추가해 보세요.")
        lines.append("> - manuals/ 폴더에 관련 매뉴얼 파일(.md, .txt, .pdf)을 추가하면 검색 범위가 넓어집니다.")
    else:
        for i, result in enumerate(results, start=1):
            lines.append(_format_result_block(result, i, highlight=highlight))

    lines.append("")

    if expanded_query.check_items:
        lines.append("## 현장 확인 항목")
        lines.append("")
        lines.append(
            "> **참고**: 아래 항목은 현장 확인을 위한 체크리스트입니다.  "
        )
        lines.append(
            "> 실제 원인 및 조치는 현장 상황과 매뉴얼을 종합해 판단하십시오."
        )
        lines.append("")
        for item in expanded_query.check_items:
            lines.append(f"- [ ] {item}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("*이 결과는 현장어-매뉴얼어 확장 검색 도구가 자동 생성했습니다.*")
    lines.append("*원인 단정 및 최종 조치는 반드시 담당 엔지니어가 확인하십시오.*")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[결과 저장] {output_path}")
