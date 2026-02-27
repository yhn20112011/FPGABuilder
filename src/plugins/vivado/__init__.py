"""
Xilinx Vivado插件

支持Vivado设计套件的自动化构建。
"""

from .plugin import VivadoPlugin, Vivado2023Adapter, Vivado2024Adapter
from .file_scanner import FileScanner
from .tcl_templates import TCLScriptGenerator
from .packbin_templates import PackBinTemplate, MCSGenerationTemplate

__all__ = [
    "VivadoPlugin",
    "Vivado2023Adapter",
    "Vivado2024Adapter",
    "FileScanner",
    "TCLScriptGenerator",
    "PackBinTemplate",
    "MCSGenerationTemplate"
]