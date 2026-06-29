# 미술교습소 네이버 블로그 자동화 (API 없는 버전)

외부 API 없이 템플릿 기반으로 블로그 글을 자동 생성하고,
네이버 블로그에 자동 게시한 뒤 게시물까지 확인하는 프로그램

---

## 기능

| 기능 | 설명 |
|---|---|
| 글 자동 생성 | 8가지 주제별 SEO 최적화 템플릿 |
| 사진 첨부 | 여러 사진 자동 업로드 |
| 네이버 자동 게시 | Playwright 브라우저 자동화 |
| **게시물 확인** | 게시 후 블로그에서 게시물 존재 확인 + 스크린샷 |
| 태그 자동 생성 | 지역명 포함 네이버 검색 최적화 태그 10개 |
| 일괄 생성 | 여러 주제 글 한꺼번에 생성 |

---

## 설치

```bash
cd naver-blog-automation
pip install -r requirements.txt
playwright install chromium
```

---

## 환경 설정

```bash
cp .env.example .env
```

`.env` 파일 편집:

```
NAVER_ID=내아이디
NAVER_PW=내비밀번호

ART_SCHOOL_NAME=OO미술교습소
ART_SCHOOL_LOCATION=서울시 강남구 역삼동
ART_SCHOOL_PHONE=010-1234-5678
ART_SCHOOL_AGE_TARGET=5세~중학생
```

---

## 사용법

### 1. 글만 생성 (게시 안함, 파일로 저장)

```bash
python main.py generate --topic 작품전시 --detail "이번 주 수묵화 체험"
```

### 2. 글 생성 + 게시 + 확인 (핵심)

```bash
# 사진 없이
python main.py post --topic 수업소개

# 사진 포함 (여러 장 가능)
python main.py post --topic 작품전시 --images photo1.jpg photo2.jpg photo3.jpg

# 임시저장 (발행 전 검토용)
python main.py post --topic 수업소개 --draft

# 브라우저 숨김 모드
python main.py post --topic 수업소개 --headless
```

### 3. 저장된 파일로 게시 + 확인

```bash
python main.py upload --file post_작품전시_20260626.json --images photo1.jpg
```

### 4. 게시물 확인만

```bash
python main.py verify --title "미술교습소"
```

### 5. 일괄 생성 (10개 주제 자동 생성)

```bash
python main.py batch --count 10 --out-dir 이번주글
```

---

## 지원 주제 8가지

| 키 | 내용 |
|---|---|
| `수업소개` | 수업 커리큘럼 광고 |
| `작품전시` | 학생 작품 공개 |
| `재료체험` | 특별 재료 체험 수업 |
| `수채화` | 수채화 수업 소개 |
| `소묘` | 소묘·크로키 수업 |
| `공예` | 클레이·공예 수업 |
| `입시미술` | 중고등 입시미술 준비 |
| `계절수업` | 계절/테마 특별 수업 |
| `전시회` | 원내 전시회 후기 |

---

## 게시물 확인 방법

게시 완료 후 자동으로 다음을 수행합니다:

1. 블로그 페이지 이동
2. 최신 게시물 목록에서 제목 검색
3. URL 추출 및 출력
4. `screenshots/` 폴더에 스크린샷 3장 저장
   - `01_write_page_*.png` - 글쓰기 화면
   - `02_before_publish_*.png` - 발행 전
   - `03_after_publish_*.png` - 발행 후
   - `verify_*.png` - 블로그 확인 화면

---

## 파일 구조

```
naver-blog-automation/
├── main.py               ← 메인 실행 파일
├── template_generator.py ← 템플릿 기반 글 생성 (API 불필요)
├── naver_blog_poster.py  ← 네이버 자동 게시 + 확인
├── requirements.txt
├── .env.example
├── screenshots/          ← 자동 생성 (스크린샷 저장)
└── README.md
```

---

## 주의사항

- **2단계 인증**: 네이버 계정에 2단계 인증이 설정된 경우, 브라우저 창에서 직접 인증 후 Enter 키를 누르면 계속 진행됩니다.
- **처음 실행**: `--headless` 없이 실행하여 로그인 과정을 직접 확인하세요.
- **게시 빈도**: 하루 1~2개 권장 (과다 자동화 시 계정 제한 위험).
- **스마트에디터**: 네이버 스마트에디터 ONE 기준으로 동작합니다.
