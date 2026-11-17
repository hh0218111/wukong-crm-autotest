"""UI 层 fixture：登录态复用（storage_state），避免每条用例都走一遍登录UI。

关键设计：整套UI用例只登录一次，把 cookie/localStorage 存下来注入后续 context。
这既提速，也避开了悟空CRM单点登录的坑 —— 反复登录会互相踢掉会话。
"""
import pytest
from playwright.sync_api import Browser

from config import settings
from pages.login_page import LoginPage


@pytest.fixture(scope="session")
def ui_state(browser: Browser, tmp_path_factory) -> str:
    """会话级登录一次，导出 storage_state 路径。"""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    login = LoginPage(pg).open()
    login.login(settings.CRM_ADMIN_USER, settings.CRM_ADMIN_PASS)
    login.expect_login_success()
    path = tmp_path_factory.mktemp("auth") / "state.json"
    ctx.storage_state(path=str(path))
    ctx.close()
    return str(path)


@pytest.fixture()
def ui_page(browser: Browser, ui_state):
    """已登录的独立页面：共享登录态但 context 隔离。"""
    ctx = browser.new_context(storage_state=ui_state,
                              viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.set_default_timeout(settings.DEFAULT_TIMEOUT)
    yield pg
    ctx.close()


@pytest.fixture()
def anon_ui_page(browser: Browser):
    """未登录页面：登录用例与权限用例专用。"""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.set_default_timeout(settings.DEFAULT_TIMEOUT)
    yield pg
    ctx.close()
