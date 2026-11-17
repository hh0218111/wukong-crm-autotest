"""回款模块接口用例（迁移自旧 testcases/test_receivables.py，5条）。

★ 本文件含简历核心素材：Bug#333 回款金额超合同金额未拦截。

迁移改造两点：
1. 旧版写死 contract_id=27 且超额值写死 5900000，依赖"27号合同恰好100万"这个
   隐含前提（实测该合同其实是1万）。现在运行时取真实已审核合同的金额，
   超额值 = 合同金额 × 5.9，让"超额"语义在任何环境下都成立。
2. 反向用例也登记清理：缺陷未修复时脏数据照样入库，不清就会越堆越多。
"""
import allure
import pytest

from utils.asserts import assert_field_not_empty, assert_success
from tests.api.conftest import collect_by_name, uniq

pytestmark = [pytest.mark.api, pytest.mark.skip_env]


def _save_and_track(receivables, contract_ref, money, tag, cleanup):
    """提交回款并登记清理（回款用 remark 作为唯一标识反查ID）。"""
    result = receivables.save(customer_id=contract_ref["customer_id"],
                              contract_id=contract_ref["contract_id"],
                              money=money, remark=tag)
    collect_by_name(receivables, tag, "receivables_id", cleanup, match_field="remark")
    return result


@allure.feature("回款模块")
@allure.story("正向")
@allure.title("新建回款成功")
def test_rec_001_receivables_save_success(receivables, contract_ref, cleanup):
    """金额取合同金额的一半，确保落在合法区间内。"""
    money = round(float(contract_ref["money"]) / 2, 2) or 100
    result = _save_and_track(receivables, contract_ref, money, uniq("rec_ok"), cleanup)
    assert_success(result, "新增回款")


@allure.feature("回款模块")
@allure.story("超合同金额")
@allure.title("回款金额超合同金额应被拦截")
@pytest.mark.xfail(strict=True, reason="Bug#333 回款超合同金额未拦截")
def test_rec_008_receivables_save_overflow_should_be_blocked(receivables, contract_ref, cleanup):
    """★ 简历核心用例：回款远超合同金额仍被接受。

    超额倍数动态计算，不写死金额 —— 保证"超额"语义与真实合同挂钩。
    """
    contract_money = float(contract_ref["money"])
    over = round(contract_money * 5.9, 2)
    result = _save_and_track(receivables, contract_ref, over, uniq("rec_over"), cleanup)
    assert result.get("code") != 200, (
        f"回款 {over} 远超合同金额 {contract_money}，应被拦截，实际: {result}"
    )


@allure.feature("回款模块")
@allure.story("负金额")
@allure.title("回款负金额应被拦截")
@pytest.mark.xfail(strict=True, reason="Bug#334 回款负金额未拦截")
def test_rec_015_receivables_save_negative_money_should_be_blocked(receivables, contract_ref, cleanup):
    result = _save_and_track(receivables, contract_ref, -100, uniq("rec_neg"), cleanup)
    assert result.get("code") != 200, f"负金额应被拦截，实际: {result}"


@allure.feature("回款模块")
@allure.story("金额小数")
@allure.title("回款金额含小数应被拦截")
@pytest.mark.xfail(strict=True, reason="回款金额小数位未拦截")
def test_rec_016_receivables_save_decimal_should_be_blocked(receivables, contract_ref, cleanup):
    result = _save_and_track(receivables, contract_ref, 100.5, uniq("rec_dec"), cleanup)
    assert result.get("code") != 200, f"小数位应被拦截，实际: {result}"


@allure.feature("回款模块")
@allure.story("列表查询")
@allure.title("回款列表分页查询成功")
def test_receivables_index_success(receivables):
    result = receivables.index(page=1, limit=5)
    assert_success(result)
    assert_field_not_empty(result["data"], "dataCount")
