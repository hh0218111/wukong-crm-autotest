"""框架自检用例：不依赖CRM环境，验证骨架本身完好。

这个文件的意义：CI 里即使业务环境挂了，也能先回答"是框架坏了还是环境坏了"。
"""
import pytest

from config import settings
from utils.yaml_loader import load_yaml

pytestmark = pytest.mark.smoke


def test_settings_loaded():
    assert settings.BASE_URL.startswith("http"), "BASE_URL 配置异常"
    assert settings.DEFAULT_TIMEOUT > 0


def test_login_data_valid():
    """数据文件的格式校验：宁可在这里报错，不要在29条用例里各炸一次。"""
    data = load_yaml("login.yaml")
    assert isinstance(data["accounts"], list) and len(data["accounts"]) > 0
    for row in data["accounts"]:
        assert {"case", "username", "password", "expect_success"} <= row.keys(), row


def test_playwright_available():
    """确认 playwright 包与浏览器驱动就位（没装chromium时本用例仍应通过，
    因为它只检查包本身，不启动浏览器）。"""
    from playwright.sync_api import sync_playwright  # noqa: F401
