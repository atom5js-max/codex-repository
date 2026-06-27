"""
synonym_expander.py
-------------------
synonym_rules.yaml 을 읽어 현장어 검색어를 매뉴얼어로 확장한다.

매칭 방식:
  - 현장 입력 쿼리 안에 field_terms 중 하나라도 포함되면 해당 규칙 발동
  - 긴 field_term 을 먼저 매칭해 과도한 확장을 방지
  - 여러 규칙이 동시에 발동될 수 있다 (예: "Modbus 통신 안 됨 속도 안 먹음")
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml  # PyYAML

logger = logging.getLogger(__name__)


@dataclass
class ExpandedQuery:
    """확장된 검색 정보를 담는다."""
    original_query: str
    original_terms: list[str]      # 공백/특수문자로 분리한 원본 토큰
    expanded_terms: list[str]      # 매뉴얼어 확장 검색어
    check_items: list[str]         # 현장 확인 항목
    matched_rules: list[str]       # 발동된 규칙 이름 목록

    @property
    def all_terms(self) -> list[str]:
        """원본 + 확장 검색어 합친 중복 없는 목록"""
        seen: set[str] = set()
        result: list[str] = []
        for t in self.original_terms + self.expanded_terms:
            t_lower = t.lower()
            if t_lower not in seen:
                seen.add(t_lower)
                result.append(t)
        return result


def _load_rules(rules_path: Path) -> dict:
    """synonym_rules.yaml 을 로드한다."""
    if not rules_path.exists():
        logger.warning("synonym_rules.yaml 없음: %s", rules_path)
        return {}
    with rules_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def _tokenize(query: str) -> list[str]:
    """
    검색어를 개별 토큰으로 분리한다.
    공백/구두점으로 분리하되 의미 있는 한글·영문·숫자 조합은 보존한다.
    """
    # 공백으로 기본 분리 후 빈 항목 제거
    tokens = [t.strip() for t in re.split(r"[\s,;/|]+", query) if t.strip()]
    return tokens


def _match_field_terms(
    query: str,
    field_terms: list[str],
) -> list[str]:
    """
    쿼리에서 발동된 field_term 목록을 반환한다.
    긴 term 을 먼저 확인해 하위어 오매칭을 줄인다.
    """
    query_lower = query.lower()
    matched: list[str] = []

    # 긴 것 먼저 정렬
    for term in sorted(field_terms, key=len, reverse=True):
        if term.lower() in query_lower:
            matched.append(term)

    return matched


def expand_query(
    query: str,
    rules_path: Path,
) -> ExpandedQuery:
    """
    사용자 입력 쿼리를 받아 확장된 검색 정보를 반환한다.

    Parameters
    ----------
    query      : 사용자가 입력한 검색어 (예: "S300 속도지령 안 먹음")
    rules_path : synonym_rules.yaml 파일 경로
    """
    rules = _load_rules(rules_path)
    original_terms = _tokenize(query)

    expanded_terms: list[str] = []
    check_items: list[str] = []
    matched_rules: list[str] = []

    for rule_name, rule_data in rules.items():
        if not isinstance(rule_data, dict):
            continue

        field_terms: list[str] = rule_data.get("field_terms", [])
        manual_terms: list[str] = rule_data.get("manual_terms", [])
        rule_checks: list[str] = rule_data.get("check_items", [])

        fired = _match_field_terms(query, field_terms)
        if fired:
            logger.debug("규칙 발동: %s (매칭: %s)", rule_name, fired)
            matched_rules.append(rule_name)
            expanded_terms.extend(manual_terms)
            check_items.extend(rule_checks)

    # 중복 제거 (순서 유지)
    seen: set[str] = set()
    unique_expanded: list[str] = []
    for t in expanded_terms:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique_expanded.append(t)

    seen_checks: set[str] = set()
    unique_checks: list[str] = []
    for c in check_items:
        if c not in seen_checks:
            seen_checks.add(c)
            unique_checks.append(c)

    return ExpandedQuery(
        original_query=query,
        original_terms=original_terms,
        expanded_terms=unique_expanded,
        check_items=unique_checks,
        matched_rules=matched_rules,
    )
