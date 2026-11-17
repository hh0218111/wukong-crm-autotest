"""商机模块接口用例（迁移自旧 testcases/test_business.py，4条）。

改造：
- 旧版 customer_id=48 写死 → 改用 customer_id fixture 动态取真实数据
- 旧版 name 用时间戳防重 → 统一 uniq()，并清理创建的数据
- 溢出用例保留 save_raw：500 时 .json() 会抛异常，必须拿原始响应断言状态码
"""
import allure
import pytest

from utils.asserts import assert_field_not_empty, assert_success
from tests.api.conftest import collect_by_name, uniq

pytestmark = [pytest.mark.api, pytest.mark.skip_env]


@allure.feature("商机模块")
@allure.story("正向")
@allure.title("新建商机成功")
def test_opp_003_business_save_success(business, customer_id, cleanup):
    name = uniq("test_商机A")
    result = business.save(name=name, customer_id=customer_id, total_price="10000")
    assert_success(result, "新增商机")
    collect_by_name(business, name, "business_id", cleanup)


@allure.feature("商机模块")
@allure.story("负金额")
@allure.title("商机负金额应被拦截")
@pytest.mark.xfail(strict=True, reason="Bug#334 商机负金额未拦截")
def test_opp_010_business_save_negative_price_should_be_blocked(business, customer_id, cleanup):
    name = uniq("test_neg")
    result = business.save(name=name, customer_id=customer_id, total_price="-100")
    collect_by_name(business, name, "business_id", cleanup)
    assert result.get("code") != 200, f"负金额应被拦截，实际: {result}"


@allure.feature("商机模块")
@allure.story("金额溢出")
@allure.title("商机金额溢出不应返回500")
@pytest.mark.xfail(strict=True, reason="商机金额溢出未拦截，服务端异常外泄")
def test_opp_011_business_save_overflow_should_not_500(business, customer_id, cleanup):
    name = uniq("test_ovf")
    resp = business.save_raw(name=name, customer_id=customer_id,
                             total_price="99999999999999999.99")
    collect_by_name(business, name, "business_id", cleanup)
    assert resp.status_code != 500, \
        f"溢出应被业务层拦截，期望非500，实际: {resp.status_code}"


@allure.feature("商机模块")
@allure.story("列表查询")
@allure.title("商机列表分页查询成功")
def test_business_index_success(business):
    result = business.index(page=1, limit=5)
    assert_success(result)
    assert_field_not_empty(result["data"], "dataCount")
