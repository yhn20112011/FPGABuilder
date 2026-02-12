"""
FPGABuilder插件包

包含各种FPGA工具链插件。
"""

import pkgutil
import importlib
from pathlib import Path

__all__ = []

# 自动发现子模块
for loader, module_name, is_pkg in pkgutil.iter_modules([str(Path(__file__).parent)]):
    if is_pkg:
        __all__.append(module_name)
        # 可选：自动导入子模块
        # importlib.import_module(f".{module_name}", __package__)