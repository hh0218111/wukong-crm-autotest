"""接口层用例 —— 端点、字段名、鉴权方式、边界值均已对本机悟空CRM实测确认（2026-11-17）。

演示五件事：
1. 接口优先策略：同一校验接口层毫秒级完成且无UI抖动，业务规则校验应下沉到这层
2. 模块级会话复用：登录一次拿 authKey+sessionId，整个模块共用
3. 写后读断言闭环：创建成功必须能查询回来，而不是只看返回码
4. 边界值实测修正：不靠猜"多长算超长"，查库拿字段定义再定边界
5. 可重复执行：系统有重名校验，固定名字第二次跑必挂 —— 用 run_id 后缀保证幂等

实测要点（面试可讲"你怎么摸清一个陌生系统的接口"）：
- 入口是 index.php，路由靠 pathinfo：BASE_URL=http://localhost/72crm/index.php
- 鉴权不是 Authorization，而是自定义头 authKey + sessionId（试错三种写法才确认）
- HTTP 永远 200，业务成败看响应体 code：200=成功，400=校验失败，101/302=未登录
- 线索客户名字段是 name（不是想当然的 customer_name），DB 定义 varchar(255)
- 系统对 name 有唯一性校验：重复提交返回 code=400「该字段值重复」
"""
import time

import pytest
import requests

from config import settings
from utils.yaml_loader import load_yaml

LOGIN_PATH = "/admin/base/login"
LEADS_ADD_PATH = "/crm/leads/save"
LEADS_LIST_PATH = "/crm/leads/index"
LEADS_DELETE_PATH = "/crm/leads/delete"

_data = load_yaml("leads.yaml")
cases = _data["cases"]
_boundaries = _data["boundaries"]

# 每轮运行唯一标识：避免重名/重手机号校验导致第二次执行失败（用例幂等性）
RUN_ID = time.strftime("%m%d%H%M%S")
_mobile_seq = iter(range(1, 10000))


def _mobile() -> str:
    """动态手机号：系统对 mobile 同样有唯一性校验，固定号码会让用例不可重复。"""
    return "13" + RUN_ID[-6:] + f"{next(_mobile_seq):03d}"


def _resolve(row: dict) -> dict:
    """把 name_ref 展开成真实长度的字符串（边界值由 DB 字段定义决定）。

    注意：边界用例的长度必须精确，所以后缀只能替换尾部字符而非追加。
    """
    payload = dict(row["data"])
    payload["mobile"] = _mobile()   # 数据文件里的号码只作示例，实际用动态值保证幂等
    if "name_ref" in payload:
        length = _boundaries[payload.pop("name_ref")]
        payload["name"] = ("长" * length)[:-len(RUN_ID)] + RUN_ID
    elif payload.get("name"):
        payload["name"] = f"{payload['name']}_{RUN_ID}"
    return payload


def _case_id(row: dict) -> str:
    return row["case"]


def _ok(resp: requests.Response) -> bool:
    """业务成功判定：HTTP 200 不代表成功，必须看响应体 code。"""
    if resp.status_code != 200:
        return False
    try:
        return resp.json().get("code") == 200
    except ValueError:
        return False


@pytest.fixture(scope="module")
def api() -> requests.Session:
    """模块级接口会话：登录一次，后续用例共享鉴权头。"""
    s = requests.Session()
    r = s.post(settings.BASE_URL + LOGIN_PATH,
               json={"username": settings.CRM_ADMIN_USER,
                     "password": settings.CRM_ADMIN_PASS},
               timeout=15)
    assert _ok(r), f"接口登录失败: {r.text[:200]}"
    data = r.json()["data"]
    # 悟空CRM 用自定义头鉴权，不是标准 Authorization
    s.headers.update({"authKey": data["authKey"], "sessionId": data["sessionId"]})
    return s


@pytest.fixture()
def created_ids(api: requests.Session):
    """用例级数据清理：收集本次创建的线索id，用完删掉，避免测试数据污染。

    这是"测试数据自治"的最小实现 —— 跑一百遍库里也不会堆一百条垃圾。
    """
    ids: list[int] = []
    yield ids
    if ids:
        api.post(settings.BASE_URL + LEADS_DELETE_PATH,
                 json={"id": ids}, timeout=15)  # 实测参数名是 id 不是 ids


def _find_leads(api: requests.Session, name: str) -> list[dict]:
    r = api.post(settings.BASE_URL + LEADS_LIST_PATH,
                 json={"page": 1, "limit": 50, "search": name[:20]}, timeout=15)
    assert _ok(r), f"列表查询失败: {r.text[:200]}"
    return [x for x in r.json()["data"]["list"] if x.get("name") == name]


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.skip_env
@pytest.mark.parametrize("row", cases, ids=[_case_id(c) for c in cases])
def test_create_leads(api: requests.Session, row: dict, created_ids):
    """数据驱动：正反场景+边界值一张表管完；断言以响应体业务码为准。"""
    payload = _resolve(row)
    r = api.post(settings.BASE_URL + LEADS_ADD_PATH, json=payload, timeout=20)

    if row["expect_success"]:
        assert _ok(r), f"合法数据应创建成功: {r.text[:200]}"
        for item in _find_leads(api, payload["name"]):
            created_ids.append(item["leads_id"])
    else:
        assert not _ok(r), f"非法数据不应静默创建成功: {r.text[:200]}"
        if row.get("expect_graceful"):
            # 缺陷断言：越界应返回业务校验错误，而不是让数据库异常冒到 HTTP 500
            assert r.status_code == 200, (
                f"越界输入应被业务层校验拦截并返回错误码，实际 HTTP {r.status_code}"
                f"（服务端异常直接暴露，见 docs/缺陷记录.md BUG-001）"
            )


@pytest.mark.api
@pytest.mark.skip_env
def test_create_then_query_back(api: requests.Session, created_ids):
    """写后读一致性：新建一条真实线索并确认列表能查回来。"""
    payload = {"name": f"写后读验证线索_{RUN_ID}", "mobile": _mobile()}
    add = api.post(settings.BASE_URL + LEADS_ADD_PATH, json=payload, timeout=15)
    assert _ok(add), add.text[:200]

    found = _find_leads(api, payload["name"])
    assert found, "新建线索应能在列表中查询到"
    assert found[0]["mobile"] == payload["mobile"], "落库手机号应与提交一致"
    created_ids.extend(x["leads_id"] for x in found)


@pytest.mark.api
@pytest.mark.skip_env
def test_duplicate_name_rejected(api: requests.Session, created_ids):
    """重名校验：同名线索第二次提交应被拒绝（实测发现的系统规则，补成回归用例）。"""
    payload = {"name": f"重名校验线索_{RUN_ID}", "mobile": _mobile()}
    first = api.post(settings.BASE_URL + LEADS_ADD_PATH, json=payload, timeout=15)
    assert _ok(first), first.text[:200]
    created_ids.extend(x["leads_id"] for x in _find_leads(api, payload["name"]))

    second = api.post(settings.BASE_URL + LEADS_ADD_PATH, json=payload, timeout=15)
    assert not _ok(second), "重复客户名不应创建成功"
    assert second.json().get("code") == 400, f"应返回校验错误码400，实际: {second.text[:150]}"


@pytest.mark.api
@pytest.mark.skip_env
def test_unauthenticated_access_rejected():
    """权限用例：不带鉴权头访问业务接口必须被拒绝（不能返回业务数据）。"""
    r = requests.post(settings.BASE_URL + LEADS_LIST_PATH,
                      json={"page": 1, "limit": 5}, timeout=15)
    assert not _ok(r), "未登录不应拿到业务数据"
