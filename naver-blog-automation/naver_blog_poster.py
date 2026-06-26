"""
네이버 블로그 자동 포스팅 모듈
Playwright를 사용한 브라우저 자동화
"""

import os
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, BrowserContext

load_dotenv()

NAVER_ID = os.environ.get("NAVER_ID", "")
NAVER_PW = os.environ.get("NAVER_PW", "")


class NaverBlogPoster:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context: BrowserContext = None
        self.page: Page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            executable_path="/opt/pw-browsers/chromium",
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self.page = await self.context.new_page()

    async def stop(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def login(self) -> bool:
        """네이버 로그인"""
        print("네이버 로그인 중...")
        await self.page.goto("https://nid.naver.com/nidlogin.login")
        await self.page.wait_for_load_state("networkidle")

        await self.page.fill("#id", NAVER_ID)
        await asyncio.sleep(0.5)
        await self.page.fill("#pw", NAVER_PW)
        await asyncio.sleep(0.5)

        await self.page.click(".btn_login")
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        current_url = self.page.url
        if "nid.naver.com" in current_url and "login" in current_url:
            print("로그인 실패 - 캡챠 또는 보안 인증이 필요할 수 있습니다.")
            return False

        print("로그인 성공!")
        return True

    async def go_to_write_page(self) -> bool:
        """블로그 글쓰기 페이지 이동"""
        print("블로그 글쓰기 페이지 이동 중...")
        await self.page.goto("https://blog.naver.com/PostWriteForm.naver")
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        if "blog.naver.com" not in self.page.url:
            return False
        return True

    async def set_title(self, title: str):
        """제목 입력"""
        title_selector = "input[placeholder='제목']"
        await self.page.wait_for_selector(title_selector, timeout=10000)
        await self.page.click(title_selector)
        await self.page.fill(title_selector, title)
        await asyncio.sleep(0.5)

    async def upload_images(self, image_paths: list[str]) -> bool:
        """이미지 업로드"""
        if not image_paths:
            return True

        print(f"이미지 {len(image_paths)}장 업로드 중...")

        for img_path in image_paths:
            if not Path(img_path).exists():
                print(f"  경고: 파일 없음 - {img_path}")
                continue

            try:
                photo_btn = self.page.locator("button[data-type='image'], .se-toolbar-item-image, button:has-text('사진')")
                await photo_btn.first.click()
                await asyncio.sleep(1)

                file_input = self.page.locator("input[type='file']")
                await file_input.set_input_files(img_path)
                await asyncio.sleep(3)

                print(f"  업로드 완료: {Path(img_path).name}")

            except Exception as e:
                print(f"  이미지 업로드 실패 ({img_path}): {e}")

        return True

    async def write_content(self, content: str, image_paths: list[str] = None):
        """본문 작성 - 스마트에디터 ONE 대응"""
        print("본문 작성 중...")

        editor_frame = None
        try:
            editor_frame = self.page.frame_locator("iframe[title='본문']").first
        except Exception:
            pass

        content_area = None
        selectors = [
            ".se-content",
            ".se-component-content",
            "div[contenteditable='true']",
            ".ProseMirror",
        ]

        for sel in selectors:
            try:
                if editor_frame:
                    content_area = editor_frame.locator(sel).first
                else:
                    content_area = self.page.locator(sel).first

                await content_area.wait_for(timeout=5000)
                await content_area.click()
                break
            except Exception:
                content_area = None

        if not content_area:
            print("  에디터 영역을 찾지 못했습니다. 키보드 입력 시도...")
            await self.page.keyboard.press("Tab")

        lines = content.split("\n")
        img_idx = 0
        img_paths = image_paths or []

        for line in lines:
            if line.startswith("[사진") and img_idx < len(img_paths):
                await self.upload_images([img_paths[img_idx]])
                img_idx += 1
                await asyncio.sleep(1)
            else:
                if line.startswith("## "):
                    clean = line.replace("## ", "")
                    await self.page.keyboard.type(clean, delay=30)
                else:
                    await self.page.keyboard.type(line, delay=20)
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(0.1)

        if img_idx < len(img_paths):
            await self.upload_images(img_paths[img_idx:])

    async def set_tags(self, tags: list[str]):
        """태그 설정"""
        print("태그 입력 중...")
        tag_selectors = [
            "input[placeholder*='태그']",
            ".se-tag-input input",
            "#tagInput",
        ]

        tag_input = None
        for sel in tag_selectors:
            try:
                tag_input = self.page.locator(sel).first
                await tag_input.wait_for(timeout=3000)
                break
            except Exception:
                tag_input = None

        if not tag_input:
            print("  태그 입력창을 찾지 못했습니다.")
            return

        for tag in tags[:10]:
            await tag_input.click()
            await tag_input.type(tag, delay=50)
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(0.3)

    async def publish(self, publish_now: bool = True) -> bool:
        """게시 또는 임시저장"""
        if publish_now:
            print("블로그 게시 중...")
            publish_selectors = [
                "button:has-text('발행')",
                "button:has-text('게시')",
                ".publish-btn",
                "#publish-btn",
            ]
            for sel in publish_selectors:
                try:
                    btn = self.page.locator(sel).first
                    await btn.wait_for(timeout=3000)
                    await btn.click()
                    await asyncio.sleep(2)

                    confirm_selectors = [
                        "button:has-text('확인')",
                        "button:has-text('발행하기')",
                        ".btn-confirm",
                    ]
                    for csel in confirm_selectors:
                        try:
                            confirm = self.page.locator(csel).first
                            await confirm.wait_for(timeout=2000)
                            await confirm.click()
                            break
                        except Exception:
                            pass

                    print("게시 완료!")
                    return True
                except Exception:
                    pass

            print("발행 버튼을 찾지 못했습니다. 임시저장으로 전환...")

        print("임시저장 중...")
        try:
            save_btn = self.page.locator("button:has-text('임시저장')").first
            await save_btn.click()
            await asyncio.sleep(2)
            print("임시저장 완료!")
            return True
        except Exception as e:
            print(f"임시저장 실패: {e}")
            return False

    async def post_blog(
        self,
        title: str,
        content: str,
        tags: list[str] = None,
        image_paths: list[str] = None,
        publish_now: bool = True,
    ) -> bool:
        """블로그 글 전체 게시 프로세스"""
        try:
            if not await self.go_to_write_page():
                print("글쓰기 페이지 이동 실패")
                return False

            await self.set_title(title)
            await asyncio.sleep(1)

            await self.write_content(content, image_paths)
            await asyncio.sleep(1)

            if tags:
                await self.set_tags(tags)
                await asyncio.sleep(1)

            return await self.publish(publish_now)

        except Exception as e:
            print(f"포스팅 중 오류 발생: {e}")
            return False


async def post_to_naver(
    title: str,
    content: str,
    tags: list[str] = None,
    image_paths: list[str] = None,
    publish_now: bool = True,
    headless: bool = False,
) -> bool:
    """네이버 블로그에 글 게시하는 메인 함수"""
    poster = NaverBlogPoster(headless=headless)

    try:
        await poster.start()

        if not await poster.login():
            print("로그인 실패. 브라우저를 수동으로 조작하세요.")
            if not headless:
                print("30초 후 자동으로 종료됩니다...")
                await asyncio.sleep(30)
            return False

        result = await poster.post_blog(
            title=title,
            content=content,
            tags=tags,
            image_paths=image_paths,
            publish_now=publish_now,
        )

        if not headless and not result:
            print("수동 확인을 위해 10초 대기...")
            await asyncio.sleep(10)

        return result

    finally:
        await poster.stop()
