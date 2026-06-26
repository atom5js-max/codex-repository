"""
API 없는 템플릿 기반 미술교습소 블로그 글 생성기
외부 API 없이 다양한 템플릿으로 블로그 글 자동 생성
"""

import random
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

SCHOOL_NAME = os.environ.get("ART_SCHOOL_NAME", "OO미술교습소")
SCHOOL_LOCATION = os.environ.get("ART_SCHOOL_LOCATION", "서울시 OO구 OO동")
SCHOOL_PHONE = os.environ.get("ART_SCHOOL_PHONE", "010-0000-0000")
AGE_TARGET = os.environ.get("ART_SCHOOL_AGE_TARGET", "5세~중학생")

# 지역 키워드 추출
def _get_district() -> str:
    for sep in ["구 ", "구"]:
        if sep in SCHOOL_LOCATION:
            parts = SCHOOL_LOCATION.split(sep)
            for p in parts:
                if "시" in p:
                    return p.split("시")[-1].strip() + "구"
    return "우리동네"

DISTRICT = _get_district()

# ─────────────────────────────────────────────
#  주제별 템플릿 라이브러리
# ─────────────────────────────────────────────

TEMPLATES = {

    "수업소개": {
        "titles": [
            f"[{DISTRICT}미술] {SCHOOL_NAME} 이번 주 수업 커리큘럼 공개!",
            f"{DISTRICT} 아이들이 반한 미술 수업, {SCHOOL_NAME}에서 만나요",
            f"창의력 쑥쑥! {SCHOOL_NAME} 이번 주 미술 수업 소개",
            f"{SCHOOL_NAME} 수업 커리큘럼 대공개 - {AGE_TARGET} 모두 환영",
        ],
        "body": lambda detail, imgs: f"""안녕하세요, {SCHOOL_NAME}입니다! 🎨

이번 주도 아이들과 함께 알차고 즐거운 미술 수업을 진행했어요.
{detail if detail else '다양한 재료와 기법으로 창의력을 키우는 시간이었습니다!'}

{imgs[0] if imgs else '[사진1]'}

## 이번 주 수업 내용

저희 {SCHOOL_NAME}은 단순히 그림을 그리는 것에서 나아가,
아이들이 **스스로 생각하고 표현하는 능력**을 키울 수 있도록 지도합니다.

✅ 기초 드로잉부터 채색까지 단계별 지도
✅ 소규모 수업으로 1:1 맞춤 피드백
✅ 연령·수준별 맞춤 커리큘럼

{imgs[1] if len(imgs) > 1 else '[사진2]'}

## 우리 아이에게 맞는 수업이 있어요

{AGE_TARGET} 누구든 환영합니다!
처음 붓을 잡는 아이부터 심화 과정까지,
{SCHOOL_NAME}은 아이의 속도에 맞춰 함께 성장합니다.

{imgs[2] if len(imgs) > 2 else '[사진3]'}

## 수업 문의 & 체험 신청

📍 위치: {SCHOOL_LOCATION}
📞 상담: {SCHOOL_PHONE}
🕐 수업 시간: 월~토 (시간 협의 가능)

지금 바로 전화 주시면 **무료 체험 수업** 안내해 드립니다! 😊
""",
        "tags": [
            f"{DISTRICT}미술학원", f"{DISTRICT}미술교습소", "어린이미술", "유아미술",
            "초등미술", "미술수업", "창의미술", "아동미술", f"{SCHOOL_NAME}",
            "미술교습소", "소규모미술", "그림수업", "미술체험", "드로잉수업", "어린이미술학원"
        ],
    },

    "작품전시": {
        "titles": [
            f"우리 아이 작품 뽐내기! {SCHOOL_NAME} 이번 주 작품 공개 ✨",
            f"완성도 대박! {DISTRICT} {SCHOOL_NAME} 아이들 작품 모음",
            f"이렇게나 잘 그렸어요 🎨 {SCHOOL_NAME} 작품 전시",
            f"자랑스러운 우리 아이 작품! {SCHOOL_NAME} 갤러리",
        ],
        "body": lambda detail, imgs: f"""안녕하세요 {SCHOOL_NAME}입니다! 🖼️

이번 주도 아이들이 정성껏 완성한 작품들을 소개해드릴게요.
{detail if detail else '아이들의 창의력과 노력이 고스란히 담긴 작품들입니다!'}

{imgs[0] if imgs else '[사진1]'}

## 이번 주 완성 작품들

아이들이 집중해서 완성한 작품 하나하나가 정말 대단하지 않나요? 🥰
처음에는 '잘 못 그릴 것 같아요'라고 수줍어하던 아이들도,
완성 후에는 뿌듯한 표정이 얼굴 가득이에요!

{imgs[1] if len(imgs) > 1 else '[사진2]'}

## 작품 속에 담긴 이야기

미술은 단순히 그림 실력이 아니라,
아이들의 **생각과 감정을 표현**하는 소중한 언어입니다.

저희 {SCHOOL_NAME}에서는 완성도보다 **표현의 즐거움**을 먼저 가르칩니다.
그 결과 아이들이 스스로 그림을 즐기고, 자신감을 갖게 됩니다. 💪

{imgs[2] if len(imgs) > 2 else '[사진3]'}

## 내 아이도 함께해요!

📍 {SCHOOL_LOCATION}
📞 상담 & 체험 예약: {SCHOOL_PHONE}

**무료 체험 수업** 신청하시면 이런 멋진 작품을 직접 만들어볼 수 있어요! 🎨
""",
        "tags": [
            f"{DISTRICT}미술학원", "어린이작품", "미술작품", "아동미술작품", f"{SCHOOL_NAME}",
            "어린이미술", "창의미술", "미술교습소", f"{DISTRICT}미술교습소",
            "유아미술작품", "초등미술작품", "미술전시", "아동창의력", "그림그리기", "미술수업"
        ],
    },

    "재료체험": {
        "titles": [
            f"오늘은 특별한 재료로! {SCHOOL_NAME} 체험 수업 현장",
            f"이런 재료 처음이야~ {DISTRICT} {SCHOOL_NAME} 특별 체험",
            f"아이들 눈이 반짝반짝! {SCHOOL_NAME} 재료 체험 수업",
            f"새로운 재료의 매력 🎨 {SCHOOL_NAME} 특별 수업 공개",
        ],
        "body": lambda detail, imgs: f"""안녕하세요 {SCHOOL_NAME}입니다! 🎨

오늘은 평소와 다른 **특별한 재료**로 수업을 진행했어요!
{detail if detail else '아이들이 처음 접하는 재료에 눈을 반짝이며 집중했습니다!'}

{imgs[0] if imgs else '[사진1]'}

## 오늘의 특별 재료

새로운 재료를 처음 만지는 아이들의 표정이 정말 귀여웠어요. 😊
"선생님, 이게 뭐예요?" 하면서 호기심 어린 눈으로 탐색하는 모습!

다양한 재료를 경험하면서 아이들은
**감각 발달**과 **창의적 표현력**을 동시에 키워나갑니다.

{imgs[1] if len(imgs) > 1 else '[사진2]'}

## 체험 수업의 효과

🌟 오감 자극으로 두뇌 발달 촉진
🌟 다양한 재료로 표현의 폭 확대
🌟 재미있는 수업으로 미술에 대한 흥미 UP!
🌟 완성의 성취감으로 자신감 향상

{imgs[2] if len(imgs) > 2 else '[사진3]'}

## 다음 특별 수업도 기대해주세요!

📍 {SCHOOL_LOCATION}
📞 수업 문의: {SCHOOL_PHONE}

체험 수업을 직접 경험하고 싶으시다면 언제든지 연락주세요! 🙌
""",
        "tags": [
            f"{DISTRICT}미술학원", "미술체험", "어린이체험", f"{SCHOOL_NAME}",
            "재료체험", "창의미술", "어린이미술", "미술교습소", "아동미술체험",
            f"{DISTRICT}미술교습소", "유아미술", "초등미술", "특별수업", "감각놀이", "오감체험"
        ],
    },

    "수채화": {
        "titles": [
            f"물감이 번지는 마법! {SCHOOL_NAME} 수채화 수업",
            f"감성 뚝뚝! {DISTRICT} {SCHOOL_NAME} 수채화 작품 공개",
            f"아이들이 만든 수채화 작품 🌈 {SCHOOL_NAME}",
            f"투명하고 맑은 수채화의 세계 - {SCHOOL_NAME}",
        ],
        "body": lambda detail, imgs: f"""안녕하세요 {SCHOOL_NAME}입니다! 🎨

오늘은 **수채화 수업** 현장을 소개해드릴게요.
{detail if detail else '물감이 물과 만나 번지는 아름다운 수채화의 세계로 아이들을 안내했습니다!'}

{imgs[0] if imgs else '[사진1]'}

## 수채화의 매력

수채화는 물과 물감이 만나 예상치 못한 아름다운 효과를 만들어냅니다.
아이들은 이 과정에서 **자연스러운 표현**을 배우고
결과를 예측하고 조절하는 **관찰력**도 키워나가요.

{imgs[1] if len(imgs) > 1 else '[사진2]'}

## 수채화 수업에서 배우는 것들

✏️ 기본 붓 사용법과 물 조절
🎨 색의 혼합과 번짐 효과 이해
🌟 명암과 원근감 표현
💡 나만의 색감 찾기

{imgs[2] if len(imgs) > 2 else '[사진3]'}

## 수채화 수업 문의

📍 {SCHOOL_LOCATION}
📞 상담 전화: {SCHOOL_PHONE}

수채화를 처음 접하는 아이도 괜찮아요!
기초부터 차근차근 알려드립니다. 😊
""",
        "tags": [
            f"{DISTRICT}미술학원", "수채화수업", "어린이수채화", f"{SCHOOL_NAME}",
            "수채화", "미술교습소", f"{DISTRICT}미술교습소", "어린이미술",
            "수채화그리기", "초등수채화", "유아수채화", "수채화체험", "미술수업", "그림수업", "아동미술"
        ],
    },

    "소묘": {
        "titles": [
            f"선 하나로 완성되는 예술! {SCHOOL_NAME} 소묘 수업",
            f"집중력 UP! {DISTRICT} {SCHOOL_NAME} 소묘·크로키 수업",
            f"데생의 기초부터! {SCHOOL_NAME} 소묘 수업 공개",
            f"연필 한 자루로 만드는 작품 - {SCHOOL_NAME} 소묘",
        ],
        "body": lambda detail, imgs: f"""안녕하세요 {SCHOOL_NAME}입니다! ✏️

오늘은 **소묘 수업** 현장을 소개해드릴게요.
{detail if detail else '연필 한 자루로 표현하는 소묘의 매력에 아이들이 푹 빠졌습니다!'}

{imgs[0] if imgs else '[사진1]'}

## 소묘, 왜 중요할까요?

소묘(데생)는 모든 미술의 기초입니다.
선을 다루는 능력, 명암을 이해하는 눈,
비례와 형태를 파악하는 감각이 모두 소묘에서 시작됩니다.

✅ 집중력과 관찰력 향상
✅ 손과 눈의 협응력 발달
✅ 입시미술의 탄탄한 기초

{imgs[1] if len(imgs) > 1 else '[사진2]'}

## 수업 진행 방식

저희는 딱딱하지 않게, 재미있는 소재로 소묘를 가르칩니다.
좋아하는 사물, 캐릭터, 자연물 등 아이들이 직접 그리고 싶은 것을 골라
선생님과 함께 표현해나가요!

{imgs[2] if len(imgs) > 2 else '[사진3]'}

## 소묘 수업 문의

📍 {SCHOOL_LOCATION}
📞 상담: {SCHOOL_PHONE}

기초 소묘부터 입시 데생까지, {SCHOOL_NAME}에서 함께해요! 🎯
""",
        "tags": [
            f"{DISTRICT}미술학원", "소묘수업", "데생", "크로키", f"{SCHOOL_NAME}",
            "어린이소묘", "미술교습소", f"{DISTRICT}미술교습소", "미술기초",
            "연필드로잉", "초등미술", "입시미술기초", "미술수업", "아동미술", "그림연습"
        ],
    },

    "공예": {
        "titles": [
            f"손으로 만드는 즐거움! {SCHOOL_NAME} 공예 수업",
            f"클레이로 뭐든 만들 수 있어요 🌟 {SCHOOL_NAME}",
            f"아이들 작품이 이렇게나! {DISTRICT} {SCHOOL_NAME} 공예 수업",
            f"만들기 대장 등극! {SCHOOL_NAME} 클레이·공예 수업",
        ],
        "body": lambda detail, imgs: f"""안녕하세요 {SCHOOL_NAME}입니다! 🏺

오늘은 **공예 수업** 현장을 소개해드릴게요!
{detail if detail else '손으로 직접 만들어가는 공예 수업에 아이들이 신나게 참여했어요!'}

{imgs[0] if imgs else '[사진1]'}

## 오늘의 공예 수업

아이들이 손으로 직접 주무르고, 빚고, 꾸미는 과정에서
**소근육 발달**과 **공간감각**이 자연스럽게 키워집니다.

"선생님, 저 이거 집에 가져가도 돼요?" 하며
완성된 작품을 꼭 껴안는 아이들의 모습이 정말 사랑스러워요! 💕

{imgs[1] if len(imgs) > 1 else '[사진2]'}

## 공예 수업의 교육 효과

🙌 소근육 발달 및 손 협응력 향상
🧠 입체적 사고와 공간 감각 발달
😊 완성의 성취감으로 자존감 UP
🎯 집중력과 인내심 향상

{imgs[2] if len(imgs) > 2 else '[사진3]'}

## 수업 문의

📍 {SCHOOL_LOCATION}
📞 상담: {SCHOOL_PHONE}

클레이, 석고, 냅킨아트 등 다양한 공예 수업을 진행합니다!
언제든지 문의주세요 😊
""",
        "tags": [
            f"{DISTRICT}미술학원", "클레이수업", "공예수업", f"{SCHOOL_NAME}",
            "어린이공예", "미술교습소", f"{DISTRICT}미술교습소", "어린이클레이",
            "유아공예", "초등공예", "만들기수업", "소근육발달", "아동미술", "미술체험", "창의만들기"
        ],
    },

    "입시미술": {
        "titles": [
            f"입시미술 이제 걱정 끝! {SCHOOL_NAME}에서 준비하세요",
            f"{DISTRICT} 입시미술 전문 {SCHOOL_NAME} - 합격의 지름길",
            f"미술고·예고 준비! {SCHOOL_NAME} 입시미술반 소개",
            f"실기부터 포트폴리오까지 {SCHOOL_NAME} 입시미술 완벽 가이드",
        ],
        "body": lambda detail, imgs: f"""안녕하세요 {SCHOOL_NAME}입니다! 🎯

입시미술을 준비하는 학생들을 위한 수업을 소개해드릴게요.
{detail if detail else '체계적인 커리큘럼으로 미술고, 예고 입시를 완벽하게 준비합니다!'}

{imgs[0] if imgs else '[사진1]'}

## {SCHOOL_NAME} 입시미술반 특징

입시미술은 단순한 그림 실력이 아니라
**전략적인 준비**가 필요합니다.

저희 {SCHOOL_NAME}은 각 학교별 입시 경향을 분석하여
맞춤형 지도를 제공합니다.

✅ 기초 소묘·수채화 탄탄히 잡기
✅ 학교별 실기 유형 맞춤 훈련
✅ 포트폴리오 제작 및 첨삭
✅ 모의 실기 테스트 정기 진행

{imgs[1] if len(imgs) > 1 else '[사진2]'}

## 합격 전략

미술 입시는 **꾸준함**이 답입니다.
일찍 시작할수록 여유 있게 준비할 수 있어요.

중학교 1학년부터 준비를 시작하면
3년간 체계적으로 실력을 쌓을 수 있습니다.

{imgs[2] if len(imgs) > 2 else '[사진3]'}

## 입시미술 상담 문의

📍 {SCHOOL_LOCATION}
📞 상담 전화: {SCHOOL_PHONE}

지금 바로 상담 신청하시면 **개인 맞춤 입시 로드맵**을 제공해드립니다! 📋
""",
        "tags": [
            f"{DISTRICT}입시미술", "미술입시", "예고입시", "미술고입시", f"{SCHOOL_NAME}",
            "입시미술학원", f"{DISTRICT}미술학원", "미술실기", "포트폴리오",
            "수채화입시", "소묘입시", "중등미술", "미술교습소", "예술고등학교", "미술대입"
        ],
    },

    "계절수업": {
        "titles": [
            f"이 계절만의 특별함! {SCHOOL_NAME} 테마 수업",
            f"계절을 담은 미술 수업 🍂 {SCHOOL_NAME}",
            f"자연에서 배우는 미술! {DISTRICT} {SCHOOL_NAME} 계절 수업",
            f"이번 계절엔 이 수업! {SCHOOL_NAME} 특별 테마 공개",
        ],
        "body": lambda detail, imgs: f"""안녕하세요 {SCHOOL_NAME}입니다! 🌿

이번 계절을 주제로 특별한 수업을 진행했어요!
{detail if detail else '계절의 색깔과 느낌을 담은 특별한 미술 시간이었습니다!'}

{imgs[0] if imgs else '[사진1]'}

## 이번 계절 테마 수업

자연은 최고의 미술 선생님입니다.
계절마다 달라지는 색깔, 모양, 분위기를 느끼고 표현하는 것이
아이들의 **감성과 관찰력**을 키워줍니다.

{imgs[1] if len(imgs) > 1 else '[사진2]'}

## 계절 수업 특별 포인트

🌈 계절에 맞는 재료와 기법 활용
🍃 자연물을 활용한 실감나는 표현
✨ 계절 감성이 담긴 나만의 작품 완성
📸 완성 작품으로 소중한 추억 만들기

{imgs[2] if len(imgs) > 2 else '[사진3]'}

## 다음 특별 수업도 기다려주세요!

📍 {SCHOOL_LOCATION}
📞 문의: {SCHOOL_PHONE}

매 계절마다 새로운 테마 수업을 진행합니다.
지금 바로 신청하세요! 🌟
""",
        "tags": [
            f"{DISTRICT}미술학원", "계절미술", "테마수업", f"{SCHOOL_NAME}",
            "어린이미술", "미술교습소", f"{DISTRICT}미술교습소", "자연미술",
            "창의미술", "유아미술", "초등미술", "특별수업", "계절테마", "아동미술", "미술수업"
        ],
    },

    "전시회": {
        "titles": [
            f"우리 아이들의 작품 세상! {SCHOOL_NAME} 전시회 후기",
            f"꼬마 작가들의 전시 🖼️ {SCHOOL_NAME} 발표회",
            f"감동 그 자체! {DISTRICT} {SCHOOL_NAME} 미술 전시회",
            f"아이들의 1년을 담은 전시 - {SCHOOL_NAME}",
        ],
        "body": lambda detail, imgs: f"""안녕하세요 {SCHOOL_NAME}입니다! 🎊

드디어 기다리던 **미술 전시회**가 열렸어요!
{detail if detail else '아이들이 정성껏 준비한 작품들을 선보이는 뜻깊은 자리였습니다!'}

{imgs[0] if imgs else '[사진1]'}

## 전시회 현장 속으로

아이들이 직접 꾸민 전시 공간에는
몇 달 동안의 노력과 열정이 가득 담겨 있었어요.

부모님들께서 아이들의 작품 앞에서 환하게 웃으시는 모습,
아이들이 자기 작품을 뿌듯하게 소개하는 모습이
정말 감동적이었습니다. 🥹

{imgs[1] if len(imgs) > 1 else '[사진2]'}

## 전시회를 통해 배우는 것들

🌟 자신의 작품에 대한 자신감과 자존감
🌟 다른 친구들의 작품을 보며 배우는 배려심
🌟 완성과 발표의 경험으로 성취감 UP
🌟 소중한 추억과 포트폴리오 자산

{imgs[2] if len(imgs) > 2 else '[사진3]'}

## 다음 전시회도 기대해주세요!

📍 {SCHOOL_LOCATION}
📞 입학 문의: {SCHOOL_PHONE}

{SCHOOL_NAME}에서 우리 아이도 꼬마 작가가 될 수 있어요! 🎨
""",
        "tags": [
            f"{DISTRICT}미술학원", "미술전시회", "어린이전시", f"{SCHOOL_NAME}",
            "아동미술전시", "미술교습소", f"{DISTRICT}미술교습소", "어린이미술",
            "미술발표회", "유아전시회", "초등전시회", "작품전시", "미술수업", "창의미술", "꼬마작가"
        ],
    },
}


def generate_blog_post(
    topic_key: str,
    class_detail: str = "",
    image_paths: list = None,
    custom_tags: list = None,
) -> dict:
    """
    블로그 글 생성 (API 없음)

    Args:
        topic_key: TEMPLATES의 키값
        class_detail: 수업 상세 내용 (없으면 기본 문구 사용)
        image_paths: 첨부 이미지 경로 목록
        custom_tags: 추가 태그

    Returns:
        {"title": str, "content": str, "tags": list[str]}
    """
    if topic_key not in TEMPLATES:
        topic_key = "수업소개"

    tmpl = TEMPLATES[topic_key]

    title = random.choice(tmpl["titles"])

    now = datetime.now()
    month_day = f"{now.month}월 {now.day}일"
    detail = class_detail or f"{month_day} {topic_key} 수업"

    img_placeholders = []
    if image_paths:
        for i in range(len(image_paths)):
            img_placeholders.append(f"[사진{i+1}]")
    else:
        img_placeholders = ["[사진1]", "[사진2]", "[사진3]"]

    content = tmpl["body"](detail, img_placeholders)

    tags = list(tmpl["tags"])
    if custom_tags:
        tags = list(dict.fromkeys(tags + custom_tags))

    return {
        "title": title,
        "content": content,
        "tags": tags[:15],
        "topic": topic_key,
    }


TOPIC_LIST = list(TEMPLATES.keys())

if __name__ == "__main__":
    print("=== 템플릿 기반 블로그 글 생성 테스트 ===\n")
    for topic in TOPIC_LIST:
        post = generate_blog_post(topic_key=topic, class_detail="테스트 수업입니다")
        print(f"[{topic}] 제목: {post['title']}")
    print(f"\n총 {len(TOPIC_LIST)}개 주제 사용 가능")
