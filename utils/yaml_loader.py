"""测试数据加载：data/ 下的 yaml 统一从这里进，用例不直接碰文件路径。"""
from pathlib import Path
from typing import Any

import yaml

from config.settings import DATA_DIR


def load_yaml(filename: str) -> Any:
    path: Path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"测试数据文件不存在: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
