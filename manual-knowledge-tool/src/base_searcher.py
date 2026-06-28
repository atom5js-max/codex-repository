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

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any  # noqa: F401

if TYPE_CHECKING:
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
        documents: list[Any],
        expanded_query: Any,
        max_results: int = 20,
        max_per_file: int = 5,
        context_chars: int = 120,
        **kwargs,
    ) -> list[Any]:
        ...

    def is_ready(self) -> bool:
        return True
