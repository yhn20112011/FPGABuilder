"""
FPGABuilder核心模块
"""

__version__ = "0.2.0"
__author__ = "FPGABuilder Team:Yihok"
__license__ = "MIT"

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