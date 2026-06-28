"""
document_loader.py
------------------
manuals/ 와 notes/ 폴더에서 파일을 로드하고,
경로를 기준으로 제품군 카테고리를 자동 분류한다.

지원 포맷: .md, .txt, .pdf
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pdf_extractor import extract_pdf_text
from text_chunker import Chunk, chunk_text

logger = logging.getLogger(__name__)


_CATEGORY_MAP: dict[str, str] = {
    "inverter":    "inverter",
    "plc":         "plc",
    "loadcell":    "loadcell",
    "instruments": "instruments",
    "labview":     "labview",
    "database":    "database",
    "notes":       "notes",
}


@dataclass
class Document:
    """로드된 단일 문서를 나타낸다."""
    file_path: Path
    category: str
    file_type: str
    chunks: list[Chunk] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return self.file_path.name


def _infer_category(file_path: Path, base_dir: Path) -> str:
    try:
        relative = file_path.relative_to(base_dir)
    except ValueError:
        relative = file_path

    for part in relative.parts[:-1]:
        part_lower = part.lower()
        for key, category in _CATEGORY_MAP.items():
            if key in part_lower:
                return category

    return "unknown"


def _read_text_file(file_path: Path) -> Optional[str]:
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr"]
    for enc in encodings:
        try:
            return file_path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    logger.warning("인코딩 감지 실패, 스킵: %s", file_path)
    return None


def _load_single_file(file_path: Path, base_dir: Path) -> Optional[Document]:
    suffix = file_path.suffix.lower().lstrip(".")
    category = _infer_category(file_path, base_dir)

    if suffix in ("md", "txt"):
        raw_text = _read_text_file(file_path)
        if not raw_text:
            return None
        chunks = chunk_text(raw_text, source_info={"file": str(file_path)})

    elif suffix == "pdf":
        pages = extract_pdf_text(file_path)
        if not pages:
            logger.info("PDF 텍스트 없음(스캔 이미지 추정), 스킵: %s", file_path)
            return None
        chunks = []
        for page_no, page_text in pages:
            page_chunks = chunk_text(
                page_text,
                source_info={"file": str(file_path), "page": page_no},
                page_number=page_no,
            )
            chunks.extend(page_chunks)

    else:
        return None

    if not chunks:
        return None

    return Document(
        file_path=file_path,
        category=category,
        file_type=suffix,
        chunks=chunks,
    )


def load_all_documents(base_dir: Path) -> list[Document]:
    supported_suffixes = {".md", ".txt", ".pdf"}
    search_roots = [
        base_dir / "manuals",
        base_dir / "notes",
    ]

    documents: list[Document] = []

    for root in search_roots:
        if not root.exists():
            logger.warning("폴더가 없음, 스킵: %s", root)
            continue

        for file_path in sorted(root.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in supported_suffixes:
                continue
            if file_path.name.startswith(".") or file_path.name.startswith("~"):
                continue

            doc = _load_single_file(file_path, base_dir)
            if doc is not None:
                documents.append(doc)
                logger.debug(
                    "로드 완료: [%s] %s (%d chunks)",
                    doc.category, doc.display_name, len(doc.chunks),
                )

    logger.info("총 %d개 파일 로드 완료", len(documents))
    return documents
