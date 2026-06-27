"""
base_searcher.py
----------------
검색 백엔드의 추상 인터페이스.

Stage B(벡터 검색)로 교체할 때 이 인터페이스를 구현하면
main.py 변경 없이 --backend 플래그만으로 전환 가능하다.

구현체:
  - KeywordSearcher  (keyword_search.py)  ← 현재 기본값
  - VectorSearcher   (vector_search.py)   ← Stage B 예정
  - HybridSearcher   (hybrid_search.py)   ← Stage B+ 예정
"""

from __future__ import annotations

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any  # noqa: F401

if TYPE_CHECKING:
    # 타입 힌트 전용 임포트 — 런타임에는 로드하지 않아 순환 임포트 방지
    from document_loader import Document
    from synonym_expander import ExpandedQuery


class BaseSearcher(ABC):
    """모든 검색 백엔드가 구현해야 하는 인터페이스."""

    @property
    @abstractmethod
    def name(self) -> str:
        """백엔드 식별자 (로그/출력용)."""
        ...

    @abstractmethod
    def search(
        self,
        documents: list[Any],       # list[Document]
        expanded_query: Any,        # ExpandedQuery
        max_results: int = 20,
        max_per_file: int = 5,
        context_chars: int = 120,
        **kwargs,
    ) -> list[Any]:                 # list[SearchResult]
        """
        문서 목록에서 검색해 점수 내림차순 결과를 반환한다.

        Parameters
        ----------
        documents      : 로드된 Document 목록
        expanded_query : 원본 + 확장 키워드 정보
        max_results    : 전체 최대 반환 수
        max_per_file   : 파일당 최대 반환 수
        context_chars  : 매칭 주변 표시 글자 수
        """
        ...

    def is_ready(self) -> bool:
        """
        백엔드가 사용 가능한 상태인지 확인한다.
        VectorSearcher 는 임베딩 모델 로드 여부를 여기서 체크한다.
        """
        return True
