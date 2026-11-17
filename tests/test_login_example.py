"""登录用例示例 —— 这是你迁移旧用例的模板，演示三件事：
1. 数据驱动：用例逻辑只写一遍，场景由 yaml 决定
2. PO 分层：用例里不出现任何选择器
3. marker 用法：smoke 标签的用例进 CI 必跑集

标记 @pytest.mark.skip_env：需要真实CRM环境。搭好环境后去掉标记即可跑。
"""
import pytest
from playwright.sync_api import Page

from pages.login_page import LoginPage
from utils.yaml_loader import load_yaml

login_cases = load_yaml("login.yaml")["accounts"]


def _case_id(row: dict) -> str:
    """用数据里的 case 字段做用例ID，报告里直接可读。"""
    return row["case"]


@pytest.mark.smoke
@pytest.mark.skip_env
@pytest.mark.parametrize("row", login_cases, ids=[_case_id(c) for c in login_cases])
def test_login(page: Page, row: dict):
    login = LoginPage(page).open()
    login.login(row["username"], row["password"])
    if row["expect_success"]:
        login.expect_login_success()
    else:
        login.expect_login_failed()
