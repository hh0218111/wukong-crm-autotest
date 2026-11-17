"""CRM 业务列表页 PO（迁移自旧框架 pages/{customer,business,contract,receivables}_page.py）。

改造：旧版四个页面类各有 33 行、内容 95% 重复（只有 URL 和新建按钮名不同）。
现在抽一个 ListPage 基类，四个子类各 3 行 —— 这是 PO 分层该有的收益。
选择器沿用旧框架 F12 实测值，已对本机实例验证。
"""
from pages.base_page import BasePage

# 前端是独立 SPA，入口 index.html + hash 路由（不是后端 index.php）
FRONTEND = "http://localhost/72crm/index.html"


class ListPage(BasePage):
    """列表页通用基类：表头/数据行/新建按钮三件套。"""

    ROUTE = ""          # 子类覆盖，如 "#/crm/customer"
    NEW_BUTTON = ""     # 子类覆盖，如 "新建客户"

    def __init__(self, page):
        super().__init__(page)
        self.table = page.locator(".el-table:visible").first
        self.table_header = self.table.locator(".el-table__header-wrapper").first
        self.table_rows = self.table.locator(".el-table__row")
        self.new_button = page.get_by_role("button", name=self.NEW_BUTTON)

    def goto(self):
        """打开列表页并等数据渲染。SPA hash 路由不触发 navigation，靠元素等待。"""
        self.page.goto(f"{FRONTEND}{self.ROUTE}")
        self.table_header.wait_for(state="visible", timeout=15000)
        self.table_rows.first.wait_for(state="visible", timeout=15000)
        return self

    def row_count(self) -> int:
        return self.table_rows.count()

    def expect_loaded(self):
        """列表加载断言：表头可见 + 至少一行数据。"""
        assert self.table_header.is_visible(), "列表表头未渲染"
        assert self.row_count() > 0, "列表数据行数为 0"


class CustomerPage(ListPage):
    ROUTE = "#/crm/customer"
    NEW_BUTTON = "新建客户"


class BusinessPage(ListPage):
    ROUTE = "#/crm/business"
    NEW_BUTTON = "新建商机"


class ContractPage(ListPage):
    ROUTE = "#/crm/contract"
    NEW_BUTTON = "新建合同"


class ReceivablesPage(ListPage):
    ROUTE = "#/crm/receivables"
    NEW_BUTTON = "新建回款"
