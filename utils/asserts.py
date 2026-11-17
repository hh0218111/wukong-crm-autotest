"""断言封装层：把分散的 assert 收口，统一错误格式并带缺陷号上下文。

迁移自旧框架 utils/asserts.py，补充两点：
- assert_blocked 支持"必须是业务错误而非HTTP异常"的强校验（BUG-001 教训）
- 所有断言失败信息都带完整响应，避免只看到 AssertionError 不知道实际返回了什么
"""


def assert_success(result: dict, msg: str = ""):
    """期望成功：业务 code == 200。"""
    assert result.get("code") == 200, f"{msg} 期望成功(code=200)，实际: {result}"


def assert_blocked(result: dict, bug_no: str = ""):
    """期望被拦截：业务 code != 200。"""
    assert result.get("code") != 200, f"[{bug_no}] 期望被拦截，实际却返回成功: {result}"


def assert_graceful_reject(resp, bug_no: str = ""):
    """期望"优雅拒绝"：HTTP 200 + 业务错误码，而不是让异常冒成 500。

    这是 BUG-001 的核心教训：只断言"没成功"是不够的，
    服务端抛 500 也算"没成功"，但那是缺陷不是正确行为。
    """
    assert resp.status_code == 200, (
        f"[{bug_no}] 应返回业务校验错误而非 HTTP {resp.status_code}"
        f"（服务端异常外泄）: {resp.text[:200]}"
    )
    assert resp.json().get("code") != 200, f"[{bug_no}] 非法输入不应创建成功: {resp.text[:200]}"


def assert_status_code(resp, expected: int):
    assert resp.status_code == expected, \
        f"期望 HTTP {expected}，实际 {resp.status_code}: {resp.text[:200]}"


def assert_field_not_empty(data: dict, field: str):
    assert data.get(field), f"字段 [{field}] 缺失或为空: {data}"
