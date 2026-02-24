"""
FPGABuilder核心模块
"""

__version__ = "0.2.0"
__author__ = "YiHok"
__license__ = "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International"

from .config import ConfigManager
from .project import ProjectManager
from .plugin_manager import PluginManager
from .cli import CLI

__all__ = [
    "ConfigManager",
    "ProjectManager",
    "PluginManager",
    "CLI",
    "__version__",
    "__author__",
    "__license__",
]