"""
pdf_extractor.py
----------------
PDF 파일에서 텍스트를 추출한다.
pdfplumber 를 우선 사용하고, 없으면 pypdf 로 대체한다.
텍스트가 없거나 너무 짧은 페이지(스캔 이미지)는 스킵한다.
복잡한 PDF 는 처리가 지연될 수 있으므로 파일당 20초 타임아웃을 적용한다.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path

logger = logging.getLogger(__name__)

_MIN_PAGE_TEXT = 30
_PDF_TIMEOUT   = 20  # seconds per PDF file


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


def _run_with_timeout(fn, file_path: Path, timeout: int) -> list[tuple[int, str]] | None:
    """fn(file_path) 를 별도 스레드에서 실행, timeout 초 안에 끝나지 않으면 None 반환."""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn, file_path)
    executor.shutdown(wait=False)
    try:
        return future.result(timeout=timeout)
    except FuturesTimeout:
        return None


def extract_pdf_text(file_path: Path) -> list[tuple[int, str]]:
    # ── pdfplumber (타임아웃 적용) ──────────────────────────────────
    try:
        result = _run_with_timeout(_extract_with_pdfplumber, file_path, _PDF_TIMEOUT)
        if result is not None:
            return result
        logger.warning("pdfplumber 타임아웃(%ds), pypdf 시도: %s", _PDF_TIMEOUT, file_path.name)
        print(f"  [경고] PDF 처리 지연, pypdf 로 재시도: {file_path.name}")
    except ImportError:
        logger.debug("pdfplumber 없음, pypdf 시도")
    except Exception as e:
        logger.warning("pdfplumber 추출 실패 (%s): %s", file_path.name, e)

    # ── pypdf 대체 (타임아웃 적용) ───────────────────────────────
    try:
        result = _run_with_timeout(_extract_with_pypdf, file_path, _PDF_TIMEOUT)
        if result is not None:
            return result
        logger.warning("pypdf 타임아웃, 스킵: %s", file_path.name)
        print(f"  [경고] PDF 처리 실패, 스킵: {file_path.name}")
    except ImportError:
        logger.warning(
            "PDF 라이브러리 없음. 'pip install pdfplumber' 또는 'pip install pypdf' 필요"
        )
    except Exception as e:
        logger.warning("pypdf 추출 실패 (%s): %s", file_path.name, e)

    return []
