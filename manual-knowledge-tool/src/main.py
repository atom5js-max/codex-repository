"""
main.py
-------
기술자료 검색 도구 CLI 진입점.

사용법:
  python main.py "S300 속도지령 안 먹음"
  python main.py "Modbus 통신 안 됨" --max-results 10
  python main.py --interactive
  python main.py --list-files

확장 흐름:
  1. document_loader  → 파일 로드 & 청크화
  2. synonym_expander → 현장어 → 매뉴얼어 확장
  3. keyword_search   → 청크 검색 & 점수 계산
  4. result_writer    → Markdown 저장
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# src/ 폴더를 직접 실행하므로 sys.path 는 이미 포함되어 있다.
# 패키지 설치 없이 로컬 실행을 위해 명시적으로 추가한다.
_SRC_DIR = Path(__file__).parent
_BASE_DIR = _SRC_DIR.parent
sys.path.insert(0, str(_SRC_DIR))

from document_loader import load_all_documents
from keyword_search import search_documents
from result_writer import write_results
from synonym_expander import expand_query


# ── 경로 상수 ─────────────────────────────────────────────────────────────────
RULES_DIR = _BASE_DIR / "rules"
SYNONYM_RULES = RULES_DIR / "synonym_rules.yaml"
SEARCH_RULES = RULES_DIR / "search_rules.yaml"
OUTPUT_FILE = _BASE_DIR / "output" / "search_result.md"


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


def run_search(query: str, args: argparse.Namespace) -> None:
    """단일 쿼리에 대해 전체 검색 파이프라인을 실행한다."""
    cfg = _load_search_config()

    max_results = args.max_results or cfg.get("max_results", 20)
    max_per_file = cfg.get("max_results_per_file", 5)
    context_chars = cfg.get("context_chars", 120)
    expanded_weight = cfg.get("expanded_match_weight", 0.7)

    # 1단계: 문서 로드
    print(f"\n[검색어] {query}")
    print("[1/4] 문서 로드 중...")
    documents = load_all_documents(_BASE_DIR)
    if not documents:
        print(
            "  경고: 로드된 문서가 없습니다.\n"
            "  manuals/ 또는 notes/ 폴더에 .md/.txt/.pdf 파일을 추가하세요."
        )

    # 2단계: 검색어 확장
    print("[2/4] 현장어 → 매뉴얼어 확장 중...")
    expanded = expand_query(query, SYNONYM_RULES)
    if expanded.matched_rules:
        print(f"  발동 규칙: {', '.join(expanded.matched_rules)}")
        print(f"  확장 키워드 {len(expanded.expanded_terms)}개 추가")
    else:
        print("  발동 규칙 없음 (원본 키워드로만 검색)")

    # 3단계: 키워드 검색
    print("[3/4] 키워드 검색 중...")
    results = search_documents(
        documents=documents,
        expanded_query=expanded,
        max_results=max_results,
        max_per_file=max_per_file,
        context_chars=context_chars,
        expanded_weight=expanded_weight,
    )
    print(f"  결과 {len(results)}건 발견")

    # 4단계: 결과 저장
    print("[4/4] 결과 저장 중...")
    write_results(
        results=results,
        expanded_query=expanded,
        output_path=OUTPUT_FILE,
    )

    # 터미널 요약 출력
    print("\n" + "=" * 60)
    if results:
        print(f"상위 결과 (최대 5건):")
        for i, r in enumerate(results[:5], 1):
            category = r.document.category
            fname = r.document.display_name
            terms_str = ", ".join(r.all_matched_term_strings[:3])
            print(f"  [{i}] [{category}] {fname} — {terms_str} (점수: {r.score:.1f})")
    else:
        print("  검색 결과 없음")
    print("=" * 60)
    print(f"전체 결과: {OUTPUT_FILE}")


def run_interactive() -> None:
    """대화형 검색 모드. 'quit' 또는 'q' 입력 시 종료."""
    print("\n기술자료 검색 도구 (대화형 모드)")
    print("종료: 'q' 또는 'quit' 입력\n")

    # 문서는 세션 시작 시 한 번만 로드
    print("문서 로드 중...")
    documents = load_all_documents(_BASE_DIR)
    print(f"  {len(documents)}개 파일 로드 완료\n")

    cfg = _load_search_config()
    max_results = cfg.get("max_results", 20)
    max_per_file = cfg.get("max_results_per_file", 5)
    context_chars = cfg.get("context_chars", 120)
    expanded_weight = cfg.get("expanded_match_weight", 0.7)

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
        results = search_documents(
            documents=documents,
            expanded_query=expanded,
            max_results=max_results,
            max_per_file=max_per_file,
            context_chars=context_chars,
            expanded_weight=expanded_weight,
        )
        write_results(
            results=results,
            expanded_query=expanded,
            output_path=OUTPUT_FILE,
        )

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
    documents = load_all_documents(_BASE_DIR)
    if not documents:
        print("로드된 문서가 없습니다.")
        return
    print(f"\n로드된 문서 ({len(documents)}개):")
    for doc in documents:
        print(f"  [{doc.category:12s}] {doc.file_path.relative_to(_BASE_DIR)}  ({len(doc.chunks)} chunks)")


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
        """,
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="검색어 (예: 'S300 속도지령 안 먹음')",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="대화형 검색 모드",
    )
    parser.add_argument(
        "--list-files", "-l",
        action="store_true",
        help="로드 가능한 파일 목록 출력",
    )
    parser.add_argument(
        "--max-results", "-n",
        type=int,
        default=None,
        help="최대 결과 수 (기본값: search_rules.yaml 설정 따름)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세 로그 출력",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)

    if args.list_files:
        run_list_files()
    elif args.interactive:
        run_interactive()
    elif args.query:
        run_search(args.query, args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
