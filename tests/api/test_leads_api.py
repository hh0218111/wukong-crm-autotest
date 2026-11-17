"""接口层用例 —— 框架的第二个测试层次，演示三件事：
1. 接口优先策略：同一校验接口层毫秒级完成且无UI抖动，业务规则校验应下沉到这层
2. 模块级会话复用：登录一次拿鉴权凭证，整个模块共用
3. 写后读断言闭环：创建成功必须能查询回来，而不是只看返回码

⚠️ 端点与鉴权头是按悟空CRM常见结构给的示例，
   务必用 Charles/Fiddler 对你本地实例实际抓包后替换 TODO 处再提交。
标记 @pytest.mark.skip_env：需要真实CRM环境；环境就绪后去标记运行。
"""
import pytest
import requests

from config import settings
from utils.yaml_loader import load_yaml

# TODO(1): 按实际抓包核对登录接口路径
LOGIN_PATH = "/adminapi/login"
# TODO(2): 按实际抓包核对线索创建/列表接口路径
LEADS_ADD_PATH = "/adminapi/crmLeads/addLeads"
LEADS_LIST_PATH = "/adminapi/crmLeads/getList"

cases = load_yaml("leads.yaml")["cases"]


def _case_id(row: dict) -> str:
    return row["case"]


@pytest.fixture(scope="module")
def api() -> requests.Session:
    """模块级接口会话：登录一次，后续用例共享鉴权头。"""
    s = requests.Session()
    r = s.post(settings.BASE_URL + LOGIN_PATH,
               json={"username": settings.CRM_ADMIN_USER,
                     "password": settings.CRM_ADMIN_PASS},
               timeout=10)
    assert r.status_code == 200, f"接口登录失败: {r.text[:200]}"
    # TODO(3): 按实际响应结构取 token 并设置鉴权头（悟空CRM通常为 Authorization: Bearer xxx）
    token = r.json().get("data", {}).get("token", "")
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.skip_env
@pytest.mark.parametrize("row", cases, ids=[_case_id(c) for c in cases])
def test_create_leads(api: requests.Session, row: dict):
    """数据驱动：正反场景一张表管完；断言以响应体业务码为准，不只看HTTP码。"""
    r = api.post(settings.BASE_URL + LEADS_ADD_PATH, json=row["data"], timeout=10)
    ok = r.status_code == 200 and str(r.json().get("code", "")).endswith("00000") \
        if r.headers.get("content-type", "").startswith("application/json") else False
    if row["expect_success"]:
        assert ok, f"合法数据应创建成功: {r.text[:200]}"
    else:
        assert not ok, f"非法数据不应静默创建成功: {r.text[:200]}"


@pytest.mark.api
@pytest.mark.skip_env
def test_create_then_query_back(api: requests.Session):
    """写后读一致性：新建一条真实线索并确认列表能查回来。"""
    payload = {"customer_name": "写后读验证线索", "mobile": "13900007777"}
    add = api.post(settings.BASE_URL + LEADS_ADD_PATH, json=payload, timeout=10)
    assert add.status_code == 200, add.text[:200]
    lst = api.get(settings.BASE_URL + LEADS_LIST_PATH,
                  params={"search": payload["customer_name"]}, timeout=10)
    assert payload["customer_name"] in lst.text, "新建线索应能查询到"
