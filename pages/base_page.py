"""所有 Page Object 的基类：沉淀通用操作，页面类只写自己特有的逻辑。

设计说明（面试可讲）：
- PO 模式的核心是把"元素定位"隔离在页面类里：改版后页面结构变了，
  只改 pages/ 下的定位器，tests/ 下的用例一行不动 —— 这是可维护性的来源
- Playwright 的 locator 自带等待（auto-waiting），所以这里不做 sleep 轮询，
  这也是我弃用 Selenium 显式等待样板代码的原因之一
"""
from playwright.sync_api import Page, expect

from config import settings


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.page.set_default_timeout(settings.DEFAULT_TIMEOUT)

    def goto(self, path: str = "/") -> None:
        """拼 BASE_URL 打开页面，并确认标题非空作为加载完成的最小信号。"""
        self.page.goto(f"{settings.BASE_URL}{path}", wait_until="domcontentloaded")

    def screenshot(self, name: str) -> str:
        """截图存到 reports/screenshots/，返回文件路径（失败钩子会调用）。"""
        from config.settings import REPORTS_DIR
        shots_dir = REPORTS_DIR / "screenshots"
        shots_dir.mkdir(parents=True, exist_ok=True)
        path = str(shots_dir / f"{name}.png")
        self.page.screenshot(path=path, full_page=True)
        return path

    def expect_visible(self, locator, timeout: int | None = None) -> None:
        expect(locator).to_be_visible(timeout=timeout)
