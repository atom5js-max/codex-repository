"""
result_writer.py
----------------
검색 결과를 Markdown 파일로 저장한다.

출력 형식:
  - 검색어 요약 (원본 / 발동 규칙 / 확장 키워드)
  - 결과 목록 (제품군, 파일명, 위치, 매칭 키워드, 주변 문장)
  - 현장 확인 항목 (단정적 지시 없이 확인 목록 형태)
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from keyword_search import SearchResult
from synonym_expander import ExpandedQuery


# 카테고리 한글 표시명
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

# 규칙 이름 한글 표시명
_RULE_LABELS: dict[str, str] = {
    "speed_command_problem": "속도지령 문제",
    "loadcell_noise":        "로드셀 노이즈",
    "modbus_comm_problem":   "Modbus 통신 문제",
    "labview_db_slow":       "LabVIEW DB 지연",
    "analog_input_issue":    "아날로그 입력 이상",
    "power_meter_pulse":     "전력량계 펄스",
    "inverter_trip":         "인버터 트립",
    "plc_io_check":          "PLC IO 이상",
}


def _bold_terms(text: str, terms: list[str]) -> str:
    """텍스트에서 매칭 단어를 **굵게** 강조한다."""
    for term in sorted(terms, key=len, reverse=True):
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        text = pattern.sub(f"**{term}**", text)
    return text


def _format_location(result: SearchResult) -> str:
    """청크 위치 정보를 문자열로 반환한다."""
    chunk = result.chunk
    parts = []
    if chunk.page_number is not None:
        parts.append(f"p.{chunk.page_number}")
    parts.append(f"단락 #{chunk.chunk_index + 1}")
    return " / ".join(parts)


def _format_result_block(result: SearchResult, index: int, highlight: bool = True) -> str:
    """단일 검색 결과를 Markdown 블록으로 포맷한다."""
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

    # 코드블록/테이블이 포함된 경우 pre 블록으로 감싸지 않고 그대로 유지
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
) -> None:
    """
    검색 결과를 Markdown 파일로 저장한다.

    Parameters
    ----------
    results        : keyword_search 가 반환한 결과 목록
    expanded_query : 확장 쿼리 정보 (원본·확장어·체크항목)
    output_path    : 저장할 파일 경로
    include_timestamp : 타임스탬프 포함 여부
    highlight      : 매칭 단어 강조 여부
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []

    # ── 헤더 ──────────────────────────────────────────────
    lines.append("# 기술자료 검색 결과")
    lines.append("")

    if include_timestamp:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"**검색 시각**: {ts}")
        lines.append("")

    # ── 검색어 요약 ────────────────────────────────────────
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

    # ── 검색 결과 목록 ─────────────────────────────────────
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

    # ── 현장 확인 항목 ─────────────────────────────────────
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

    # ── 푸터 ──────────────────────────────────────────────
    lines.append("*이 결과는 현장어-매뉴얼어 확장 검색 도구가 자동 생성했습니다.*")
    lines.append("*원인 단정 및 최종 조치는 반드시 담당 엔지니어가 확인하십시오.*")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[결과 저장] {output_path}")
