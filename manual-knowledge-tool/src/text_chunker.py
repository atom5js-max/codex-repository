"""
text_chunker.py
---------------
문서 텍스트를 검색 가능한 청크(단락)로 분할한다.

분할 우선순위:
  1. 빈 줄(이중 개행)로 단락 구분
  2. 단락이 max_chunk_length 초과 시 문장 단위로 재분할
  3. min_chunk_length 미만 청크는 이전 청크에 병합하거나 버린다
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# 기본 청킹 파라미터 (search_rules.yaml 로 재정의 가능)
DEFAULT_MIN_CHUNK = 20
DEFAULT_MAX_CHUNK = 800

# 문장 구분 패턴 (마침표/느낌표/물음표 + 공백 또는 줄바꿈)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。])\s+")


@dataclass
class Chunk:
    """단일 검색 단위(문단/단락)를 나타낸다."""
    text: str
    chunk_index: int          # 문서 내 순번 (0-based)
    page_number: Optional[int] = None  # PDF인 경우 페이지 번호
    source_info: dict = field(default_factory=dict)

    @property
    def preview(self) -> str:
        """앞 80자 미리보기"""
        return self.text[:80].replace("\n", " ")


def _split_into_sentences(text: str) -> list[str]:
    """문장 단위로 분할한다."""
    parts = _SENTENCE_SPLIT.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def _merge_short_chunks(
    raw_chunks: list[str],
    min_len: int,
    max_len: int,
) -> list[str]:
    """
    너무 짧은 청크를 앞 청크에 병합하고,
    너무 긴 청크는 문장 단위로 재분할한다.
    """
    result: list[str] = []

    for raw in raw_chunks:
        raw = raw.strip()
        if not raw:
            continue

        if len(raw) > max_len:
            # 긴 청크: 문장 단위 재분할
            sentences = _split_into_sentences(raw)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) + 1 <= max_len:
                    current = (current + " " + sent).strip()
                else:
                    if current:
                        result.append(current)
                    current = sent
            if current:
                result.append(current)
        elif len(raw) < min_len:
            # 짧은 청크: 이전 청크에 병합
            if result:
                result[-1] = result[-1] + "\n" + raw
            else:
                result.append(raw)
        else:
            result.append(raw)

    return result


def chunk_text(
    text: str,
    source_info: dict | None = None,
    page_number: Optional[int] = None,
    min_chunk: int = DEFAULT_MIN_CHUNK,
    max_chunk: int = DEFAULT_MAX_CHUNK,
) -> list[Chunk]:
    """
    텍스트를 청크 목록으로 분할한다.

    Parameters
    ----------
    text        : 원본 텍스트
    source_info : 파일 경로 등 출처 정보 (검색 결과 표시용)
    page_number : PDF 페이지 번호 (없으면 None)
    min_chunk   : 최소 청크 길이
    max_chunk   : 최대 청크 길이
    """
    if not text or not text.strip():
        return []

    # 이중 개행으로 1차 분할
    raw_paragraphs = re.split(r"\n\s*\n", text)

    # 길이 조정 (짧은 병합, 긴 재분할)
    paragraphs = _merge_short_chunks(raw_paragraphs, min_chunk, max_chunk)

    chunks: list[Chunk] = []
    for idx, para in enumerate(paragraphs):
        chunks.append(
            Chunk(
                text=para,
                chunk_index=idx,
                page_number=page_number,
                source_info=source_info or {},
            )
        )

    return chunks
