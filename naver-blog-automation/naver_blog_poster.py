"""
네이버 블로그 자동 포스팅 + 게시물 확인 모듈
Playwright 브라우저 자동화 (외부 API 없음)
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, BrowserContext, Browser

load_dotenv()

NAVER_ID = os.environ.get("NAVER_ID", "")
NAVER_PW = os.environ.get("NAVER_PW", "")

SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)


class NaverBlogPoster:

    def __init__(self, headless: bool = False, slow_mo: int = 100):
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.posted_url: str = None

    # ─────────────────────── 브라우저 시작/종료 ───────────────────────

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            executable_path="/opt/pw-browsers/chromium",
            slow_mo=self.slow_mo,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ko-KR",
        )
        self.page = await self.context.new_page()
        # 봇 감지 우회
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

    async def stop(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _screenshot(self, name: str):
        path = SCREENSHOT_DIR / f"{name}_{datetime.now().strftime('%H%M%S')}.png"
        await self.page.screenshot(path=str(path))
        return str(path)

    # ─────────────────────── 로그인 ───────────────────────

    async def login(self) -> bool:
        print("▶ 네이버 로그인 중...")
        await self.page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")
        await asyncio.sleep(1)

        # ID 입력
        await self.page.click("#id")
        await asyncio.sleep(0.3)
        for char in NAVER_ID:
            await self.page.keyboard.type(char, delay=random_delay())
        await asyncio.sleep(0.5)

        # PW 입력
        await self.page.click("#pw")
        await asyncio.sleep(0.3)
        for char in NAVER_PW:
            await self.page.keyboard.type(char, delay=random_delay())
        await asyncio.sleep(0.5)

        await self.page.click(".btn_login")
        await asyncio.sleep(3)

        current_url = self.page.url

        if "nid.naver.com" in current_url:
            await self._screenshot("login_failed")
            if "2step" in current_url or "second" in current_url or "sms" in current_url.lower():
                print("  ⚠ 2단계 인증 필요 - 브라우저 창에서 직접 인증 완료 후 Enter 누르세요.")
                if not self.headless:
                    input("  인증 완료 후 Enter 키를 누르세요...")
                    await asyncio.sleep(2)
                else:
                    return False
            else:
                print("  ✗ 로그인 실패 (ID/PW 확인 또는 캡챠 발생)")
                return False

        print(f"  ✓ 로그인 성공 ({NAVER_ID})")
        return True

    # ─────────────────────── 글쓰기 페이지 이동 ───────────────────────

    async def go_to_write_page(self) -> bool:
        print("▶ 글쓰기 페이지 이동...")
        await self.page.goto(
            f"https://blog.naver.com/{NAVER_ID}",
            wait_until="domcontentloaded"
        )
        await asyncio.sleep(2)

        # 글쓰기 버튼 클릭 시도
        write_selectors = [
            "a.btn_write",
            "a[href*='PostWriteForm']",
            ".blog_write_btn",
            "a:has-text('글쓰기')",
        ]
        for sel in write_selectors:
            try:
                btn = self.page.locator(sel).first
                await btn.wait_for(timeout=3000)
                await btn.click()
                await asyncio.sleep(3)
                print("  ✓ 글쓰기 버튼 클릭")
                return True
            except Exception:
                pass

        # 직접 URL 이동
        await self.page.goto(
            "https://blog.naver.com/PostWriteForm.naver",
            wait_until="domcontentloaded"
        )
        await asyncio.sleep(3)

        if "PostWrite" in self.page.url or "blog.naver.com" in self.page.url:
            print("  ✓ 글쓰기 페이지 도달")
            return True

        print("  ✗ 글쓰기 페이지 이동 실패")
        return False

    # ─────────────────────── 제목 입력 ───────────────────────

    async def set_title(self, title: str):
        print(f"▶ 제목 입력: {title[:30]}...")
        selectors = [
            "input.se-title-input",
            "input[placeholder='제목']",
            ".se-title-text input",
            "#title",
        ]
        for sel in selectors:
            try:
                inp = self.page.locator(sel).first
                await inp.wait_for(timeout=5000)
                await inp.click()
                await asyncio.sleep(0.3)
                await inp.fill(title)
                await asyncio.sleep(0.5)
                print("  ✓ 제목 입력 완료")
                return
            except Exception:
                pass

        # 스마트에디터 내부 iframe에서 제목 시도
        try:
            frame = self.page.frame_locator("iframe").first
            inp = frame.locator("input[placeholder='제목'], .se-title-input").first
            await inp.wait_for(timeout=3000)
            await inp.fill(title)
            print("  ✓ 제목 입력 완료 (iframe)")
        except Exception as e:
            print(f"  ✗ 제목 입력 실패: {e}")

    # ─────────────────────── 사진 업로드 ───────────────────────

    async def upload_image(self, image_path: str) -> bool:
        if not Path(image_path).exists():
            print(f"  ✗ 파일 없음: {image_path}")
            return False

        print(f"  사진 업로드: {Path(image_path).name}")

        photo_btn_selectors = [
            "button[data-name='image']",
            ".se-toolbar-item-image button",
            "button[title='사진']",
            "button:has-text('사진')",
            ".se-image-toolbar-btn",
        ]
        clicked = False
        for sel in photo_btn_selectors:
            try:
                btn = self.page.locator(sel).first
                await btn.wait_for(timeout=3000)
                await btn.click()
                await asyncio.sleep(1)
                clicked = True
                break
            except Exception:
                pass

        if not clicked:
            print("  ✗ 사진 버튼을 찾지 못했습니다.")
            return False

        try:
            file_input = self.page.locator("input[type='file']").last
            await file_input.set_input_files(image_path)
            await asyncio.sleep(4)

            # 삽입 확인 버튼
            confirm_sels = ["button:has-text('확인')", "button:has-text('삽입')", ".confirm-btn"]
            for sel in confirm_sels:
                try:
                    btn = self.page.locator(sel).first
                    await btn.wait_for(timeout=2000)
                    await btn.click()
                    await asyncio.sleep(1)
                    break
                except Exception:
                    pass

            print(f"  ✓ 사진 업로드 완료: {Path(image_path).name}")
            return True

        except Exception as e:
            print(f"  ✗ 파일 입력 실패: {e}")
            return False

    # ─────────────────────── 본문 작성 ───────────────────────

    async def write_content(self, content: str, image_paths: list = None):
        print("▶ 본문 작성 중...")
        img_paths = image_paths or []
        img_idx = 0

        # 에디터 클릭
        editor_selectors = [
            ".se-content",
            ".se-component-content",
            "div[contenteditable='true']",
            ".ProseMirror",
        ]
        editor_clicked = False
        for sel in editor_selectors:
            try:
                editor = self.page.locator(sel).first
                await editor.wait_for(timeout=5000)
                await editor.click()
                editor_clicked = True
                break
            except Exception:
                pass

        if not editor_clicked:
            try:
                frame = self.page.frame_locator("iframe[title='본문'], iframe[title='editor']").first
                editor = frame.locator("div[contenteditable='true'], .ProseMirror").first
                await editor.click()
                editor_clicked = True
            except Exception:
                pass

        if not editor_clicked:
            print("  ⚠ 에디터를 찾지 못했습니다. Tab 키로 이동 시도...")
            await self.page.keyboard.press("Tab")

        await asyncio.sleep(0.5)

        lines = content.split("\n")
        for line in lines:
            stripped = line.strip()

            # 사진 삽입 위치
            if stripped.startswith("[사진") and img_idx < len(img_paths):
                await asyncio.sleep(0.5)
                await self.upload_image(img_paths[img_idx])
                img_idx += 1
                await asyncio.sleep(0.5)
                continue

            # 소제목
            if stripped.startswith("## "):
                text = stripped[3:]
                await self.page.keyboard.type(text, delay=30)
                await self.page.keyboard.press("Enter")
            elif stripped:
                await self.page.keyboard.type(stripped, delay=20)
                await self.page.keyboard.press("Enter")
            else:
                await self.page.keyboard.press("Enter")

            await asyncio.sleep(0.05)

        # 남은 사진 끝에 추가
        while img_idx < len(img_paths):
            await self.upload_image(img_paths[img_idx])
            img_idx += 1

        await asyncio.sleep(0.5)
        print("  ✓ 본문 작성 완료")

    # ─────────────────────── 태그 입력 ───────────────────────

    async def set_tags(self, tags: list):
        print(f"▶ 태그 입력 ({len(tags[:10])}개)...")
        tag_selectors = [
            "input[placeholder*='태그']",
            ".se-tag-input input",
            "input[class*='tag']",
            "#tagInput",
        ]
        tag_input = None
        for sel in tag_selectors:
            try:
                inp = self.page.locator(sel).first
                await inp.wait_for(timeout=3000)
                tag_input = inp
                break
            except Exception:
                pass

        if not tag_input:
            print("  ✗ 태그 입력창을 찾지 못했습니다.")
            return

        for tag in tags[:10]:
            try:
                await tag_input.click()
                await asyncio.sleep(0.2)
                await tag_input.type(tag, delay=40)
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(0.3)
            except Exception:
                pass

        print("  ✓ 태그 입력 완료")

    # ─────────────────────── 게시/임시저장 ───────────────────────

    async def publish(self, publish_now: bool = True) -> bool:
        action = "발행" if publish_now else "임시저장"
        print(f"▶ {action} 진행 중...")

        if publish_now:
            publish_selectors = [
                "button:has-text('발행')",
                "button:has-text('게시')",
                ".publish-btn",
                "button[data-type='publish']",
            ]
            for sel in publish_selectors:
                try:
                    btn = self.page.locator(sel).first
                    await btn.wait_for(timeout=5000)
                    await btn.click()
                    await asyncio.sleep(2)

                    # 발행 확인 팝업
                    confirm_sels = [
                        "button:has-text('발행하기')",
                        "button:has-text('확인')",
                        ".btn_confirm",
                        ".layer_btn .btn_blue",
                    ]
                    for csel in confirm_sels:
                        try:
                            cbtn = self.page.locator(csel).first
                            await cbtn.wait_for(timeout=3000)
                            await cbtn.click()
                            await asyncio.sleep(3)
                            break
                        except Exception:
                            pass

                    print(f"  ✓ {action} 완료")
                    return True
                except Exception:
                    pass

        # 임시저장
        try:
            save_sels = ["button:has-text('임시저장')", ".temp-save-btn"]
            for sel in save_sels:
                try:
                    btn = self.page.locator(sel).first
                    await btn.wait_for(timeout=3000)
                    await btn.click()
                    await asyncio.sleep(2)
                    print("  ✓ 임시저장 완료")
                    return True
                except Exception:
                    pass
        except Exception:
            pass

        return False

    # ─────────────────────── 게시물 확인 ───────────────────────

    async def verify_post(self, title: str) -> dict:
        """
        게시 후 실제 블로그에서 게시물 존재 여부 확인
        Returns: {"success": bool, "url": str, "title_found": str, "screenshot": str}
        """
        print("\n▶ 게시물 확인 중...")

        await asyncio.sleep(3)

        blog_url = f"https://blog.naver.com/{NAVER_ID}"
        await self.page.goto(blog_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # 블로그 내 최신 글 확인
        post_selectors = [
            ".blog_list .list_title",
            ".post-item .title",
            ".se-title",
            "a.link_post",
            ".post_title",
        ]

        found_title = None
        found_url = None

        for sel in post_selectors:
            try:
                items = self.page.locator(sel)
                count = await items.count()
                for i in range(min(count, 5)):
                    item_text = await items.nth(i).text_content()
                    if item_text and (title[:10] in item_text or item_text[:10] in title):
                        found_title = item_text.strip()
                        try:
                            href = await items.nth(i).get_attribute("href")
                            if href:
                                found_url = href if href.startswith("http") else f"https://blog.naver.com{href}"
                        except Exception:
                            pass
                        break
                if found_title:
                    break
            except Exception:
                pass

        # iframe 내부 확인 (블로그 프레임)
        if not found_title:
            try:
                frames = self.page.frames
                for frame in frames:
                    if "blog.naver.com" in frame.url:
                        items = frame.locator("a.link_post, .post_title, .list_title a")
                        count = await items.count()
                        for i in range(min(count, 5)):
                            item_text = await items.nth(i).text_content()
                            if item_text and (title[:10] in item_text or item_text[:10] in title):
                                found_title = item_text.strip()
                                href = await items.nth(i).get_attribute("href")
                                if href:
                                    found_url = href if href.startswith("http") else f"https://blog.naver.com{href}"
                                break
                        if found_title:
                            break
            except Exception:
                pass

        # 스크린샷 저장
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shot_path = await self._screenshot(f"verify_{ts}")

        if found_title:
            print(f"  ✓ 게시물 확인 완료!")
            print(f"  제목: {found_title}")
            if found_url:
                print(f"  URL:  {found_url}")
            print(f"  스크린샷: {shot_path}")
            return {
                "success": True,
                "url": found_url or blog_url,
                "title_found": found_title,
                "screenshot": shot_path,
                "blog_url": blog_url,
            }
        else:
            # 제목은 못 찾았지만 현재 URL 기록
            current_url = self.page.url
            print(f"  ⚠ 제목을 직접 확인하지 못했습니다.")
            print(f"  블로그 페이지: {current_url}")
            print(f"  스크린샷 저장: {shot_path}")
            print(f"  → 스크린샷에서 게시 여부를 직접 확인하세요.")
            return {
                "success": False,
                "url": current_url,
                "title_found": None,
                "screenshot": shot_path,
                "blog_url": blog_url,
            }

    # ─────────────────────── 전체 게시 프로세스 ───────────────────────

    async def post_and_verify(
        self,
        title: str,
        content: str,
        tags: list = None,
        image_paths: list = None,
        publish_now: bool = True,
    ) -> dict:
        """
        글 작성 → 게시 → 확인까지 전체 수행
        Returns: {"posted": bool, "verified": dict}
        """
        if not await self.go_to_write_page():
            return {"posted": False, "verified": None, "error": "글쓰기 페이지 이동 실패"}

        await self._screenshot("01_write_page")

        await self.set_title(title)
        await asyncio.sleep(0.5)

        await self.write_content(content, image_paths)
        await asyncio.sleep(0.5)

        if tags:
            await self.set_tags(tags)
            await asyncio.sleep(0.5)

        await self._screenshot("02_before_publish")

        posted = await self.publish(publish_now)
        await asyncio.sleep(2)

        await self._screenshot("03_after_publish")

        verify_result = await self.verify_post(title)

        return {
            "posted": posted,
            "verified": verify_result,
            "timestamp": datetime.now().isoformat(),
        }


def random_delay() -> int:
    import random
    return random.randint(80, 200)


# ─────────────────────── 편의 함수 ───────────────────────

async def run_post(
    title: str,
    content: str,
    tags: list = None,
    image_paths: list = None,
    publish_now: bool = True,
    headless: bool = False,
) -> dict:
    """
    네이버 블로그 게시 + 확인 실행

    Returns:
        {"posted": bool, "verified": dict, "timestamp": str}
    """
    poster = NaverBlogPoster(headless=headless, slow_mo=80)
    try:
        await poster.start()
        if not await poster.login():
            return {"posted": False, "verified": None, "error": "로그인 실패"}
        return await poster.post_and_verify(
            title=title,
            content=content,
            tags=tags,
            image_paths=image_paths,
            publish_now=publish_now,
        )
    finally:
        await poster.stop()
