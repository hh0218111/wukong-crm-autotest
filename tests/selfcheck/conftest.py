"""自检层 fixture：用本地静态假站点替代真实CRM，框架自检不依赖任何外部环境。"""
from pathlib import Path

import pytest
from playwright.sync_api import Browser

from config import settings

FAKE_HTML = (Path(__file__).parent / "fake_site" / "index.html").read_text(encoding="utf-8")


def _route_fake(route):
    """所有请求一律返回假站点，避免真实网络与端口依赖。"""
    route.fulfill(status=200, content_type="text/html; charset=utf-8", body=FAKE_HTML)


@pytest.fixture()
def fake_page(browser: Browser):
    """独立 context，拦截全部请求 —— 与真实环境完全隔离。"""
    ctx = browser.new_context()
    ctx.route("**/*", _route_fake)
    pg = ctx.new_page()
    pg.set_default_timeout(settings.DEFAULT_TIMEOUT)
    yield pg
    ctx.close()
