"""
네이버 블로그 자동화 메인 실행 파일
미술교습소 광고형 블로그 글 생성 + 자동 게시
"""

import asyncio
import argparse
import json
from pathlib import Path

from content_generator import generate_blog_post, generate_multiple_posts, BLOG_TOPICS
from naver_blog_poster import post_to_naver


def parse_args():
    parser = argparse.ArgumentParser(description="미술교습소 네이버 블로그 자동화")
    subparsers = parser.add_subparsers(dest="command", help="실행 명령")

    # 글 생성만 하기
    gen = subparsers.add_parser("generate", help="블로그 글 생성 (게시 안함)")
    gen.add_argument("--topic", choices=list(BLOG_TOPICS.keys()), default="수업소개", help="블로그 주제")
    gen.add_argument("--detail", default="", help="수업 상세 내용")
    gen.add_argument("--keywords", nargs="+", help="추가 SEO 키워드")
    gen.add_argument("--images", nargs="+", help="사진 파일 경로")
    gen.add_argument("--output", default="output.json", help="결과 저장 파일명")

    # 글 생성 + 게시
    post = subparsers.add_parser("post", help="블로그 글 생성 후 네이버에 게시")
    post.add_argument("--topic", choices=list(BLOG_TOPICS.keys()), default="수업소개", help="블로그 주제")
    post.add_argument("--detail", default="", help="수업 상세 내용")
    post.add_argument("--keywords", nargs="+", help="추가 SEO 키워드")
    post.add_argument("--images", nargs="+", help="사진 파일 경로 (여러 개 가능)")
    post.add_argument("--draft", action="store_true", help="임시저장만 (게시 안함)")
    post.add_argument("--headless", action="store_true", help="브라우저 숨김 모드")

    # 기존 JSON으로 게시
    upload = subparsers.add_parser("upload", help="저장된 JSON 파일로 네이버에 게시")
    upload.add_argument("--file", required=True, help="업로드할 JSON 파일")
    upload.add_argument("--images", nargs="+", help="사진 파일 경로")
    upload.add_argument("--draft", action="store_true", help="임시저장만")
    upload.add_argument("--headless", action="store_true", help="브라우저 숨김 모드")

    # 여러 글 일괄 생성
    batch = subparsers.add_parser("batch", help="여러 주제로 블로그 글 일괄 생성")
    batch.add_argument("--count", type=int, default=5, help="생성할 글 수")
    batch.add_argument("--output-dir", default="batch_output", help="결과 저장 폴더")

    return parser.parse_args()


def save_post(post: dict, filename: str):
    """글 내용을 JSON으로 저장"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {filename}")


def print_post_preview(post: dict):
    """글 미리보기 출력"""
    print("\n" + "=" * 60)
    print(f"제목: {post['title']}")
    print("=" * 60)
    print(post["content"][:500] + "..." if len(post["content"]) > 500 else post["content"])
    print("\n태그:", ", ".join(post["tags"][:5]) + f"... 외 {max(0, len(post['tags'])-5)}개")
    print("=" * 60)


async def cmd_generate(args):
    """글 생성 명령"""
    print(f"\n[주제: {args.topic}] 블로그 글 생성 중...\n")

    image_descs = []
    if args.images:
        for i, img in enumerate(args.images, 1):
            image_descs.append(f"사진{i}: {Path(img).name}")

    post = generate_blog_post(
        topic_key=args.topic,
        class_detail=args.detail,
        image_descriptions=image_descs if image_descs else None,
        custom_keywords=args.keywords,
    )

    print_post_preview(post)
    save_post(post, args.output)
    return post


async def cmd_post(args):
    """글 생성 + 게시 명령"""
    print(f"\n[주제: {args.topic}] 블로그 글 생성 중...\n")

    image_descs = []
    if args.images:
        for i, img in enumerate(args.images, 1):
            image_descs.append(f"사진{i}: {Path(img).name}")

    post = generate_blog_post(
        topic_key=args.topic,
        class_detail=args.detail,
        image_descriptions=image_descs if image_descs else None,
        custom_keywords=args.keywords,
    )

    print_post_preview(post)

    print("\n네이버 블로그에 게시 중...")
    success = await post_to_naver(
        title=post["title"],
        content=post["content"],
        tags=post["tags"],
        image_paths=args.images,
        publish_now=not args.draft,
        headless=args.headless,
    )

    if success:
        print("\n✅ 블로그 게시 성공!")
        save_post(post, f"posted_{args.topic}.json")
    else:
        print("\n❌ 게시 실패. 생성된 글을 파일로 저장합니다.")
        save_post(post, f"failed_{args.topic}.json")


async def cmd_upload(args):
    """JSON 파일로 게시 명령"""
    post_file = Path(args.file)
    if not post_file.exists():
        print(f"파일 없음: {args.file}")
        return

    with open(post_file, encoding="utf-8") as f:
        post = json.load(f)

    print_post_preview(post)

    print("\n네이버 블로그에 게시 중...")
    success = await post_to_naver(
        title=post["title"],
        content=post["content"],
        tags=post.get("tags", []),
        image_paths=args.images,
        publish_now=not args.draft,
        headless=args.headless,
    )

    if success:
        print("\n✅ 블로그 게시 성공!")
    else:
        print("\n❌ 게시 실패.")


async def cmd_batch(args):
    """일괄 생성 명령"""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print(f"\n{args.count}개의 블로그 글 일괄 생성 중...\n")
    posts = generate_multiple_posts(args.count)

    for i, post in enumerate(posts, 1):
        filename = output_dir / f"post_{i:02d}.json"
        save_post(post, str(filename))

    print(f"\n✅ {len(posts)}개 글 생성 완료! 저장 위치: {output_dir}/")

    summary_file = output_dir / "summary.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        for i, post in enumerate(posts, 1):
            f.write(f"{i}. {post['title']}\n")
    print(f"목록 저장: {summary_file}")


async def main():
    args = parse_args()

    if args.command == "generate":
        await cmd_generate(args)
    elif args.command == "post":
        await cmd_post(args)
    elif args.command == "upload":
        await cmd_upload(args)
    elif args.command == "batch":
        await cmd_batch(args)
    else:
        print("명령을 선택하세요. --help 참고")
        print("\n[사용 예시]")
        print("  글 생성만:        python main.py generate --topic 작품전시 --detail '수묵화 수업'")
        print("  글 생성+게시:     python main.py post --topic 수업소개 --images photo1.jpg photo2.jpg")
        print("  저장된 글 게시:   python main.py upload --file output.json --images photo1.jpg")
        print("  일괄 생성:        python main.py batch --count 10")
        print("\n[지원 주제]")
        for key, desc in BLOG_TOPICS.items():
            print(f"  {key}: {desc}")


if __name__ == "__main__":
    asyncio.run(main())
