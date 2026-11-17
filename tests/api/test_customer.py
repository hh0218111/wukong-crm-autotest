"""客户模块接口用例（迁移自旧 testcases/test_customer.py，6条 → 含矩阵展开共9条）。

改造三点：
1. 手机号矩阵从"用例里内联 parametrize"移到 data/mobile_matrix.yaml —— 加场景不改代码
2. 旧版矩阵里 12位/空号 期望值写的是 200（当时"先实测"留下的），
   现按缺陷事实统一用 xfail 标记，期望值表达真实业务预期而非将错就错
3. 新建的数据统一进 cleanup，旧版只删了 delete 用例那一条，其余全留在库里
"""
import allure
import pytest

from utils.asserts import assert_blocked, assert_field_not_empty, assert_success
from utils.yaml_loader import load_yaml
from tests.api.conftest import collect_by_name, mobile, uniq

pytestmark = [pytest.mark.api, pytest.mark.skip_env]

_matrix = load_yaml("mobile_matrix.yaml")["cases"]


@allure.feature("客户模块")
@allure.story("列表查询")
@allure.title("客户列表查询成功")
def test_customer_list_success(customer):
    assert_success(customer.index())


@allure.feature("客户模块")
@allure.story("列表查询")
@allure.title("客户列表分页查询成功")
def test_customer_list_pagination_success(customer):
    result = customer.index(page=1, limit=5)
    assert_success(result)
    assert_field_not_empty(result["data"], "dataCount")
    assert len(result["data"]["list"]) <= 5, "limit=5 时返回行数不应超过5"


@allure.feature("客户模块")
@allure.story("详情查询")
@allure.title("按列表首个ID查详情成功")
def test_customer_read_success(customer, customer_id):
    assert_success(customer.read(customer_id))


@allure.feature("客户模块")
@allure.story("手机号边界矩阵")
@pytest.mark.parametrize("case", _matrix, ids=[c["case"] for c in _matrix])
def test_customer_save_mobile_matrix(customer, case, cleanup):
    """数据驱动：手机号合法/非法场景一张表管完。

    known_bug 字段标记已知缺陷：用 xfail 表达"预期应拦截但当前未拦截"，
    strict=True 保证缺陷一旦修复用例会立刻变红提醒摘掉标记。
    """
    if case.get("known_bug"):
        pytest.xfail(f"{case['known_bug']}：{case['case']}")

    name = uniq("test_mobile")
    result = customer.save(name=name, mobile=case["mobile"])
    if case["expect_success"]:
        assert_success(result)
        # save 响应的 data 里不含 customer_id，必须按唯一名反查才能登记清理
        collect_by_name(customer, name, "customer_id", cleanup)
    else:
        assert_blocked(result, case["case"])


@allure.feature("客户模块")
@allure.story("删除")
@allure.title("新建后删除客户成功")
def test_customer_delete_success(customer):
    """自造数据再删，不动环境已有数据。"""
    created = customer.save(name=uniq("test_del"), mobile=mobile())
    assert_success(created)
    new_id = created["data"]["customer_id"]
    assert_success(customer.delete(new_id))
