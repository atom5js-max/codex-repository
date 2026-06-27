"""
keyword_search.py
-----------------
원본 + 확장 검색어를 이용해 Document 청크를 검색한다.

점수 체계:
  - 원본 검색어 1회 매칭 = 1.0점
  - 확장 검색어 1회 매칭 = 0.7점 (search_rules.yaml 의 expanded_match_weight)
  - 동일 청크 내 여러 검색어 매칭 시 합산
  - 제목/헤더 포함 청크에 가중치 적용

반환되는 SearchResult 마다 match_type 이 'original' 또는 'expanded' 로 표시된다.
두 종류가 모두 매칭된 경우 'both' 로 표시한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from document_loader import Document
from synonym_expander import ExpandedQuery
from text_chunker import Chunk


# 헤더 패턴 (마크다운 h1~h3)
_HEADER_RE = re.compile(r"^#{1,3}\s+", re.MULTILINE)
_HEADER_WEIGHT = 1.5   # 헤더를 포함한 청크는 점수를 높게 준다


@dataclass
class MatchedTerm:
    """하나의 매칭 결과"""
    term: str
    match_type: str   # 'original' | 'expanded'
    count: int        # 청크 내 매칭 횟수


@dataclass
class SearchResult:
    """단일 검색 결과 레코드"""
    document: Document
    chunk: Chunk
    matched_terms: list[MatchedTerm]
    score: float

    @property
    def match_type_label(self) -> str:
        """원본/확장/복합 매칭 종류를 사람이 읽기 쉬운 문자열로 반환한다."""
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


def _count_occurrences(text: str, term: str, case_sensitive: bool = False) -> int:
    """텍스트 안에서 term 이 등장하는 횟수를 반환한다."""
    if not case_sensitive:
        return text.lower().count(term.lower())
    return text.count(term)


def _has_header(text: str) -> bool:
    return bool(_HEADER_RE.search(text))


def _extract_context(text: str, term: str, context_chars: int = 120) -> str:
    """
    term 이 처음 등장하는 위치 기준으로 앞뒤 context_chars 글자를 반환한다.
    """
    idx = text.lower().find(term.lower())
    if idx == -1:
        return text[:context_chars * 2].strip()

    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(term) + context_chars)
    excerpt = text[start:end].strip()

    # 앞이 잘린 경우 "..." 붙이기
    if start > 0:
        excerpt = "..." + excerpt
    if end < len(text):
        excerpt = excerpt + "..."

    return excerpt


def search_documents(
    documents: list[Document],
    expanded_query: ExpandedQuery,
    max_results: int = 20,
    max_per_file: int = 5,
    context_chars: int = 120,
    expanded_weight: float = 0.7,
) -> list[SearchResult]:
    """
    모든 Document 의 청크를 검색해 점수 내림차순으로 정렬된 결과를 반환한다.

    Parameters
    ----------
    documents       : 로드된 Document 목록
    expanded_query  : synonym_expander 가 생성한 확장 쿼리
    max_results     : 최대 반환 결과 수
    max_per_file    : 파일당 최대 반환 결과 수
    context_chars   : 매칭 위치 주변 표시 글자 수
    expanded_weight : 확장 검색어 매칭 가중치 (원본 = 1.0 기준)
    """
    results: list[SearchResult] = []

    # 파일당 결과 수 카운터
    file_counts: dict[str, int] = {}

    for doc in documents:
        file_key = str(doc.file_path)
        file_counts.setdefault(file_key, 0)

        for chunk in doc.chunks:
            if not chunk.text.strip():
                continue

            matched_terms: list[MatchedTerm] = []
            score = 0.0

            # 원본 검색어 매칭
            for term in expanded_query.original_terms:
                if len(term) < 2:   # 너무 짧은 토큰은 무시
                    continue
                cnt = _count_occurrences(chunk.text, term)
                if cnt > 0:
                    matched_terms.append(MatchedTerm(term=term, match_type="original", count=cnt))
                    score += cnt * 1.0

            # 확장 검색어 매칭
            for term in expanded_query.expanded_terms:
                if len(term) < 2:
                    continue
                cnt = _count_occurrences(chunk.text, term)
                if cnt > 0:
                    matched_terms.append(MatchedTerm(term=term, match_type="expanded", count=cnt))
                    score += cnt * expanded_weight

            if not matched_terms:
                continue

            # 헤더 포함 청크에 가중치
            if _has_header(chunk.text):
                score *= _HEADER_WEIGHT

            # 파일당 최대 결과 수 제한
            if file_counts[file_key] >= max_per_file:
                continue

            file_counts[file_key] += 1

            # 컨텍스트 추출 (첫 번째 매칭 단어 기준)
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

    # 점수 내림차순 정렬
    results.sort(key=lambda r: r.score, reverse=True)

    return results[:max_results]
