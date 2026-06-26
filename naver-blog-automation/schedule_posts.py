"""
정기 자동 게시 스케줄러
매일/주간 단위로 블로그 글 자동 생성 및 예약 게시
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from content_generator import generate_blog_post, BLOG_TOPICS
from naver_blog_poster import post_to_naver


WEEKLY_SCHEDULE = [
    {"day": 0, "hour": 9, "topic": "수업소개", "detail": "이번 주 미술 수업 커리큘럼 소개"},
    {"day": 2, "hour": 14, "topic": "작품전시", "detail": "학생들의 이번 주 완성 작품 공개"},
    {"day": 4, "hour": 10, "topic": "재료체험", "detail": "이번 주 특별 재료 체험 수업"},
]

MONTHLY_THEMES = [
    "수채화", "소묘", "공예", "계절수업", "전시회", "입시미술"
]

LOG_FILE = "schedule_log.json"


def load_log() -> list:
    if Path(LOG_FILE).exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_log(logs: list):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def log_post(title: str, topic: str, success: bool):
    logs = load_log()
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "title": title,
        "topic": topic,
        "success": success,
    })
    save_log(logs)


def get_todays_topic() -> dict:
    """오늘 요일에 맞는 스케줄 반환"""
    weekday = datetime.now().weekday()
    for schedule in WEEKLY_SCHEDULE:
        if schedule["day"] == weekday:
            return schedule
    month = datetime.now().month
    topic = MONTHLY_THEMES[(month - 1) % len(MONTHLY_THEMES)]
    return {"topic": topic, "detail": f"{datetime.now().month}월 {topic} 수업"}


async def run_scheduled_post(
    image_dir: str = None,
    headless: bool = True,
    dry_run: bool = False,
):
    """스케줄에 따른 자동 게시 실행"""
    schedule = get_todays_topic()
    topic = schedule["topic"]
    detail = schedule.get("detail", "")

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 자동 게시 시작")
    print(f"주제: {topic} - {detail}")

    image_paths = []
    if image_dir:
        img_dir = Path(image_dir)
        if img_dir.exists():
            extensions = [".jpg", ".jpeg", ".png", ".webp"]
            today = datetime.now().strftime("%Y%m%d")
            for ext in extensions:
                found = list(img_dir.glob(f"*{today}*{ext}")) + list(img_dir.glob(f"*{ext}"))
                image_paths.extend([str(p) for p in found[:3]])
            image_paths = list(dict.fromkeys(image_paths))[:4]

    image_descs = [f"사진{i+1}: {Path(p).name}" for i, p in enumerate(image_paths)]

    post = generate_blog_post(
        topic_key=topic,
        class_detail=detail,
        image_descriptions=image_descs if image_descs else None,
    )

    print(f"생성된 제목: {post['title']}")

    if dry_run:
        print("[DRY RUN] 실제 게시하지 않음")
        save_path = f"scheduled_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(post, f, ensure_ascii=False, indent=2)
        print(f"저장: {save_path}")
        return True

    success = await post_to_naver(
        title=post["title"],
        content=post["content"],
        tags=post["tags"],
        image_paths=image_paths if image_paths else None,
        publish_now=True,
        headless=headless,
    )

    log_post(post["title"], topic, success)

    if success:
        print("✅ 자동 게시 성공!")
    else:
        print("❌ 자동 게시 실패 - 로그 확인 필요")

    return success


async def run_daily_loop(
    post_hour: int = 9,
    image_dir: str = None,
    headless: bool = True,
):
    """매일 지정 시각에 자동 게시하는 루프"""
    print(f"자동 게시 스케줄러 시작 - 매일 {post_hour:02d}:00 게시")
    print("종료하려면 Ctrl+C를 누르세요.\n")

    while True:
        now = datetime.now()
        target = now.replace(hour=post_hour, minute=0, second=0, microsecond=0)

        if now >= target:
            target += timedelta(days=1)

        wait_sec = (target - now).total_seconds()
        print(f"다음 게시 예정: {target.strftime('%Y-%m-%d %H:%M')} ({wait_sec/3600:.1f}시간 후)")

        await asyncio.sleep(wait_sec)

        await run_scheduled_post(image_dir=image_dir, headless=headless)

        await asyncio.sleep(60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="블로그 자동 게시 스케줄러")
    parser.add_argument("--once", action="store_true", help="지금 바로 1회 게시")
    parser.add_argument("--dry-run", action="store_true", help="실제 게시 없이 글만 생성")
    parser.add_argument("--hour", type=int, default=9, help="매일 게시 시각 (기본: 9시)")
    parser.add_argument("--image-dir", help="오늘 사진이 저장된 폴더 경로")
    parser.add_argument("--headless", action="store_true", help="브라우저 숨김 모드")
    args = parser.parse_args()

    if args.once or args.dry_run:
        asyncio.run(
            run_scheduled_post(
                image_dir=args.image_dir,
                headless=args.headless,
                dry_run=args.dry_run,
            )
        )
    else:
        asyncio.run(
            run_daily_loop(
                post_hour=args.hour,
                image_dir=args.image_dir,
                headless=args.headless,
            )
        )
