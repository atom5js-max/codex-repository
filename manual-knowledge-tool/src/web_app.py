"""Flask 기반 전자제품 매뉴얼 검색 웹 애플리케이션."""

from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template, request

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
        print(f"[2/3] Cache loaded — {len(cached)} documents ready")
        return cached

    print("[2/3] Loading documents... (PDF may take 30+ seconds)")
    docs = load_all_documents(_BASE)
    print(f"[3/3] Done — {len(docs)} documents loaded, saving cache...")
    if docs:
        save_cache(docs, CACHE_FILE)
    return docs


_documents = _boot_load()
_searcher = KeywordSearcher()


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
        out.append({
            "score": round(result.score, 2),
            "category": result.document.category,
            "display_name": result.document.display_name,
            "match_type": result.match_type_label,
            "matched_terms": result.all_matched_term_strings,
            "context": result.chunk.source_info.get("context_excerpt", ""),
            "location": result.chunk.source_info.get("location", ""),
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
        {"name": doc.file_path.name, "category": doc.category, "chunks": len(doc.chunks)}
        for doc in _documents
    ]
    return jsonify({"files": files, "total": len(files)})


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