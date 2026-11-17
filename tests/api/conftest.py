"""接口层 fixture：会话自愈 + 动态取真实业务ID + 数据自清理。

迁移改造的关键一点：旧用例把 customer_id=48 / contract_id=27 写死在代码里，
换个环境或数据被删就全挂。现在改成运行时从列表接口取真实存在的ID，
用例不再依赖"某条特定数据必须存在"这个隐含前提。
"""
import time

import pytest

from api.client import SessionHolder
from api.crm import BusinessApi, ContractApi, CustomerApi, LeadsApi, ReceivablesApi

RUN_ID = time.strftime("%m%d%H%M%S")
_seq = iter(range(1, 100000))


def uniq(prefix: str) -> str:
    """唯一名称：系统对 name 有唯一性校验，固定名字会让用例不可重复执行。"""
    return f"{prefix}_{RUN_ID}_{next(_seq)}"


def mobile() -> str:
    """唯一手机号：mobile 同样有唯一性校验。"""
    return "13" + RUN_ID[-6:] + f"{next(_seq):03d}"


@pytest.fixture(scope="session")
def session():
    """会话容器：只登录一次，被单点登录踢掉时自动重建。

    注意返回的是 SessionHolder 而非裸 Session —— 悟空CRM同账号重复登录会
    使旧 authKey 失效，登录模块用例必然触发这一点，必须能自愈。
    """
    return SessionHolder()


@pytest.fixture(scope="session")
def leads(session):
    return LeadsApi(session)


@pytest.fixture(scope="session")
def customer(session):
    return CustomerApi(session)


@pytest.fixture(scope="session")
def business(session):
    return BusinessApi(session)


@pytest.fixture(scope="session")
def contract(session):
    return ContractApi(session)


@pytest.fixture(scope="session")
def receivables(session):
    return ReceivablesApi(session)


@pytest.fixture(scope="session")
def customer_id(customer) -> int:
    """取一个真实存在的客户ID（替代旧代码里写死的 48）。"""
    result = customer.index(page=1, limit=5)
    rows = result.get("data", {}).get("list", [])
    assert rows, "环境里没有客户数据，无法执行业务用例"
    return rows[0]["customer_id"]


@pytest.fixture(scope="session")
def contract_ref(contract) -> dict:
    """取一份**已审核通过**的真实合同，回款用例的前置条件。

    踩坑记录：最初只按 money>0 挑合同，结果全部回款用例返回
    「合同未审核通过」(code=400) —— 校验在金额之前就被拦下了，
    导致超额/负数/小数三条缺陷用例全部 XPASS（假通过）。
    这说明：反向用例必须确保前置条件成立，否则"被拦截"根本不是在测目标规则。

    实测 check_status=7 表示审核通过（旧用例写死的27号合同正是此状态）。
    """
    for page in range(1, 12):
        rows = contract.index(page=page, limit=50).get("data", {}).get("list", [])
        if not rows:
            break
        good = [r for r in rows
                if str(r.get("check_status")) == "7" and float(r.get("money") or 0) > 0]
        if good:
            return good[0]
    pytest.skip("环境里没有已审核通过的正金额合同，回款用例前置条件不满足")


@pytest.fixture()
def cleanup():
    """收集本轮创建的数据，用例结束后删除 —— 跑多少遍库里都不堆垃圾。

    用法：cleanup.append((api对象, [id, ...]))
    """
    tasks: list[tuple] = []
    yield tasks
    for api_obj, ids in tasks:
        if ids:
            try:
                api_obj.delete(ids)
            except Exception:
                pass  # 清理失败不应掩盖用例本身的结论


def collect_by_name(api_obj, name: str, id_field: str, cleanup, pages: int = 3,
                    match_field: str = "name"):
    """按唯一标识查回新建数据的ID并登记清理（回款用 remark 匹配）。

    为什么需要：多数 save 接口只返回"添加成功"字符串，拿不到ID，
    只能反查列表。用唯一名精确匹配，避免误删环境里的既有数据。
    """
    ids = []
    for page in range(1, pages + 1):
        rows = api_obj.index(page=page, limit=50).get("data", {}).get("list", [])
        if not rows:
            break
        ids.extend(r[id_field] for r in rows if r.get(match_field) == name)
        if ids:
            break
    if ids:
        cleanup.append((api_obj, ids))
    return ids
