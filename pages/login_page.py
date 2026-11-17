"""登录页 PO —— 选择器为 F12 实测值，已对本机 SPA 实例验证通过（2026-11-17）。

迁移改造：原先是占位选择器（#username / button.login-btn），
现替换为旧框架实测的真实值，并保留两个关键工程细节：
1. SPA hash 路由不触发标准 navigation 事件 → 用 wait_for_function 轮询 hash
2. 登录后有升级/引导弹窗遮挡 → 必须关掉，否则后续业务用例点不到元素
"""
from playwright.sync_api import Page, expect

from pages.base_page import BasePage

FRONTEND = "http://localhost/72crm/index.html"


class LoginPage(BasePage):
    URL = f"{FRONTEND}#/login"

    USERNAME_INPUT = "input[placeholder='请输入用户名']"
    PASSWORD_INPUT = "input[placeholder='请输入密码']"
    LOGIN_BUTTON = ".login-by-pwd .btn"      # 实际是 div.btn，不是 button
    ERROR_TIP = ".el-form-item__error"
    REMEMBER_CHECKBOX = ".el-checkbox"

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self) -> "LoginPage":
        self.page.goto(self.URL)
        self.page.wait_for_load_state("networkidle")
        self.page.locator(self.USERNAME_INPUT).wait_for(state="visible", timeout=15000)
        return self

    def login(self, username: str, password: str) -> None:
        """只负责操作，不做断言 —— PO 管操作，用例管验证。"""
        self.page.locator(self.USERNAME_INPUT).fill(username)
        self.page.locator(self.PASSWORD_INPUT).fill(password)
        self.page.locator(self.LOGIN_BUTTON).click()

    def wait_workbench(self, timeout: int = 20000) -> None:
        self.page.wait_for_function(
            "() => window.location.hash.includes('workbench')", timeout=timeout)

    def close_dialogs(self) -> None:
        """关闭登录后的升级通知/导入引导弹窗，最多3轮。"""
        for _ in range(3):
            btns = self.page.locator(".el-dialog__headerbtn:visible")
            if btns.count() == 0:
                break
            btns.first.click()
            self.page.wait_for_timeout(400)

    def expect_login_success(self) -> None:
        self.wait_workbench()
        self.close_dialogs()
        assert "workbench" in self.page.url, f"登录后未跳转工作台: {self.page.url}"

    def expect_login_failed(self) -> None:
        """失败判定：仍停在登录页（错误提示或表单校验）。"""
        self.page.wait_for_timeout(1200)
        assert "workbench" not in self.page.url, \
            f"非法凭据竟然登录成功: {self.page.url}"
