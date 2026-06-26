# 미술교습소 네이버 블로그 자동화

Claude AI로 미술교습소 광고형 블로그 글을 자동 생성하고 네이버에 게시하는 프로그램

---

## 기능

| 기능 | 설명 |
|---|---|
| AI 글 자동 생성 | Claude Opus로 SEO 최적화 광고형 블로그 글 생성 |
| 사진 첨부 | 여러 사진 자동 업로드 |
| 네이버 자동 게시 | Playwright로 네이버 블로그 자동 포스팅 |
| 정기 자동화 | 매일 지정 시각 자동 게시 |
| 태그 자동 생성 | 네이버 검색 최적화 해시태그 10~15개 |

---

## 설치

```bash
cd naver-blog-automation
pip install -r requirements.txt
playwright install chromium
```

---

## 환경 설정

`.env.example`을 `.env`로 복사하고 값을 채우세요:

```bash
cp .env.example .env
```

```
ANTHROPIC_API_KEY=sk-ant-...      # Claude API 키
NAVER_ID=내아이디                  # 네이버 아이디
NAVER_PW=내비밀번호                # 네이버 비밀번호

ART_SCHOOL_NAME=OO미술교습소
ART_SCHOOL_LOCATION=서울시 강남구 역삼동
ART_SCHOOL_PHONE=010-1234-5678
ART_SCHOOL_AGE_TARGET=5세~중학생
```

---

## 사용법

### 1. 글만 생성 (게시 안함)

```bash
python main.py generate --topic 작품전시 --detail "이번 주 수묵화 체험"
```

### 2. 글 생성 + 네이버 게시

```bash
# 사진 없이 게시
python main.py post --topic 수업소개

# 사진 포함 게시
python main.py post --topic 작품전시 --images photo1.jpg photo2.jpg photo3.jpg

# 임시저장만 (직접 확인 후 발행)
python main.py post --topic 수업소개 --draft
```

### 3. 저장된 글 게시

```bash
python main.py upload --file output.json --images photo1.jpg
```

### 4. 여러 글 일괄 생성

```bash
python main.py batch --count 10 --output-dir 이번주_글
```

### 5. 매일 자동 게시 (스케줄러)

```bash
# 매일 오전 9시 자동 게시
python schedule_posts.py --hour 9 --image-dir ./오늘사진/

# 지금 바로 1회 게시
python schedule_posts.py --once --image-dir ./오늘사진/

# 실제 게시 없이 글만 생성 (테스트)
python schedule_posts.py --dry-run
```

---

## 지원 주제

| 주제 키 | 설명 |
|---|---|
| `수업소개` | 미술 수업 내용과 커리큘럼 소개 |
| `작품전시` | 학생들의 완성 작품 공개 |
| `재료체험` | 특별한 미술 재료 체험 수업 |
| `전시회` | 원내 미술 전시회 후기 |
| `계절수업` | 계절/테마 특별 수업 |
| `수채화` | 수채화 기초부터 심화까지 |
| `소묘` | 소묘·크로키 수업 |
| `공예` | 클레이·공예 수업 |
| `입시미술` | 중고등 입시미술 준비 |

---

## 주의사항

1. **네이버 로그인**: 2단계 인증이나 보안 설정에 따라 수동 로그인이 필요할 수 있음
2. **자동화 제한**: 네이버는 봇 감지 시스템이 있으므로 `--headless` 모드는 처음에 사용 금지 권장
3. **게시 빈도**: 하루 1~2개 이상 자동 게시 시 계정 제한 위험 있음
4. **사진 저작권**: 업로드 사진은 직접 촬영한 수업 사진 사용 권장

---

## 파일 구조

```
naver-blog-automation/
├── main.py               # 메인 실행 파일
├── content_generator.py  # Claude AI 글 생성
├── naver_blog_poster.py  # 네이버 자동 게시
├── schedule_posts.py     # 정기 자동화 스케줄러
├── requirements.txt      # 패키지 목록
├── .env.example          # 환경변수 예시
└── README.md
```
