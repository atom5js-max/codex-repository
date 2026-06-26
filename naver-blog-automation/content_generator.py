"""
미술교습소 네이버 블로그 콘텐츠 자동 생성기
Claude API를 사용하여 SEO 최적화된 광고형 블로그 글 생성
"""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SCHOOL_NAME = os.environ.get("ART_SCHOOL_NAME", "OO미술교습소")
SCHOOL_LOCATION = os.environ.get("ART_SCHOOL_LOCATION", "서울시 OO구 OO동")
SCHOOL_PHONE = os.environ.get("ART_SCHOOL_PHONE", "010-0000-0000")
AGE_TARGET = os.environ.get("ART_SCHOOL_AGE_TARGET", "5세~중학생")

BLOG_TOPICS = {
    "수업소개": "미술 수업 내용과 커리큘럼 소개",
    "작품전시": "학생들의 완성 작품 공개",
    "재료체험": "특별한 미술 재료 체험 수업",
    "전시회": "원내 미술 전시회 후기",
    "계절수업": "계절/테마 특별 수업",
    "수채화": "수채화 기초부터 심화까지",
    "소묘": "소묘·크로키 수업",
    "공예": "클레이·공예 수업",
    "입시미술": "중고등 입시미술 준비",
}


def generate_blog_post(
    topic_key: str,
    class_detail: str = "",
    image_descriptions: list[str] = None,
    custom_keywords: list[str] = None,
) -> dict:
    """
    미술교습소 블로그 글 생성

    Args:
        topic_key: BLOG_TOPICS의 키값 (예: "수업소개", "작품전시")
        class_detail: 수업 상세 내용 (예: "이번 주 수묵화 체험 수업")
        image_descriptions: 첨부 사진 설명 목록
        custom_keywords: 추가 SEO 키워드

    Returns:
        {"title": str, "content": str, "tags": list[str]}
    """
    topic_desc = BLOG_TOPICS.get(topic_key, topic_key)
    image_info = ""
    if image_descriptions:
        image_info = "\n첨부 사진:\n" + "\n".join(
            f"- {desc}" for desc in image_descriptions
        )

    keywords = [
        SCHOOL_LOCATION.split("시")[1].split("구")[0].strip() + "구미술학원" if "구" in SCHOOL_LOCATION else "미술학원",
        SCHOOL_LOCATION.split("구")[0].split("시")[-1].strip() + "미술교습소" if "시" in SCHOOL_LOCATION else "미술교습소",
        "어린이미술",
        "유아미술",
        "초등미술",
        f"{AGE_TARGET} 미술",
    ]
    if custom_keywords:
        keywords.extend(custom_keywords)

    prompt = f"""당신은 미술교습소 네이버 블로그 전문 마케터입니다.
네이버 검색 노출에 최적화된 광고형 블로그 글을 작성해주세요.

[미술교습소 정보]
- 이름: {SCHOOL_NAME}
- 위치: {SCHOOL_LOCATION}
- 대상: {AGE_TARGET}
- 전화: {SCHOOL_PHONE}
- 주제: {topic_desc}
- 수업 내용: {class_detail if class_detail else "일반 수업"}
{image_info}

[SEO 키워드 (자연스럽게 3~5회 포함)]
{', '.join(keywords)}

[작성 규칙]
1. 제목: 검색 키워드 포함, 감성적이고 클릭 유도형 (30자 이내)
2. 도입부: 공감형 첫 문장으로 독자 관심 유도
3. 본문 구성:
   - 소제목 3~4개 (## 사용)
   - 각 섹션 150~200자
   - 사진 삽입 위치 표시: [사진1], [사진2] 등
   - 이모지 적절히 활용
4. 수업 효과/특징 강조 (창의력, 집중력, 자신감 등)
5. 체험/후기 형식으로 진정성 있게
6. 마무리: 상담 유도 CTA (전화번호 포함)
7. 해시태그: 10~15개 (네이버 검색 최적화)
8. 전체 길이: 800~1200자

JSON 형식으로 반환:
{{
  "title": "블로그 제목",
  "content": "본문 전체 (마크다운 형식)",
  "tags": ["태그1", "태그2", ...]
}}"""

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2000,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    import re

    raw = ""
    for block in message.content:
        if block.type == "text":
            raw = block.text
            break

    json_match = re.search(r"\{[\s\S]*\}", raw)
    if json_match:
        return json.loads(json_match.group())

    return {"title": "미술교습소 블로그", "content": raw, "tags": keywords}


def generate_multiple_posts(count: int = 5) -> list[dict]:
    """다양한 주제로 여러 블로그 글 일괄 생성"""
    import random

    topics = list(BLOG_TOPICS.keys())
    posts = []

    for i in range(count):
        topic = topics[i % len(topics)]
        print(f"[{i+1}/{count}] '{topic}' 주제 글 생성 중...")
        post = generate_blog_post(topic_key=topic)
        posts.append(post)
        print(f"  제목: {post['title']}")

    return posts


if __name__ == "__main__":
    print("=== 미술교습소 블로그 글 생성 테스트 ===\n")

    post = generate_blog_post(
        topic_key="작품전시",
        class_detail="이번 주 수묵화 체험 수업에서 아이들이 멋진 작품을 완성했어요",
        image_descriptions=["아이들이 붓으로 그림 그리는 모습", "완성된 수묵화 작품들"],
        custom_keywords=["수묵화체험", "어린이수묵화"],
    )

    print(f"제목: {post['title']}\n")
    print(f"본문:\n{post['content']}\n")
    print(f"태그: {', '.join(post['tags'])}")
