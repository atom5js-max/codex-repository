"""
summarizer.py
-------------
Stage C 플레이스홀더: 검색 결과를 LLM 으로 요약한다.
현재는 아무것도 반환하지 않는다(None).
"""

from __future__ import annotations

from typing import Optional

from keyword_search import SearchResult
from synonym_expander import ExpandedQuery


_SUMMARIZER_ENABLED = False


def summarize(
    results: list[SearchResult],
    query: str,
    expanded_query: ExpandedQuery,
    max_input_chars: int = 3000,
) -> Optional[str]:
    if not _SUMMARIZER_ENABLED:
        return None
    if not results:
        return None
    return None


def _build_context(results: list[SearchResult], max_chars: int) -> str:
    parts: list[str] = []
    total = 0
    for r in results:
        snippet = r.chunk.text[:500]
        if total + len(snippet) > max_chars:
            break
        parts.append(f"[{r.document.category} / {r.document.display_name}]\n{snippet}")
        total += len(snippet)
    return "\n\n---\n\n".join(parts)


def _build_prompt(query: str, context: str) -> str:
    return (
        f"다음은 '{query}' 검색어와 관련된 기술 문서 발췌입니다.\n"
        "아래 내용을 바탕으로 현장 엔지니어가 참고할 수 있도록 관련 내용을 정리해 주세요.\n"
        "단, 원인을 단정하거나 조치를 확정하지 마시고, "
        "'확인이 필요합니다', '검토해 볼 수 있습니다' 수준으로 작성해 주세요.\n\n"
        f"[문서 발췌]\n{context}"
    )
