"""
pdf_extractor.py
----------------
PDF 파일에서 텍스트를 추출한다.
pdfplumber 를 우선 사용하고, 없으면 pypdf 로 대체한다.
텍스트가 없거나 너무 짧은 페이지(스캔 이미지)는 스킵한다.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_MIN_PAGE_TEXT = 30


def _extract_with_pdfplumber(file_path: Path) -> list[tuple[int, str]]:
    import pdfplumber  # type: ignore

    pages: list[tuple[int, str]] = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if len(text) >= _MIN_PAGE_TEXT:
                pages.append((i, text))
    return pages


def _extract_with_pypdf(file_path: Path) -> list[tuple[int, str]]:
    from pypdf import PdfReader  # type: ignore

    pages: list[tuple[int, str]] = []
    reader = PdfReader(str(file_path))
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if len(text) >= _MIN_PAGE_TEXT:
            pages.append((i, text))
    return pages


def extract_pdf_text(file_path: Path) -> list[tuple[int, str]]:
    try:
        return _extract_with_pdfplumber(file_path)
    except ImportError:
        logger.debug("pdfplumber 없음, pypdf 시도")
    except Exception as e:
        logger.warning("pdfplumber 추출 실패 (%s): %s", file_path.name, e)

    try:
        return _extract_with_pypdf(file_path)
    except ImportError:
        logger.warning(
            "PDF 라이브러리 없음. 'pip install pdfplumber' 또는 'pip install pypdf' 필요"
        )
    except Exception as e:
        logger.warning("pypdf 추출 실패 (%s): %s", file_path.name, e)

    return []
