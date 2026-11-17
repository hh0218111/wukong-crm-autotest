"""pytest 全局 fixture —— 这个文件是框架的心脏，面试必问，注释请逐行看懂。

登录态为什么这样设计（高频面试题："你的框架怎么处理登录？"）：
1. browser 是 session 级：整个进程只启动一次浏览器，避免每条用例冷启动，
   全套用例时间从小时级降到分钟级
2. context 是 function 级：每个用例一个全新浏览器上下文（独立cookie），
   用例之间互不污染 —— 这是隔离性
3. logged_in_page 是 function 级：对"必须登录"的用例，复用登录动作但隔离状态；
   如果实测登录太慢，可优化为 session 级 + storage_state 保存cookie注入，
   README 的"性能优化路线"里写了做法，属于加分项
"""
from datetime import datetime

import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from config import settings
from pages.login_page import LoginPage


# ---------- 浏览器与会话 ----------

@pytest.fixture(scope="session")
def browser() -> Browser:
    """session 级：整个测试进程共享一个 Chromium 实例。"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.HEADLESS, slow_mo=settings.SLOW_MO)
        yield browser
        browser.close()


@pytest.fixture()
def context(browser: Browser) -> BrowserContext:
    """function 级：每条用例独立上下文，cookie/存储互不影响。"""
    ctx = browser.new_context(base_url=settings.BASE_URL)
    yield ctx
    ctx.close()


@pytest.fixture()
def page(context: BrowserContext) -> Page:
    """function 级：每条用例一个全新页面。"""
    p = context.new_page()
    p.set_default_timeout(settings.DEFAULT_TIMEOUT)
    yield p
    p.close()


# ---------- 登录态复用 ----------

@pytest.fixture()
def logged_in_page(page: Page) -> Page:
    """已登录的页面：用例直接从业务页开始，不用再写一遍登录。

    迁移旧用例时，29条里凡是登录前提的，参数改成接收本fixture即可。
    """
    login = LoginPage(page).open()
    login.login(settings.CRM_ADMIN_USER, settings.CRM_ADMIN_PASS)
    login.expect_login_success()
    return page


# ---------- 失败自动截图 ----------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败时自动截图存档，报告链接里可直接看 —— 回归失败不用重跑现场。"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page") or item.funcargs.get("logged_in_page")
        if page is not None:
            shots = settings.REPORTS_DIR / "screenshots"
            shots.mkdir(parents=True, exist_ok=True)
            name = f"{item.name}_{datetime.now():%H%M%S}"
            try:
                page.screenshot(path=str(shots / f"{name}.png"), full_page=True)
                print(f"\n[失败截图] reports/screenshots/{name}.png")
            except Exception:
                pass  # 浏览器已崩溃等极端情况，截图失败不应掩盖原始报错
