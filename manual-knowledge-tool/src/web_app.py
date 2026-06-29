"""Flask 기반 전자제품 매뉴얼 검색 웹 애플리케이션."""

from __future__ import annotations

import os
import sys
import webbrowser
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from threading import Lock

from flask import Flask, abort, jsonify, render_template, request, send_file

_SRC = Path(__file__).parent
_BASE = _SRC.parent
sys.path.insert(0, str(_SRC))

from doc_cache import get_cache_path, load_cache, save_cache
from document_loader import load_all_documents
from keyword_search import KeywordSearcher
from synonym_expander import expand_query

SYNONYM_RULES = _BASE / "rules" / "synonym_rules.yaml"
SEARCH_RULES = _BASE / "rules" / "search_rules.yaml"
CACHE_FILE = get_cache_path(_BASE)

app = Flask(__name__)


def _boot_load() -> list:
    supported = {".md", ".txt", ".pdf"}
    expected: list[Path] = []
    for root in [_BASE / "manuals", _BASE / "notes"]:
        if root.exists():
            expected.extend(
                fp for fp in root.rglob("*")
                if fp.is_file()
                and fp.suffix.lower() in supported
                and not fp.name.startswith(".")
            )

    print(f"[1/3] Checking cache... ({len(expected)} files found)")
    cached = load_cache(CACHE_FILE, expected)
    if cached is not None:
        print(f"[2/3] Cache loaded - {len(cached)} documents ready")
        return cached

    print("[2/3] Loading documents... (PDF may take 30+ seconds)")
    docs = load_all_documents(_BASE)
    print(f"[3/3] Done - {len(docs)} documents loaded, saving cache...")
    if docs:
        save_cache(docs, CACHE_FILE, expected)
    return docs


_documents = _boot_load()
_searcher = KeywordSearcher()
_document_registry = {str(index): document for index, document in enumerate(_documents)}
_document_ids = {str(document.file_path): doc_id for doc_id, document in _document_registry.items()}
_pdf_preview_lock = Lock()


def _get_document(document_id: str):
    document = _document_registry.get(document_id)
    if document is None:
        abort(404, description="문서를 찾을 수 없습니다.")
    return document


def _is_allowed_document_path(file_path: Path) -> bool:
    resolved = file_path.resolve()
    for root in (_BASE / "manuals", _BASE / "notes"):
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def _page_text(document, page_number: int) -> str:
    page_chunks = [
        chunk.text.strip()
        for chunk in document.chunks
        if chunk.page_number == page_number and chunk.text.strip()
    ]
    return "\n\n".join(page_chunks)


@lru_cache(maxsize=64)
def _render_pdf_page_preview(file_path: str, page_number: int) -> bytes:
    import pypdfium2 as pdfium  # type: ignore

    # PDFium은 동일 프로세스 내 동시 렌더링 시 불안정할 수 있어 순차 처리한다.
    with _pdf_preview_lock:
        pdf = pdfium.PdfDocument(file_path)
        try:
            if page_number < 1 or page_number > len(pdf):
                raise IndexError(page_number)
            page = pdf[page_number - 1]
            try:
                bitmap = page.render(scale=0.7)
                try:
                    image = bitmap.to_pil()
                    output = BytesIO()
                    image.save(output, format="PNG", optimize=True)
                    return output.getvalue()
                finally:
                    bitmap.close()
            finally:
                page.close()
        finally:
            pdf.close()


def _load_search_cfg() -> dict:
    try:
        import yaml
        if SEARCH_RULES.exists():
            with SEARCH_RULES.open(encoding="utf-8") as f:
                return (yaml.safe_load(f) or {}).get("search", {})
    except Exception:
        pass
    return {}


@app.route("/")
def index():
    return render_template("index.html", doc_count=len(_documents))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "documents": len(_documents)})


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({
            "results": [], "query": "", "matched_rules": [],
            "original_terms": [], "expanded_terms": [], "check_items": [],
        })

    cfg = _load_search_cfg()
    expanded = expand_query(q, SYNONYM_RULES)
    results = _searcher.search(
        documents=_documents,
        expanded_query=expanded,
        max_results=cfg.get("max_results", 20),
        max_per_file=cfg.get("max_results_per_file", 5),
        context_chars=cfg.get("context_chars", 150),
        expanded_weight=cfg.get("expanded_match_weight", 0.7),
    )

    out = []
    for result in results:
        page_number = result.chunk.page_number
        out.append({
            "score": round(result.score, 2),
            "category": result.document.category,
            "display_name": result.document.display_name,
            "document_id": _document_ids[str(result.document.file_path)],
            "file_type": result.document.file_type,
            "page_number": page_number,
            "match_type": result.match_type_label,
            "matched_terms": result.all_matched_term_strings,
            "context": result.chunk.source_info.get("context_excerpt", ""),
            "location": (
                f"PDF {page_number}쪽"
                if result.document.file_type == "pdf" and page_number
                else result.chunk.source_info.get("location", "")
            ),
        })

    return jsonify({
        "query": q,
        "original_terms": expanded.original_terms,
        "expanded_terms": expanded.expanded_terms,
        "matched_rules": expanded.matched_rules,
        "check_items": expanded.check_items,
        "results": out,
    })


@app.route("/api/files")
def api_files():
    files = [
        {
            "id": _document_ids[str(doc.file_path)],
            "name": doc.file_path.name,
            "category": doc.category,
            "file_type": doc.file_type,
            "chunks": len(doc.chunks),
        }
        for doc in _documents
    ]
    return jsonify({"files": files, "total": len(files)})


@app.route("/api/documents/<document_id>/pages/<int:page_number>")
def api_document_page(document_id: str, page_number: int):
    document = _get_document(document_id)
    if document.file_type != "pdf":
        abort(400, description="PDF 문서만 페이지 단위로 조회할 수 있습니다.")
    if page_number < 1:
        abort(400, description="페이지 번호는 1 이상이어야 합니다.")

    text = _page_text(document, page_number)
    if not text:
        abort(404, description="해당 페이지의 추출 텍스트가 없습니다.")

    cid_count = text.lower().count("(cid:")
    extraction_warning = (
        "이 PDF는 글꼴 인코딩 때문에 추출문 일부가 깨질 수 있습니다. "
        "왼쪽 PDF 원본 화면을 기준으로 확인하십시오."
        if cid_count >= 3
        else ""
    )
    return jsonify({
        "document_id": document_id,
        "display_name": document.display_name,
        "page_number": page_number,
        "text": text,
        "extraction_warning": extraction_warning,
    })


@app.route("/api/documents/<document_id>/file")
def api_document_file(document_id: str):
    document = _get_document(document_id)
    file_path = document.file_path
    if (
        document.file_type != "pdf"
        or file_path.suffix.lower() != ".pdf"
        or not file_path.is_file()
        or not _is_allowed_document_path(file_path)
    ):
        abort(404, description="PDF 원본 파일을 찾을 수 없습니다.")

    response = send_file(
        file_path,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=file_path.name,
        conditional=True,
        max_age=3600,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/api/documents/<document_id>/pages/<int:page_number>/preview.png")
def api_document_page_preview(document_id: str, page_number: int):
    document = _get_document(document_id)
    file_path = document.file_path
    if (
        document.file_type != "pdf"
        or file_path.suffix.lower() != ".pdf"
        or not file_path.is_file()
        or not _is_allowed_document_path(file_path)
        or page_number < 1
    ):
        abort(404, description="PDF 미리보기를 만들 수 없습니다.")

    try:
        png_bytes = _render_pdf_page_preview(str(file_path.resolve()), page_number)
    except (IndexError, RuntimeError, ValueError):
        abort(404, description="해당 PDF 페이지가 없습니다.")

    response = send_file(
        BytesIO(png_bytes),
        mimetype="image/png",
        conditional=True,
        max_age=3600,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    open_browser = os.environ.get("OPEN_BROWSER", "1") == "1"

    print("=" * 55)
    print("  기술자료 검색 대시보드 시작")
    print(f"  문서 {len(_documents)}개 로드 완료")
    print(f"  로컬 접속: http://localhost:{port}")
    print(f"  서버 바인딩: {host}:{port}")
    print("  종료: Ctrl+C")
    print("=" * 55)

    if open_browser:
        webbrowser.open(f"http://localhost:{port}")
    app.run(host=host, port=port, debug=False)
