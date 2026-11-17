"""登录模块接口用例（迁移自旧 testcases/test_login.py，2条）。

改造：旧版在用例里直接拼 url + requests.post，现在走统一客户端；
补充 authKey/sessionId 双头都非空的断言（旧版只查了 authKey）。
"""
import allure
import pytest
import requests

from config import settings

pytestmark = [pytest.mark.api, pytest.mark.skip_env]


@allure.feature("登录模块")
@allure.story("正向")
@allure.title("登录-正确账号密码")
def test_login_success():
    r = requests.post(settings.BASE_URL + "/admin/base/login",
                      json={"username": settings.CRM_ADMIN_USER,
                            "password": settings.CRM_ADMIN_PASS}, timeout=20)
    result = r.json()
    assert result.get("code") == 200, f"登录失败: {result}"
    assert result["data"]["authKey"], "authKey 不应为空"
    assert result["data"]["sessionId"], "sessionId 不应为空（双头鉴权缺一不可）"


@allure.feature("登录模块")
@allure.story("反向")
@allure.title("登录-错误密码")
def test_login_wrong_password():
    r = requests.post(settings.BASE_URL + "/admin/base/login",
                      json={"username": settings.CRM_ADMIN_USER,
                            "password": "wrong123"}, timeout=20)
    result = r.json()
    assert result.get("code") != 200, f"错误密码竟然登录成功: {result}"
