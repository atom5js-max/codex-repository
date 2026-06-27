"""
doc_cache.py
------------
파싱된 Document 청크를 JSON 캐시 파일로 저장해
재실행 시 재파싱 없이 빠르게 로드한다.

캐시 무효화 조건:
  - 파일의 수정 시각(mtime)이 달라진 경우
  - 캐시 버전 번호가 다른 경우

Stage B(벡터 검색) 확장 포인트:
  - 각 Chunk 레코드에 'embedding' 필드를 추가해 저장
  - VectorSearcher 는 이 필드가 있으면 재임베딩 없이 재사용
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from document_loader import Document
from text_chunker import Chunk

logger = logging.getLogger(__name__)

_CACHE_VERSION = 1          # 구조 변경 시 올려서 전체 재파싱 유도
_DEFAULT_CACHE_FILE = ".doc_cache.json"


def _chunk_to_dict(chunk: Chunk) -> dict:
    return {
        "text": chunk.text,
        "chunk_index": chunk.chunk_index,
        "page_number": chunk.page_number,
        "source_info": chunk.source_info,
        # Stage B: "embedding": None  ← 벡터 검색 구현 시 여기에 저장
    }


def _chunk_from_dict(d: dict) -> Chunk:
    return Chunk(
        text=d["text"],
        chunk_index=d["chunk_index"],
        page_number=d.get("page_number"),
        source_info=d.get("source_info", {}),
    )


def _doc_to_dict(doc: Document) -> dict:
    return {
        "file_path": str(doc.file_path),
        "category": doc.category,
        "file_type": doc.file_type,
        "mtime": doc.file_path.stat().st_mtime if doc.file_path.exists() else 0.0,
        "chunks": [_chunk_to_dict(c) for c in doc.chunks],
    }


def _doc_from_dict(d: dict) -> Document:
    doc = Document(
        file_path=Path(d["file_path"]),
        category=d["category"],
        file_type=d["file_type"],
    )
    doc.chunks = [_chunk_from_dict(c) for c in d.get("chunks", [])]
    return doc


def save_cache(documents: list[Document], cache_path: Path) -> None:
    """파싱된 문서 목록을 JSON 캐시 파일로 저장한다."""
    data = {
        "version": _CACHE_VERSION,
        "files": {str(doc.file_path): _doc_to_dict(doc) for doc in documents},
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.debug("캐시 저장: %s (%d개 문서)", cache_path, len(documents))


def load_cache(
    cache_path: Path,
    expected_files: list[Path],
) -> Optional[list[Document]]:
    """
    캐시 파일이 유효하면 Document 목록을 반환하고,
    유효하지 않으면 None 을 반환한다.

    유효 조건: 버전 일치 + 모든 파일의 mtime 일치
    """
    if not cache_path.exists():
        return None

    try:
        with cache_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.debug("캐시 읽기 실패: %s", e)
        return None

    if data.get("version") != _CACHE_VERSION:
        logger.debug("캐시 버전 불일치, 재파싱")
        return None

    cached: dict = data.get("files", {})

    # expected_files 중 캐시에 없거나 mtime 이 달라진 파일이 있으면 무효
    for fp in expected_files:
        key = str(fp)
        if key not in cached:
            logger.debug("캐시에 없는 파일: %s", fp.name)
            return None
        current_mtime = fp.stat().st_mtime if fp.exists() else 0.0
        if abs(cached[key]["mtime"] - current_mtime) > 0.01:
            logger.debug("mtime 변경 감지: %s", fp.name)
            return None

    # 캐시에만 있고 실제 파일이 사라진 경우도 무효
    expected_keys = {str(fp) for fp in expected_files}
    if set(cached.keys()) != expected_keys:
        logger.debug("파일 목록 변경 감지, 재파싱")
        return None

    documents = [_doc_from_dict(d) for d in cached.values()]
    logger.debug("캐시 로드 성공: %d개 문서", len(documents))
    return documents


def get_cache_path(base_dir: Path, filename: str = _DEFAULT_CACHE_FILE) -> Path:
    """캐시 파일 경로를 반환한다 (output/ 폴더 내에 숨김 파일로 저장)."""
    return base_dir / "output" / filename
