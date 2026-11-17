"""合同模块接口用例（迁移自旧 testcases/test_contract.py，6条 → 矩阵展开后9条）。

改造：
- 旧版把负金额/溢出/0金额分散成4个独立函数 + 一个矩阵，逻辑重复
  现在统一收进金额矩阵，一条数据一个场景，缺陷用 known_bug 标记
- 溢出场景单独保留 raw 断言：不只要"没创建成功"，还要"不能是HTTP 500"
- 旧版 num 用时间戳，现统一 uniq()；创建的数据进 cleanup
"""
import allure
import pytest

from utils.asserts import assert_blocked, assert_field_not_empty, assert_success
from utils.yaml_loader import load_yaml
from tests.api.conftest import collect_by_name, uniq

pytestmark = [pytest.mark.api, pytest.mark.skip_env]

_matrix = load_yaml("contract_money.yaml")["cases"]


@allure.feature("合同模块")
@allure.story("金额边界矩阵")
@pytest.mark.parametrize("case", _matrix, ids=[c["case"] for c in _matrix])
def test_contract_money_matrix(contract, customer_id, case, cleanup):
    if case.get("known_bug"):
        pytest.xfail(f"{case['known_bug']}：{case['case']}")

    name = uniq("HT矩阵")
    result = contract.save(name=name, num=uniq("HT"),
                           customer_id=customer_id, money=case["money"],
                           examineStatus=1)
    if case["expect_success"]:
        assert_success(result)
        collect_by_name(contract, name, "contract_id", cleanup)
    else:
        assert_blocked(result, case["case"])


@allure.feature("合同模块")
@allure.story("金额溢出")
@allure.title("合同金额溢出不应返回500")
@pytest.mark.xfail(strict=True, reason="合同金额溢出未拦截，服务端异常外泄")
def test_con_010_contract_save_overflow_should_not_500(contract, customer_id, cleanup):
    """这条与矩阵里的溢出场景互补：矩阵查业务码，这条查HTTP层是否泄露异常。"""
    name = uniq("HT500")
    resp = contract.save_raw(name=name, num=uniq("HT"),
                             customer_id=customer_id,
                             money="99999999999999999.99", examineStatus=1)
    collect_by_name(contract, name, "contract_id", cleanup)
    assert resp.status_code != 500, \
        f"溢出应被业务层拦截，期望非500，实际: {resp.status_code}"


@allure.feature("合同模块")
@allure.story("列表查询")
@allure.title("合同列表分页查询成功")
def test_contract_index_success(contract):
    result = contract.index(page=1, limit=5)
    assert_success(result)
    assert_field_not_empty(result["data"], "dataCount")
