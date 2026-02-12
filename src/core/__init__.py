"""
FPGABuilder核心模块
"""

__version__ = "0.1.0"
__author__ = "FPGABuilder Team"
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