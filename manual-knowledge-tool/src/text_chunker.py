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


DEFAULT_MIN_CHUNK = 20
DEFAULT_MAX_CHUNK = 800

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。])\s+")


@dataclass
class Chunk:
    """단일 검색 단위(문단/단락)를 나타낸다."""
    text: str
    chunk_index: int
    page_number: Optional[int] = None
    source_info: dict = field(default_factory=dict)

    @property
    def preview(self) -> str:
        return self.text[:80].replace("\n", " ")


def _split_into_sentences(text: str) -> list[str]:
    parts = _SENTENCE_SPLIT.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def _merge_short_chunks(
    raw_chunks: list[str],
    min_len: int,
    max_len: int,
) -> list[str]:
    result: list[str] = []

    for raw in raw_chunks:
        raw = raw.strip()
        if not raw:
            continue

        if len(raw) > max_len:
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
    if not text or not text.strip():
        return []

    raw_paragraphs = re.split(r"\n\s*\n", text)
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
