"""
synonym_expander.py
-------------------
synonym_rules.yaml 을 읽어 현장어 검색어를 매뉴얼어로 확장한다.

매칭 방식:
  - 현장 입력 쿼리 안에 field_terms 중 하나라도 포함되면 해당 규칙 발동
  - 긴 field_term 을 먼저 매칭해 과도한 확장을 방지
  - 여러 규칙이 동시에 발동될 수 있다
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ExpandedQuery:
    """확장된 검색 정보를 담는다."""
    original_query: str
    original_terms: list[str]
    expanded_terms: list[str]
    check_items: list[str]
    matched_rules: list[str]

    @property
    def all_terms(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for t in self.original_terms + self.expanded_terms:
            t_lower = t.lower()
            if t_lower not in seen:
                seen.add(t_lower)
                result.append(t)
        return result


def _load_rules(rules_path: Path) -> dict:
    if not rules_path.exists():
        logger.warning("synonym_rules.yaml 없음: %s", rules_path)
        return {}
    with rules_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def _tokenize(query: str) -> list[str]:
    tokens = [t.strip() for t in re.split(r"[\s,;/|]+", query) if t.strip()]
    return tokens


def _match_field_terms(query: str, field_terms: list[str]) -> list[str]:
    query_lower = query.lower()
    matched: list[str] = []
    for term in sorted(field_terms, key=len, reverse=True):
        if term.lower() in query_lower:
            matched.append(term)
    return matched


def expand_query(query: str, rules_path: Path) -> ExpandedQuery:
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
