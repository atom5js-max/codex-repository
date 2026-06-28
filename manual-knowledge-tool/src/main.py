"""
main.py
-------
기술자료 검색 도구 CLI 진입점.

사용법:
  python main.py "S300 속도지령 안 먹음"
  python main.py "Modbus 통신 안 됨" --max-results 10
  python main.py --interactive
  python main.py --list-files
  python main.py --stats
  python main.py "로드셀 값 튐" --no-cache
  python main.py "속도 안 먹음" --backend keyword   (현재 기본값)

Stage B 전환 시:
  python main.py "속도 안 먹음" --backend vector
  python main.py "속도 안 먹음" --backend hybrid

파이프라인:
  1. doc_cache       → 캐시 히트 시 재파싱 생략
  2. document_loader → 파일 로드 & 청크화
  3. synonym_expander → 현장어 → 매뉴얼어 확장
  4. BaseSearcher    → 검색 & 점수 계산
  5. summarizer      → (Stage C) LLM 요약, 현재 비활성
  6. result_writer   → Markdown 저장
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_SRC_DIR = Path(__file__).parent
_BASE_DIR = _SRC_DIR.parent
sys.path.insert(0, str(_SRC_DIR))

from base_searcher import BaseSearcher
from doc_cache import get_cache_path, load_cache, save_cache
from document_loader import load_all_documents
from keyword_search import KeywordSearcher, SearchResult
from result_writer import write_results
from summarizer import summarize
from synonym_expander import expand_query

# ── 경로 상수 ──────────────────────────────────────────────────────────────────
RULES_DIR = _BASE_DIR / "rules"
SYNONYM_RULES = RULES_DIR / "synonym_rules.yaml"
SEARCH_RULES = RULES_DIR / "search_rules.yaml"
OUTPUT_FILE = _BASE_DIR / "output" / "search_result.md"
CACHE_FILE = get_cache_path(_BASE_DIR)


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s | %(name)s | %(message)s",
    )


def _load_search_config() -> dict:
    """search_rules.yaml 에서 검색 설정을 읽는다. 실패 시 기본값 반환."""
    try:
        import yaml
        if SEARCH_RULES.exists():
            with SEARCH_RULES.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return data.get("search", {})
    except Exception:
        pass
    return {}


def _get_searcher(backend: str) -> BaseSearcher:
    if backend == "keyword":
        return KeywordSearcher()
    print(f"  경고: 알 수 없는 백엔드 '{backend}', keyword 로 폴백")
    return KeywordSearcher()


def _load_documents(use_cache: bool = True) -> list:
    """캐시를 확인하고 없으면 실제 파싱 후 캐시에 저장한다."""
    if use_cache:
        supported = {".md", ".txt", ".pdf"}
        expected: list[Path] = []
        for root in [_BASE_DIR / "manuals", _BASE_DIR / "notes"]:
            if root.exists():
                expected.extend(
                    fp for fp in root.rglob("*")
                    if fp.is_file() and fp.suffix.lower() in supported
                    and not fp.name.startswith(".")
                )

        cached = load_cache(CACHE_FILE, expected)
        if cached is not None:
            print(f"  캐시 히트: {len(cached)}개 파일 (재파싱 생략)")
            return cached

    documents = load_all_documents(_BASE_DIR)

    if use_cache and documents:
        save_cache(documents, CACHE_FILE)

    return documents


def run_search(query: str, args: argparse.Namespace) -> None:
    """단일 쿼리에 대해 전체 검색 파이프라인을 실행한다."""
    cfg = _load_search_config()
    max_results = args.max_results or cfg.get("max_results", 20)
    max_per_file = cfg.get("max_results_per_file", 5)
    context_chars = cfg.get("context_chars", 120)
    expanded_weight = cfg.get("expanded_match_weight", 0.7)

    print(f"\n[검색어] {query}")

    print("[1/5] 문서 로드 중...")
    use_cache = not getattr(args, "no_cache", False)
    documents = _load_documents(use_cache=use_cache)
    if not documents:
        print(
            "  경고: 로드된 문서가 없습니다.\n"
            "  manuals/ 또는 notes/ 폴더에 .md/.txt/.pdf 파일을 추가하세요."
        )

    print("[2/5] 현장어 → 매뉴얼어 확장 중...")
    expanded = expand_query(query, SYNONYM_RULES)
    if expanded.matched_rules:
        print(f"  발동 규칙: {', '.join(expanded.matched_rules)}")
        print(f"  확장 키워드 {len(expanded.expanded_terms)}개 추가")
    else:
        print("  발동 규칙 없음 (원본 키워드로만 검색)")

    print(f"[3/5] 키워드 검색 중 (backend: {args.backend})...")
    searcher = _get_searcher(args.backend)
    results = searcher.search(
        documents=documents,
        expanded_query=expanded,
        max_results=max_results,
        max_per_file=max_per_file,
        context_chars=context_chars,
        expanded_weight=expanded_weight,
    )
    print(f"  결과 {len(results)}건 발견")

    print("[4/5] 요약 생성 중...")
    summary = summarize(results, query, expanded)
    if summary:
        print("  요약 생성 완료")
    else:
        print("  요약 비활성 (Stage C)")

    print("[5/5] 결과 저장 중...")
    write_results(
        results=results,
        expanded_query=expanded,
        output_path=OUTPUT_FILE,
        summary=summary,
    )

    print("\n" + "=" * 60)
    if results:
        print("상위 결과 (최대 5건):")
        for i, r in enumerate(results[:5], 1):
            terms_str = ", ".join(r.all_matched_term_strings[:3])
            print(
                f"  [{i}] [{r.document.category}] {r.document.display_name}"
                f" — {terms_str} (점수: {r.score:.1f})"
            )
    else:
        print("  검색 결과 없음")
    print("=" * 60)
    print(f"전체 결과: {OUTPUT_FILE}")


def run_interactive() -> None:
    """대화형 검색 모드."""
    print("\n기술자료 검색 도구 (대화형 모드)")
    print("종료: 'q' 또는 'quit' 입력\n")

    print("문서 로드 중...")
    documents = _load_documents(use_cache=True)
    print(f"  {len(documents)}개 파일 로드 완료\n")

    cfg = _load_search_config()
    searcher = KeywordSearcher()

    while True:
        try:
            query = input("검색어> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not query:
            continue
        if query.lower() in ("q", "quit", "exit", "종료"):
            print("종료합니다.")
            break

        expanded = expand_query(query, SYNONYM_RULES)
        results = searcher.search(
            documents=documents,
            expanded_query=expanded,
            max_results=cfg.get("max_results", 20),
            max_per_file=cfg.get("max_results_per_file", 5),
        )
        write_results(results=results, expanded_query=expanded, output_path=OUTPUT_FILE)

        if results:
            for i, r in enumerate(results[:5], 1):
                print(
                    f"  [{i}] [{r.document.category}] {r.document.display_name}"
                    f" — {', '.join(r.all_matched_term_strings[:2])} (점수: {r.score:.1f})"
                )
        else:
            print("  결과 없음")
        print(f"  → {OUTPUT_FILE}\n")


def run_list_files() -> None:
    """로드 가능한 파일 목록을 출력한다."""
    documents = _load_documents(use_cache=True)
    if not documents:
        print("로드된 문서가 없습니다.")
        return
    print(f"\n로드된 문서 ({len(documents)}개):")
    for doc in documents:
        print(
            f"  [{doc.category:12s}] {doc.file_path.relative_to(_BASE_DIR)}"
            f"  ({len(doc.chunks)} chunks)"
        )


def run_stats() -> None:
    """문서 통계와 로드된 규칙 정보를 출력한다."""
    import yaml

    documents = _load_documents(use_cache=True)

    print(f"\n{'=' * 50}")
    print("문서 통계")
    print(f"{'=' * 50}")

    from collections import Counter
    cat_count: Counter = Counter()
    chunk_count: Counter = Counter()
    for doc in documents:
        cat_count[doc.category] += 1
        chunk_count[doc.category] += len(doc.chunks)

    print(f"{'카테고리':<15} {'파일 수':>6} {'청크 수':>8}")
    print("-" * 35)
    for cat in sorted(cat_count):
        print(f"  {cat:<13} {cat_count[cat]:>6} {chunk_count[cat]:>8}")
    print(f"  {'합계':<13} {sum(cat_count.values()):>6} {sum(chunk_count.values()):>8}")

    print(f"\n{'=' * 50}")
    print("동의어 규칙 통계")
    print(f"{'=' * 50}")

    if SYNONYM_RULES.exists():
        with SYNONYM_RULES.open(encoding="utf-8") as f:
            rules = yaml.safe_load(f) or {}
        print(f"  규칙 수: {len(rules)}개")
        for name, data in rules.items():
            if isinstance(data, dict):
                ft = len(data.get("field_terms", []))
                mt = len(data.get("manual_terms", []))
                ci = len(data.get("check_items", []))
                print(f"  {name}: 현장어 {ft}개 / 매뉴얼어 {mt}개 / 확인항목 {ci}개")

    print(f"\n캐시 파일: {CACHE_FILE}")
    print(f"캐시 존재: {'예' if CACHE_FILE.exists() else '아니오'}")
    if CACHE_FILE.exists():
        size_kb = CACHE_FILE.stat().st_size / 1024
        print(f"캐시 크기: {size_kb:.1f} KB")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="산업설비 기술자료 현장어-매뉴얼어 확장 검색 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py "S300 속도지령 안 먹음"
  python main.py "Modbus 통신 안 됨" --max-results 15
  python main.py "로드셀 값 튐"
  python main.py "LabVIEW DB 저장 느림"
  python main.py --interactive
  python main.py --list-files
  python main.py --stats
  python main.py "속도 안 먹음" --no-cache
        """,
    )
    parser.add_argument("query", nargs="?", help="검색어")
    parser.add_argument("--interactive", "-i", action="store_true", help="대화형 모드")
    parser.add_argument("--list-files", "-l", action="store_true", help="파일 목록 출력")
    parser.add_argument("--stats", "-s", action="store_true", help="문서/규칙 통계 출력")
    parser.add_argument("--max-results", "-n", type=int, default=None, help="최대 결과 수")
    parser.add_argument(
        "--backend",
        choices=["keyword", "vector", "hybrid"],
        default="keyword",
        help="검색 백엔드 (Stage B: vector/hybrid 예정)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="캐시를 무시하고 모든 파일을 재파싱",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 로그")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)

    if args.stats:
        run_stats()
    elif args.list_files:
        run_list_files()
    elif args.interactive:
        run_interactive()
    elif args.query:
        run_search(args.query, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
