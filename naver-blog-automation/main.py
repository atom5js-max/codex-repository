"""
미술교습소 네이버 블로그 자동화 (API 없는 버전)
템플릿 기반 글 생성 + 네이버 자동 게시 + 게시물 확인
"""

import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime

from template_generator import generate_blog_post, TOPIC_LIST, TEMPLATES
from naver_blog_poster import run_post


# ─────────────────────── 출력 헬퍼 ───────────────────────

def print_divider(char="─", width=60):
    print(char * width)

def print_post_preview(post: dict):
    print_divider("═")
    print(f"  제목 : {post['title']}")
    print(f"  주제 : {post['topic']}")
    print(f"  태그 : {', '.join(post['tags'][:5])} 외 {max(0, len(post['tags'])-5)}개")
    print_divider()
    preview = post["content"][:400].replace("\n", "\n  ")
    print(f"  {preview}...")
    print_divider("═")

def save_post(post: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=2)
    print(f"  저장: {path}")

def print_result(result: dict):
    print_divider("═")
    if result.get("posted"):
        print("  ✅ 게시 완료!")
    else:
        print(f"  ❌ 게시 실패: {result.get('error', '알 수 없음')}")

    v = result.get("verified")
    if v:
        print_divider()
        print("  [게시물 확인]")
        if v.get("success"):
            print(f"  ✓ 확인 성공!")
            print(f"  제목 : {v.get('title_found')}")
            print(f"  URL  : {v.get('url')}")
        else:
            print(f"  ⚠ 자동 확인 불가 → 스크린샷 직접 확인 필요")
            print(f"  블로그: {v.get('blog_url')}")
        print(f"  📸 스크린샷: {v.get('screenshot')}")

    print_divider("═")


# ─────────────────────── 인자 파싱 ───────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="미술교습소 네이버 블로그 자동화 (API 없는 버전)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # ── generate ──
    g = sub.add_parser("generate", help="블로그 글 생성만 (게시 안함)")
    g.add_argument("--topic", choices=TOPIC_LIST, default="수업소개", help="주제 선택")
    g.add_argument("--detail", default="", help="수업 상세 내용")
    g.add_argument("--tags", nargs="+", help="추가 태그")
    g.add_argument("--images", nargs="+", help="사진 경로 (위치 표시용)")
    g.add_argument("--output", default="", help="저장 파일명 (기본: 자동)")

    # ── post ──
    p = sub.add_parser("post", help="글 생성 + 네이버 게시 + 확인")
    p.add_argument("--topic", choices=TOPIC_LIST, default="수업소개", help="주제 선택")
    p.add_argument("--detail", default="", help="수업 상세 내용")
    p.add_argument("--tags", nargs="+", help="추가 태그")
    p.add_argument("--images", nargs="+", help="첨부 사진 파일 경로")
    p.add_argument("--draft", action="store_true", help="임시저장만 (발행 안함)")
    p.add_argument("--headless", action="store_true", help="브라우저 숨김 모드")

    # ── upload ──
    u = sub.add_parser("upload", help="저장된 JSON 파일로 게시 + 확인")
    u.add_argument("--file", required=True, help="게시할 JSON 파일")
    u.add_argument("--images", nargs="+", help="첨부 사진 파일 경로")
    u.add_argument("--draft", action="store_true", help="임시저장만")
    u.add_argument("--headless", action="store_true", help="브라우저 숨김 모드")

    # ── verify ──
    v = sub.add_parser("verify", help="최근 게시물 확인만")
    v.add_argument("--title", default="", help="확인할 게시물 제목 (일부)")
    v.add_argument("--headless", action="store_true", help="브라우저 숨김 모드")

    # ── batch ──
    b = sub.add_parser("batch", help="여러 주제로 일괄 생성")
    b.add_argument("--count", type=int, default=5, help="생성할 글 수")
    b.add_argument("--out-dir", default="batch_output", help="저장 폴더")

    return parser


# ─────────────────────── 명령 처리 ───────────────────────

async def cmd_generate(args):
    print(f"\n[{args.topic}] 블로그 글 생성 중...")
    post = generate_blog_post(
        topic_key=args.topic,
        class_detail=args.detail,
        image_paths=args.images,
        custom_tags=args.tags,
    )
    print_post_preview(post)

    fname = args.output or f"post_{args.topic}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    save_post(post, fname)


async def cmd_post(args):
    print(f"\n[{args.topic}] 블로그 글 생성 중...")
    post = generate_blog_post(
        topic_key=args.topic,
        class_detail=args.detail,
        image_paths=args.images,
        custom_tags=args.tags,
    )
    print_post_preview(post)

    print("\n네이버 블로그 게시 시작...")
    result = await run_post(
        title=post["title"],
        content=post["content"],
        tags=post["tags"],
        image_paths=args.images,
        publish_now=not args.draft,
        headless=args.headless,
    )
    print_result(result)

    fname = f"post_{args.topic}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    post["result"] = result
    save_post(post, fname)


async def cmd_upload(args):
    fpath = Path(args.file)
    if not fpath.exists():
        print(f"파일 없음: {args.file}")
        return

    with open(fpath, encoding="utf-8") as f:
        post = json.load(f)

    print_post_preview(post)

    print("\n네이버 블로그 게시 시작...")
    result = await run_post(
        title=post["title"],
        content=post["content"],
        tags=post.get("tags", []),
        image_paths=args.images,
        publish_now=not args.draft,
        headless=args.headless,
    )
    print_result(result)


async def cmd_verify(args):
    from naver_blog_poster import NaverBlogPoster
    print("\n게시물 확인 시작...")
    poster = NaverBlogPoster(headless=args.headless, slow_mo=80)
    try:
        await poster.start()
        if not await poster.login():
            print("로그인 실패")
            return
        result = await poster.verify_post(args.title)
        print_divider("═")
        if result["success"]:
            print("  ✅ 게시물 확인 완료!")
            print(f"  제목 : {result['title_found']}")
            print(f"  URL  : {result['url']}")
        else:
            print("  ⚠ 자동 확인 불가 → 스크린샷을 직접 확인하세요.")
            print(f"  블로그: {result['blog_url']}")
        print(f"  📸 스크린샷: {result['screenshot']}")
        print_divider("═")
    finally:
        await poster.stop()


async def cmd_batch(args):
    out_dir = Path(args.out_dir)
    out_dir.mkdir(exist_ok=True)
    print(f"\n{args.count}개 글 일괄 생성 중...")

    topics_cycle = TOPIC_LIST * ((args.count // len(TOPIC_LIST)) + 1)
    posts = []
    for i in range(args.count):
        topic = topics_cycle[i]
        post = generate_blog_post(topic_key=topic)
        fname = out_dir / f"post_{i+1:02d}_{topic}.json"
        save_post(post, str(fname))
        print(f"  [{i+1}/{args.count}] {post['title']}")
        posts.append(post)

    summary = out_dir / "summary.txt"
    with open(summary, "w", encoding="utf-8") as f:
        for i, p in enumerate(posts, 1):
            f.write(f"{i:02d}. [{p['topic']}] {p['title']}\n")

    print(f"\n✅ {len(posts)}개 글 생성 완료")
    print(f"  폴더: {out_dir}/")
    print(f"  목록: {summary}")


# ─────────────────────── 메인 ───────────────────────

async def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "generate":
        await cmd_generate(args)
    elif args.command == "post":
        await cmd_post(args)
    elif args.command == "upload":
        await cmd_upload(args)
    elif args.command == "verify":
        await cmd_verify(args)
    elif args.command == "batch":
        await cmd_batch(args)
    else:
        print("\n미술교습소 네이버 블로그 자동화 (API 없는 버전)")
        print_divider()
        print("사용법:")
        print("  글 생성만       : python main.py generate --topic 작품전시 --detail '수묵화 수업'")
        print("  생성+게시+확인  : python main.py post --topic 수업소개 --images photo1.jpg photo2.jpg")
        print("  파일로 게시     : python main.py upload --file post_작품전시.json --images photo1.jpg")
        print("  게시물 확인만   : python main.py verify --title '미술교습소'")
        print("  일괄 생성       : python main.py batch --count 10")
        print_divider()
        print("지원 주제:")
        for topic in TOPIC_LIST:
            desc = TEMPLATES[topic]["titles"][0][:25]
            print(f"  {topic:<8} - {desc}...")


if __name__ == "__main__":
    asyncio.run(main())
