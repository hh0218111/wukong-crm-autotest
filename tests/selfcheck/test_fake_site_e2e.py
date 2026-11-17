"""端到端自检：用本地静态假站点验证框架"登录态复用"链路真的通。

为什么要有这个文件（面试可讲）：
真实CRM环境没起时，团队没法判断"用例挂了是框架坏了还是环境坏了"。
这里用 Playwright 拦截 http://localhost:8078/** 的请求返回本地假页面，
在不装任何服务的前提下跑通：PO层操作 → fixture登录 → 数据驱动断言 → 失败截图。

标记 @pytest.mark.selfcheck：不依赖业务环境，CI 必跑。
"""
import pytest

from config import settings
from pages.login_page import LoginPage
from utils.yaml_loader import load_yaml

pytestmark = [pytest.mark.selfcheck, pytest.mark.smoke]

login_cases = load_yaml("login.yaml")["accounts"]


def test_login_success_on_fake(fake_page):
    """正例：正确账号登录后能看到工作台（验证 PO 层与断言链路）。"""
    login = LoginPage(fake_page).open()
    login.login("admin", "admin123")
    login.expect_login_success()


@pytest.mark.parametrize("row", login_cases, ids=[c["case"] for c in login_cases])
def test_login_cases_on_fake(fake_page, row: dict):
    """数据驱动链路自检：同一份 login.yaml 在假站点上按预期通过/失败。

    这条用例的意义：证明"数据文件 → parametrize → PO操作 → 断言"整条链是通的，
    换成真实CRM时只需去掉 skip_env 标记，用例代码零改动。
    """
    login = LoginPage(fake_page).open()
    login.login(row["username"], row["password"])
    if row["expect_success"]:
        login.expect_login_success()
    else:
        login.expect_login_failed()


def test_login_state_reuse(fake_page):
    """登录态复用自检：登录后同 context 内新开页面仍是已登录状态。

    真实框架里靠 storage_state 实现，这里验证 cookie 持久化机制本身可用。
    """
    login = LoginPage(fake_page).open()
    login.login("admin", "admin123")
    login.expect_login_success()

    second = fake_page.context.new_page()
    second.goto(f"{settings.BASE_URL}/", wait_until="domcontentloaded")
    assert second.locator("#welcome").is_visible(), "新页面应沿用已登录 cookie"
    second.close()
