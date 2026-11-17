"""项目根 conftest —— 唯一的职责是把项目根加入 sys.path。

为什么需要：本地开发时 pytest 通常能把 rootdir 放进 sys.path，
但 CI（干净环境、无 venv 安装本项目）里不一定成立，会出现
`ModuleNotFoundError: No module named 'config'`。
显式注入后，本地和 CI 的导入行为完全一致。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
