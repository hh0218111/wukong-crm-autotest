# 悟空CRM 自动化测试框架（接口 + UI 双层）

基于 **Pytest + Playwright + Requests** 的分层自动化框架：Page Object 模式 + yaml 数据驱动 + 会话自愈 + 数据自清理 + 失败自动截图 + Allure 报告 + GitHub Actions CI。

**当前状态（实测）**：50 条用例 —— 接口 36 / UI 5 / 假站点自检 6 / 框架自检 3
- 默认 `pytest`：9 passed（不依赖业务环境，CI 可跑）
- 全量：37 passed, 12 xfailed（已知缺陷守护）, 1 failed（BUG-001 回归守护）
- 连跑两轮结果一致，五张业务表零数据残留

## 目录结构

```
crm-autotest/
├── config/
│   └── settings.py        # 全局配置，.env 注入，代码零硬编码
├── data/                  # 测试数据外置（加场景=加数据，不改代码）
│   ├── login.yaml         #   登录正反场景
│   ├── leads.yaml         #   线索边界值（含255/256字符）
│   ├── mobile_matrix.yaml #   手机号合法性矩阵
│   └── contract_money.yaml#   合同金额边界矩阵
├── api/                   # 接口封装层
│   ├── client.py          #   ApiClient + SessionHolder（单点登录自愈）
│   └── crm.py             #   线索/客户/商机/合同/回款 五模块
├── pages/
│   ├── base_page.py       # PO基类：goto/截图/通用等待
│   ├── login_page.py      # 登录页：F12实测选择器 + SPA等待 + 弹窗处理
│   └── crm_pages.py       # 四大列表页：ListPage基类 + 3行子类
├── utils/
│   ├── yaml_loader.py     # 数据加载入口
│   ├── asserts.py         # 断言收口（含"优雅拒绝"断言）
│   └── db.py              # PyMySQL 造数据/落库核对/清理
├── tests/
│   ├── conftest.py        # fixture核心（浏览器/登录态/失败截图）
│   ├── test_smoke_framework.py  # 框架自检（不依赖业务环境）
│   ├── selfcheck/         # 假站点端到端自检（不需要CRM环境）
│   │   ├── conftest.py    #   fake_page fixture：拦截请求返回本地页面
│   │   ├── fake_site/     #   静态假站点，选择器对齐真实PO
│   │   └── test_fake_site_e2e.py
│   ├── api/               # 接口层 36 条
│   │   ├── conftest.py    #   会话自愈 + 动态取真实ID + 数据清理
│   │   ├── test_login.py / test_customer.py / test_business.py
│   │   ├── test_contract.py / test_receivables.py  # ★含Bug#333
│   │   └── test_leads_api.py                       # ★含BUG-001
│   └── ui/                # UI层 5 条
│       ├── conftest.py    #   storage_state 登录态复用
│       └── test_crm_ui.py #   登录 + 四大列表（参数化）
├── docs/
│   ├── 环境启动说明.md    # 四服务启动顺序与踩坑
│   ├── 缺陷记录.md        # BUG-001 完整报告 + 接口契约
│   └── 迁移记录.md        # 28条旧用例迁移全过程与修复的问题
├── .github/workflows/ci.yml       # push 触发自动跑
├── pytest.ini             # marker定义与默认参数
└── .env.example           # 环境模板
```

## 快速开始

```bash
python -m venv venv
venv\Scripts\activate        # Windows；mac/linux 用 source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
copy .env.example .env       # 改成你的CRM地址和账号

pytest                                         # 默认跑不依赖环境的用例（9 passed）
pytest -m "skip_env or not skip_env"           # 全量（需先起环境，见docs/环境启动说明.md）
pytest -m skip_env                             # 只跑需要真实CRM的用例
pytest tests/selfcheck -q                      # 假站点端到端自检（验证框架链路本身）
pytest tests/test_smoke_framework.py -q        # 只跑配置/数据格式自检
pytest --co -q                                 # 只看用例收集结果
allure serve reports/allure-results            # 看可视化报告
```

## 新增用例的三步法

1. 页面：继承 `ListPage` 或 `BasePage`，选择器用 `playwright codegen` 录制后人工整理，集中在 PO 层
2. 数据：可变输入输出沉到 `data/*.yaml`，已知缺陷用 `known_bug` 字段标记
3. 断言：只调 PO 的 `expect_*` 或 `utils/asserts.py`，用例层不出现选择器；创建的数据登记 `cleanup`

## 设计取舍（面试高频问题备答）

| 问题 | 这个框架的答案 |
|---|---|
| 为什么用 Playwright 不用 Selenium | 自动等待机制消灭大部分显式等待样板代码；context 隔离比多driver轻量；trace/截图开箱即用 |
| 登录态怎么处理 | UI层：会话级登录一次 + storage_state 注入，context 仍逐用例隔离；接口层：SessionHolder 持有会话，被单点登录踢掉时自动重登 |
| 遇到单点登录怎么办 | 实测源码发现登录会 `Cache::rm` 旧 authKey，登录用例必然踢掉业务会话 → 检测 101/302 自动重建，且重试只放在 raw() 一层（避免非幂等请求重发） |
| 反向用例怎么保证有效 | 必须确保前置条件成立：回款用例要挑 check_status=7 的已审核合同，否则"被拦截"拦的是审核规则不是金额规则，用例会假通过 |
| 测试数据怎么不污染环境 | cleanup fixture + 按唯一名/remark 反查ID删除；实测跑前跑后五张表行数不变 |
| 数据为什么外置 yaml | 同一段逻辑跑N个场景；非开发同学也能补充测试数据；diff 数据比 diff 代码可读 |
| 用例失败了怎么定位 | 失败自动截图 + Allure 附件 + （后续）trace.zip；配合接口层/SQL层复现，就是分层排障思路 |
| PO 模式解决什么问题 | 改版时定位器集中修改，用例层不动；操作与断言职责分离 |

## 进度

- [x] 28条旧用例全部迁移（登录/客户/商机/合同/回款 + 4个UI列表），详见 docs/迁移记录.md
- [x] 接口自动化层：五模块封装 + 会话自愈 + 数据清理
- [x] storage_state 登录态复用
- [x] 失败自动截图（按类型识别任意Page）+ Allure 附件
- [x] 假站点自检层：不依赖业务环境验证框架链路
- [x] 发现并记录 BUG-001（线索名越界致 HTTP 500 泄露 SQL 异常）
- [ ] GitHub 建仓 push，让 Actions 真正跑起来
- [ ] 数据构造器：用 utils/db.py 造完整业务链路数据，摆脱对环境既有数据的依赖
- [ ] BUG-001 修复后摘掉守护标记，验证用例转绿
