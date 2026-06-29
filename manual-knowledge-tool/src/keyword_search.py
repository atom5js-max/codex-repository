"""
keyword_search.py
-----------------
BaseSearcher 를 구현한 키워드 검색 백엔드.

점수 체계:
  - 원본 검색어 1회 매칭 = 1.0점
  - 확장 검색어 1회 매칭 = 0.7점 (search_rules.yaml 의 expanded_match_weight)
  - 동일 청크 내 여러 검색어 매칭 시 합산
  - 헤더 포함 청크에 가중치 적용

단어 경계 처리:
  - 길이 ≤ whole_word_threshold 인 짧은 용어는 \b 경계 매칭 사용
  - 예: "DB" 검색 시 "Modbus", "DBU" 는 제외되고 "DB Insert", "DB 연결" 만 매칭

Stage B 전환 방법:
  - VectorSearcher(BaseSearcher) 를 구현한 뒤
  - main.py 의 --backend 플래그로 교체
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from base_searcher import BaseSearcher
from document_loader import Document
from synonym_expander import ExpandedQuery
from text_chunker import Chunk

_HEADER_RE = re.compile(r"^#{1,3}\s+", re.MULTILINE)
_HEADER_WEIGHT = 1.5

_WHOLE_WORD_THRESHOLD = 4

_MAX_TERM_COUNT = 3

_KO_STOPWORDS = frozenset({
    "이상",
    "안됨",
    "먹음",
    "느림",
    "틀림",
    "있음",
    "없음",
    "저장",
})


@dataclass
class MatchedTerm:
    term: str
    match_type: str
    count: int


@dataclass
class SearchResult:
    document: Document
    chunk: Chunk
    matched_terms: list[MatchedTerm]
    score: float

    @property
    def match_type_label(self) -> str:
        has_original = any(m.match_type == "original" for m in self.matched_terms)
        has_expanded = any(m.match_type == "expanded" for m in self.matched_terms)
        if has_original and has_expanded:
            return "원본+확장"
        if has_original:
            return "원본"
        return "확장"

    @property
    def all_matched_term_strings(self) -> list[str]:
        return [m.term for m in self.matched_terms]


def _count_occurrences(text: str, term: str, whole_word: bool = False) -> int:
    if whole_word:
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        return len(pattern.findall(text))
    return text.lower().count(term.lower())


def _should_use_whole_word(term: str) -> bool:
    return len(term) <= _WHOLE_WORD_THRESHOLD and re.match(r"^[A-Za-z0-9]+$", term) is not None


def _has_header(text: str) -> bool:
    return bool(_HEADER_RE.search(text))


def _filename_bonus(file_path, original_terms: list[str]) -> float:
    stem = file_path.stem.lower()
    bonus = 0.0
    for term in original_terms:
        if len(term) < 2:
            continue
        if term.lower() in _KO_STOPWORDS:
            continue
        if len(term) >= 3 and term.lower() in stem:
            bonus += 3.0
    return bonus


def _extract_context(text: str, term: str, context_chars: int = 120) -> str:
    idx = text.lower().find(term.lower())
    if idx == -1:
        return text[: context_chars * 2].strip()

    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(term) + context_chars)
    excerpt = text[start:end].strip()

    if start > 0:
        excerpt = "..." + excerpt
    if end < len(text):
        excerpt = excerpt + "..."
    return excerpt


class KeywordSearcher(BaseSearcher):
    """형태소 분석 없는 단순 문자열 키워드 검색."""

    @property
    def name(self) -> str:
        return "keyword"

    def search(
        self,
        documents: list[Document],
        expanded_query: ExpandedQuery,
        max_results: int = 20,
        max_per_file: int = 5,
        context_chars: int = 120,
        expanded_weight: float = 0.7,
        **kwargs,
    ) -> list[SearchResult]:
        return search_documents(
            documents=documents,
            expanded_query=expanded_query,
            max_results=max_results,
            max_per_file=max_per_file,
            context_chars=context_chars,
            expanded_weight=expanded_weight,
        )


def search_documents(
    documents: list[Document],
    expanded_query: ExpandedQuery,
    max_results: int = 20,
    max_per_file: int = 5,
    context_chars: int = 120,
    expanded_weight: float = 0.7,
) -> list[SearchResult]:
    results: list[SearchResult] = []

    for doc in documents:
        for chunk in doc.chunks:
            if not chunk.text.strip():
                continue

            matched_terms: list[MatchedTerm] = []
            score = 0.0

            for term in expanded_query.original_terms:
                if len(term) < 2:
                    continue
                if term.lower() in _KO_STOPWORDS:
                    continue
                whole = _should_use_whole_word(term)
                cnt = min(_count_occurrences(chunk.text, term, whole_word=whole), _MAX_TERM_COUNT)
                if cnt > 0:
                    matched_terms.append(
                        MatchedTerm(term=term, match_type="original", count=cnt)
                    )
                    score += cnt * 1.0

            for term in expanded_query.expanded_terms:
                if len(term) < 2:
                    continue
                whole = _should_use_whole_word(term)
                cnt = min(_count_occurrences(chunk.text, term, whole_word=whole), _MAX_TERM_COUNT)
                if cnt > 0:
                    matched_terms.append(
                        MatchedTerm(term=term, match_type="expanded", count=cnt)
                    )
                    score += cnt * expanded_weight

            if not matched_terms:
                continue

            if _has_header(chunk.text):
                score *= _HEADER_WEIGHT

            score += _filename_bonus(doc.file_path, expanded_query.original_terms)

            first_term = matched_terms[0].term
            chunk.source_info["context_excerpt"] = _extract_context(
                chunk.text, first_term, context_chars
            )

            results.append(
                SearchResult(
                    document=doc,
                    chunk=chunk,
                    matched_terms=matched_terms,
                    score=score,
                )
            )

    results.sort(key=lambda r: r.score, reverse=True)

    limited_results: list[SearchResult] = []
    file_counts: dict[str, int] = {}
    for result in results:
        file_key = str(result.document.file_path)
        if file_counts.get(file_key, 0) >= max_per_file:
            continue
        file_counts[file_key] = file_counts.get(file_key, 0) + 1
        limited_results.append(result)
        if len(limited_results) >= max_results:
            break

    return limited_results
