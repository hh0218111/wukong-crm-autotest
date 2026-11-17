# 悟空CRM UI自动化测试框架

基于 **Pytest + Playwright** 的分层自动化框架：Page Object 模式 + yaml 数据驱动 + 失败自动截图 + Allure 报告 + GitHub Actions CI。

## 目录结构

```
crm-autotest/
├── config/
│   └── settings.py        # 全局配置，.env 注入，代码零硬编码
├── data/
│   └── login.yaml         # 测试数据外置（加场景=加数据，不改代码）
├── pages/
│   ├── base_page.py       # PO基类：goto/截图/通用等待
│   └── login_page.py      # 登录页：定位器集中管理
├── utils/
│   ├── yaml_loader.py     # 数据加载入口
│   └── db.py              # PyMySQL 造数据/落库核对/清理
├── tests/
│   ├── conftest.py        # fixture核心（浏览器/登录态/失败截图）
│   ├── test_smoke_framework.py  # 框架自检（不依赖业务环境）
│   └── test_login_example.py    # 数据驱动用例模板
├── .github/workflows/ci.yml       # push 触发自动跑（阶段一第3周接入）
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

pytest -m "not skip_env"                       # 跑全部可跑用例
pytest tests/test_smoke_framework.py -q        # 只跑框架自检
pytest --co -q                                 # 只看用例收集结果
allure serve reports/allure-results            # 看可视化报告
```

## 迁移旧用例的三步法

1. 每个页面建一个 PO 类（照 `login_page.py`），选择器用 `npx playwright codegen <你的CRM地址>` 辅助录制后人工整理
2. 用例逻辑从"过程脚本"拆成"数据+断言"：可变的输入输出沉到 `data/*.yaml`
3. 断言只依赖 PO 的 expect_* 方法，用例层不出现选择器

## 设计取舍（面试高频问题备答）

| 问题 | 这个框架的答案 |
|---|---|
| 为什么用 Playwright 不用 Selenium | 自动等待机制消灭大部分显式等待样板代码；context 隔离比多driver轻量；trace/截图开箱即用 |
| 登录态怎么处理 | 三级方案：function级context隔离 → logged_in_page fixture复用登录流程 → （性能优化路线）storage_state 保存cookie注入，跳过登录UI |
| 数据为什么外置 yaml | 同一段逻辑跑N个场景；非开发同学也能补充测试数据；diff 数据比 diff 代码可读 |
| 用例失败了怎么定位 | 失败自动截图 + Allure 附件 + （后续）trace.zip；配合接口层/SQL层复现，就是分层排障思路 |
| PO 模式解决什么问题 | 改版时定位器集中修改，用例层不动；操作与断言职责分离 |

## 待办路线（边做边勾）

- [ ] 29条旧用例逐页迁移（登录→线索→客户→商机→合同→回款）
- [ ] 接口自动化层：Requests + Pytest，与UI层共数据源
- [ ] GitHub Actions：push 触发 smoke 集
- [ ] storage_state 登录态优化（README"设计取舍"第三行有思路）
- [ ] 数据构造器：用 utils/db.py 造商机/合同/回款链路数据
