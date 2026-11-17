"""CRM 五模块接口封装（迁移自旧框架 api/*.py，字段与端点均为 F12 实测值）。

改造要点：旧版每个函数都重复 headers/url/timeout 三件套，且 save 与 save_raw
是两份几乎相同的代码。现在统一走 ApiClient，raw 只是换个返回形式，零重复。
"""
from api.client import ApiClient


class LeadsApi(ApiClient):
    PATH = "/crm/leads"

    def index(self, page=1, limit=10, search="", **extra):
        return self.post(f"{self.PATH}/index",
                         {"page": page, "limit": limit, "search": search, **extra})

    def save(self, name, mobile="", **extra):
        return self.post(f"{self.PATH}/save", {"name": name, "mobile": mobile, **extra})

    def save_raw(self, name, mobile="", **extra):
        return self.raw(f"{self.PATH}/save", {"name": name, "mobile": mobile, **extra})

    def delete(self, ids):
        # 实测参数名是 id（不是 ids），写错会静默不删
        return self.post(f"{self.PATH}/delete", {"id": ids if isinstance(ids, list) else [ids]})


class CustomerApi(ApiClient):
    PATH = "/crm/customer"

    def index(self, page=1, limit=10, scene_id=0, **extra):
        return self.post(f"{self.PATH}/index",
                         {"page": page, "limit": limit, "scene_id": scene_id, **extra})

    def read(self, customer_id):
        return self.post(f"{self.PATH}/read", {"id": customer_id})

    def save(self, name, mobile="", **extra):
        return self.post(f"{self.PATH}/save", {"name": name, "mobile": mobile, **extra})

    def save_raw(self, name, mobile="", **extra):
        return self.raw(f"{self.PATH}/save", {"name": name, "mobile": mobile, **extra})

    def update(self, customer_id, **fields):
        return self.post(f"{self.PATH}/update", {"id": customer_id, **fields})

    def delete(self, customer_id):
        # 与其他模块保持一致：允许传单个id或id列表。
        # 曾因无脑再包一层列表，导致 cleanup 传 [244] 变成 [[244]]，
        # 服务端解析失败返回空body，清理静默失效（表现为JSONDecodeError）。
        ids = customer_id if isinstance(customer_id, list) else [customer_id]
        return self.post(f"{self.PATH}/delete", {"id": ids})


class BusinessApi(ApiClient):
    PATH = "/crm/business"

    def index(self, page=1, limit=10, scene_id=0, **extra):
        return self.post(f"{self.PATH}/index",
                         {"page": page, "limit": limit, "scene_id": scene_id, **extra})

    def _payload(self, name, customer_id, total_price, discount_rate=0,
                 status_id=4, deal_date="2026-08-20", type_id=1, **extra):
        return {"name": name, "customer_id": customer_id, "total_price": total_price,
                "discount_rate": discount_rate, "status_id": status_id,
                "deal_date": deal_date, "type_id": type_id, **extra}

    def save(self, name, customer_id, total_price, **kw):
        return self.post(f"{self.PATH}/save", self._payload(name, customer_id, total_price, **kw))

    def save_raw(self, name, customer_id, total_price, **kw):
        return self.raw(f"{self.PATH}/save", self._payload(name, customer_id, total_price, **kw))

    def delete(self, ids):
        return self.post(f"{self.PATH}/delete", {"id": ids if isinstance(ids, list) else [ids]})


class ContractApi(ApiClient):
    PATH = "/crm/contract"

    def index(self, page=1, limit=10, scene_id=0, **extra):
        return self.post(f"{self.PATH}/index",
                         {"page": page, "limit": limit, "scene_id": scene_id, **extra})

    def _payload(self, name, num, customer_id, money,
                 order_date="2026-08-20", check_user_id=1, **extra):
        return {"name": name, "num": num, "customer_id": customer_id, "money": money,
                "order_date": order_date, "check_user_id": check_user_id, **extra}

    def save(self, name, num, customer_id, money, **kw):
        return self.post(f"{self.PATH}/save", self._payload(name, num, customer_id, money, **kw))

    def save_raw(self, name, num, customer_id, money, **kw):
        return self.raw(f"{self.PATH}/save", self._payload(name, num, customer_id, money, **kw))

    def delete(self, ids):
        return self.post(f"{self.PATH}/delete", {"id": ids if isinstance(ids, list) else [ids]})


class ReceivablesApi(ApiClient):
    PATH = "/crm/receivables"

    def index(self, page=1, limit=10, scene_id=0, **extra):
        return self.post(f"{self.PATH}/index",
                         {"page": page, "limit": limit, "scene_id": scene_id, **extra})

    def read(self, receivables_id):
        return self.post(f"{self.PATH}/read", {"id": receivables_id})

    def _payload(self, customer_id, contract_id, money, return_time="2026-08-20",
                 return_type="现金", check_user_id=1, examineStatus=1, **extra):
        return {"customer_id": customer_id, "contract_id": contract_id, "money": money,
                "return_time": return_time, "return_type": return_type,
                "check_user_id": check_user_id, "examineStatus": examineStatus, **extra}

    def save(self, customer_id, contract_id, money, **kw):
        return self.post(f"{self.PATH}/save", self._payload(customer_id, contract_id, money, **kw))

    def save_raw(self, customer_id, contract_id, money, **kw):
        return self.raw(f"{self.PATH}/save", self._payload(customer_id, contract_id, money, **kw))

    def delete(self, ids):
        return self.post(f"{self.PATH}/delete", {"id": ids if isinstance(ids, list) else [ids]})
