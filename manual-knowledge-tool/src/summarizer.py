"""
summarizer.py
-------------
Stage C 플레이스홀더: 검색 결과를 LLM 으로 요약한다.

현재는 아무것도 반환하지 않는다(None).
Stage C 구현 시 아래 중 하나를 연결한다:

  옵션 1 - 로컬 Ollama:
    import requests
    response = requests.post("http://localhost:11434/api/generate", json={...})

  옵션 2 - Claude API (anthropic SDK):
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(...)

원칙:
  - 요약은 "관련 내용 정리"에 그친다
  - "원인은 X이다", "Y를 교체하라" 같은 단정 표현은 프롬프트에서 명시 금지
  - 요약 실패 시 None 반환, 검색 결과 자체를 그대로 출력
"""

from __future__ import annotations

from typing import Optional

from keyword_search import SearchResult
from synonym_expander import ExpandedQuery


# Stage C 구현 시 True 로 변경하거나 환경변수로 제어
_SUMMARIZER_ENABLED = False


def summarize(
    results: list[SearchResult],
    query: str,
    expanded_query: ExpandedQuery,
    max_input_chars: int = 3000,
) -> Optional[str]:
    """
    검색 결과를 요약 텍스트로 반환한다.

    Parameters
    ----------
    results         : 검색 결과 목록
    query           : 원본 검색어
    expanded_query  : 확장 쿼리 정보
    max_input_chars : LLM 에 전달할 최대 컨텍스트 길이

    Returns
    -------
    요약 문자열 또는 None (미구현/실패)
    """
    if not _SUMMARIZER_ENABLED:
        return None

    if not results:
        return None

    # Stage C 구현 시 아래 부분을 채운다
    # context = _build_context(results, max_input_chars)
    # prompt = _build_prompt(query, context)
    # return _call_llm(prompt)
    return None


def _build_context(results: list[SearchResult], max_chars: int) -> str:
    """상위 결과의 텍스트를 LLM 프롬프트용으로 이어 붙인다."""
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
    """LLM 에 전달할 프롬프트를 구성한다."""
    return (
        f"다음은 '{query}' 검색어와 관련된 기술 문서 발췌입니다.\n"
        "아래 내용을 바탕으로 현장 엔지니어가 참고할 수 있도록 관련 내용을 정리해 주세요.\n"
        "단, 원인을 단정하거나 조치를 확정하지 마시고, "
        "'확인이 필요합니다', '검토해 볼 수 있습니다' 수준으로 작성해 주세요.\n\n"
        f"[문서 발췌]\n{context}"
    )
