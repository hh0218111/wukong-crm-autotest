"""登录页 Page Object —— 迁移你的29条旧用例时，每个页面照着这个模式建一个类。

注意：下面的选择器是按悟空CRM常见结构给的示例，
务必打开真实页面用 Playwright Inspector 核对（npx playwright codegen 可辅助录制）。
"""
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    # --- 定位器集中管理：改版时只动这里 ---
    USERNAME_INPUT = "#username"           # 示例值，以实际页面为准
    PASSWORD_INPUT = "#password"           # 示例值，以实际页面为准
    LOGIN_BUTTON = "button.login-btn"      # 示例值，以实际页面为准
    SUCCESS_INDICATOR = "text=工作台"      # 登录成功的判定锚点：任一业务页特征元素
    ERROR_TOAST = ".el-message--error"     # 失败判定锚点：错误提示

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self) -> "LoginPage":
        self.goto("/login")
        return self

    def login(self, username: str, password: str) -> None:
        """执行一次登录动作。注意：不做断言，断言留给用例层。
        PO 负责'操作'，用例负责'验证'——职责分离，这也是面试点。"""
        if username:
            self.page.fill(self.USERNAME_INPUT, username)
        if password:
            self.page.fill(self.PASSWORD_INPUT, password)
        self.page.click(self.LOGIN_BUTTON)

    def expect_login_success(self) -> None:
        expect(self.page.locator(self.SUCCESS_INDICATOR)).to_be_visible()

    def expect_login_failed(self) -> None:
        expect(self.page.locator(self.ERROR_TOAST)).to_be_visible()
