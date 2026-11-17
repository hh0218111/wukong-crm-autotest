"""接口客户端基类：所有 api 模块共用一个会话与请求入口。

迁移改造点（相对旧框架每个函数各自 requests.post）：
- 旧版每个 api 函数都要传 headers、各自拼 url、各自写 timeout —— 重复且易漏
- 现在会话持有鉴权头，模块函数只声明"路径 + 业务参数"，请求细节收口在一处
- 同时提供 json() 与 raw() 两种返回：业务断言用前者，HTTP异常类缺陷用后者
"""
import requests

from config import settings

TIMEOUT = 20


class SessionHolder:
    """可重建的会话容器 —— 应对悟空CRM的单点登录机制。

    实测发现（源码 admin/model/User.php 登录逻辑）：
        //删除旧缓存
        Cache::rm('Auth_' . $userInfo['authkey']);
    同一账号再次登录会主动删掉上一个会话的缓存，旧 authKey 立刻失效（code=101）。

    后果：登录模块用例自己登录一次，就把 session 级 fixture 的会话踢掉了，
    后续所有业务用例全部 101 —— 这不是被测系统的缺陷，是框架的设计漏洞。

    解法：会话由容器持有，检测到 101/302 自动重新登录并重试一次。
    """

    def __init__(self):
        self._s: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        if self._s is None:
            self._s = login_session()
        return self._s

    def refresh(self) -> requests.Session:
        self._s = login_session()
        return self._s


def _is_auth_expired(result) -> bool:
    return isinstance(result, dict) and result.get("code") in (101, 302)


class ApiClient:
    def __init__(self, holder: "SessionHolder"):
        self.holder = holder
        self.base = settings.BASE_URL

    @property
    def s(self) -> requests.Session:
        return self.holder.session

    def post(self, path: str, payload: dict | None = None) -> dict:
        """返回业务 JSON。

        鉴权重试只在 raw() 里做一次 —— 这里绝不能再重试一遍：
        删除/新建这类非幂等请求重发会造成"第一次已成功、第二次报错"，
        表现为清理时 JSONDecodeError（实际数据已经删掉了）。
        """
        return self.raw(path, payload).json()

    def raw(self, path: str, payload: dict | None = None) -> requests.Response:
        """返回原始响应：溢出/异常类缺陷需要断言 HTTP 状态码本身。

        注意：本机 php-cgi 在连续请求下偶发返回空 body / 502（环境抖动，
        不是被测系统缺陷）。这类瞬时故障重试一次，避免污染测试结论；
        但业务性 500（如 BUG-001 的字段越界）不重试，必须如实暴露。
        """
        resp = self.s.post(self.base + path, json=payload or {}, timeout=TIMEOUT)
        if resp.status_code in (502, 503, 504) or (
                resp.status_code == 200 and not resp.text.strip()):
            resp = self.s.post(self.base + path, json=payload or {}, timeout=TIMEOUT)
        # 500 等非JSON响应不做鉴权判断，直接返回供状态码断言
        if "application/json" in resp.headers.get("content-type", ""):
            try:
                if _is_auth_expired(resp.json()):
                    self.holder.refresh()
                    resp = self.s.post(self.base + path, json=payload or {}, timeout=TIMEOUT)
            except ValueError:
                pass
        return resp

    def get(self, path: str, params: dict | None = None) -> dict:
        result = self.s.get(self.base + path, params=params or {}, timeout=TIMEOUT).json()
        if _is_auth_expired(result):
            self.holder.refresh()
            result = self.s.get(self.base + path, params=params or {}, timeout=TIMEOUT).json()
        return result


def login_session(username: str | None = None, password: str | None = None) -> requests.Session:
    """登录并返回带鉴权头的会话（悟空CRM 用 authKey + sessionId 双头）。"""
    s = requests.Session()
    r = s.post(settings.BASE_URL + "/admin/base/login",
               json={"username": username or settings.CRM_ADMIN_USER,
                     "password": password or settings.CRM_ADMIN_PASS},
               timeout=TIMEOUT)
    result = r.json()
    assert result.get("code") == 200, f"登录失败: {result}"
    s.headers.update({
        "authKey": result["data"]["authKey"],
        "sessionId": result["data"]["sessionId"],
        "Content-Type": "application/json",
    })
    return s
