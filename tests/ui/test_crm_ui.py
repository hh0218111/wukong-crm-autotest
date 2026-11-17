"""CRM UI 用例（迁移自旧 test_ui_smoke.py + test_crm_modules.py，共5条）。

改造三点：
1. 旧版 authenticated_page 每条用例都重新登录一次（4条业务用例=4次登录），
   现在会话级登录一次 + storage_state 注入，速度提升且避开单点登录互踢
2. 旧版四个列表用例是四段几乎相同的代码，现在参数化成一条数据驱动用例
3. 旧版账号密码硬编码在用例里，现在统一从 settings 取
"""
import allure
import pytest

from config import settings
from pages.crm_pages import BusinessPage, ContractPage, CustomerPage, ReceivablesPage
from pages.login_page import LoginPage

pytestmark = [pytest.mark.ui, pytest.mark.skip_env]

_LIST_PAGES = [
    ("客户列表", CustomerPage),
    ("商机列表", BusinessPage),
    ("合同列表", ContractPage),
    ("回款列表", ReceivablesPage),
]


@allure.feature("登录模块")
@allure.story("UI登录")
@allure.title("UI登录成功跳转工作台")
def test_login_success(anon_ui_page):
    login = LoginPage(anon_ui_page).open()
    login.login(settings.CRM_ADMIN_USER, settings.CRM_ADMIN_PASS)
    login.expect_login_success()


@allure.feature("业务列表")
@allure.story("列表加载")
@pytest.mark.parametrize("label,page_cls", _LIST_PAGES, ids=[x[0] for x in _LIST_PAGES])
def test_list_loads(ui_page, label, page_cls):
    """四大业务列表：表头渲染 + 数据行非空。"""
    page_obj = page_cls(ui_page).goto()
    page_obj.expect_loaded()
