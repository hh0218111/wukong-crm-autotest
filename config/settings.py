"""全局配置：环境相关的一切从这里取值，代码里不硬编码任何地址/账号。

设计说明（面试可讲）：
- .env 放敏感值和可变值，通过 python-dotenv 加载，.env 不进 git
- os.getenv 带默认值，保证别人 clone 下来没有 .env 也能跑冒烟用例
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录 = config/ 的上一级
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"

load_dotenv(ROOT_DIR / ".env")

# --- 应用环境 ---
BASE_URL = os.getenv("BASE_URL", "http://localhost:8078")
CRM_ADMIN_USER = os.getenv("CRM_ADMIN_USER", "admin")
CRM_ADMIN_PASS = os.getenv("CRM_ADMIN_PASS", "admin123")

# --- 浏览器 ---
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))  # 调试时可设 200-500 观察执行过程

# --- 超时（毫秒）---
DEFAULT_TIMEOUT = 10_000

# --- 数据库 ---
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "wukong_crm"),
    "charset": "utf8mb4",
}
