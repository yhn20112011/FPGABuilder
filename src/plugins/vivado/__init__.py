"""
Xilinx Vivado插件

支持Vivado设计套件的自动化构建。
"""

from .plugin import VivadoPlugin, Vivado2023Adapter, Vivado2024Adapter

__all__ = [
    "VivadoPlugin",
    "Vivado2023Adapter",
    "Vivado2024Adapter"
]