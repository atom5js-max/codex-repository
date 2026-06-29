"""Document chunk cache with input-file manifest validation."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from document_loader import Document
from text_chunker import Chunk

logger = logging.getLogger(__name__)

_CACHE_VERSION = 3
_DEFAULT_CACHE_FILE = ".doc_cache.json"


def _chunk_to_dict(chunk: Chunk) -> dict:
    return {
        "text": chunk.text,
        "chunk_index": chunk.chunk_index,
        "page_number": chunk.page_number,
        "source_info": chunk.source_info,
    }


def _chunk_from_dict(data: dict) -> Chunk:
    return Chunk(
        text=data["text"],
        chunk_index=data["chunk_index"],
        page_number=data.get("page_number"),
        source_info=data.get("source_info", {}),
    )


def _doc_to_dict(doc: Document) -> dict:
    return {
        "file_path": str(doc.file_path),
        "category": doc.category,
        "file_type": doc.file_type,
        "chunks": [_chunk_to_dict(chunk) for chunk in doc.chunks],
    }


def _doc_from_dict(data: dict) -> Document:
    doc = Document(
        file_path=Path(data["file_path"]),
        category=data["category"],
        file_type=data["file_type"],
    )
    doc.chunks = [_chunk_from_dict(chunk) for chunk in data.get("chunks", [])]
    return doc


def _file_manifest(files: list[Path]) -> dict[str, float]:
    return {
        str(file_path): file_path.stat().st_mtime if file_path.exists() else 0.0
        for file_path in files
    }


def save_cache(
    documents: list[Document],
    cache_path: Path,
    expected_files: list[Path] | None = None,
) -> None:
    source_files = expected_files or [doc.file_path for doc in documents]
    data = {
        "version": _CACHE_VERSION,
        "manifest": _file_manifest(source_files),
        "documents": [_doc_to_dict(doc) for doc in documents],
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    logger.debug("Cache saved: %s (%d documents)", cache_path, len(documents))


def load_cache(
    cache_path: Path,
    expected_files: list[Path],
) -> Optional[list[Document]]:
    if not cache_path.exists():
        return None

    try:
        with cache_path.open(encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        logger.debug("Cache read failed: %s", error)
        return None

    if data.get("version") != _CACHE_VERSION:
        return None

    if data.get("manifest", {}) != _file_manifest(expected_files):
        return None

    documents = [_doc_from_dict(item) for item in data.get("documents", [])]
    logger.debug("Cache loaded: %d documents", len(documents))
    return documents


def get_cache_path(base_dir: Path, filename: str = _DEFAULT_CACHE_FILE) -> Path:
    return base_dir / "output" / filename
