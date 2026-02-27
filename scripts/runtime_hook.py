#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller runtime hook for FPGABuilder
解决相对导入和包路径问题
"""

import os
import sys

# 调试模式控制
DEBUG = os.environ.get('FPGABuilder_DEBUG', '').lower() in ('1', 'true', 'yes', 'on')

def debug_print(*args, **kwargs):
    """只在调试模式下打印信息"""
    if DEBUG:
        print(*args, **kwargs)

def error_print(*args, **kwargs):
    """始终打印错误信息"""
    print(*args, **kwargs)

def info_print(*args, **kwargs):
    """始终打印重要信息（如错误、警告）"""
    print(*args, **kwargs)

# 打印调试信息
debug_print(f"FPGABuilder runtime hook executing...")
debug_print(f"sys.path before: {sys.path}")

# 添加必要的路径到sys.path
if hasattr(sys, '_MEIPASS'):
    # PyInstaller打包运行时 - _MEIPASS是临时解压目录
    base_path = sys._MEIPASS
    debug_print(f"Running in PyInstaller mode, _MEIPASS: {base_path}")

    # 检查目录结构
    debug_print(f"Contents of _MEIPASS: {os.listdir(base_path)}")

    # 添加核心包路径
    core_path = os.path.join(base_path, 'core')
    plugins_path = os.path.join(base_path, 'plugins')

    if os.path.exists(core_path):
        sys.path.insert(0, core_path)
        debug_print(f"Added core path: {core_path}")

    if os.path.exists(plugins_path):
        sys.path.insert(0, plugins_path)
        debug_print(f"Added plugins path: {plugins_path}")

    # 也添加base_path本身
    sys.path.insert(0, base_path)
    debug_print(f"Added base path: {base_path}")
else:
    # 正常运行时 - 开发模式
    debug_print("Running in development mode")
    # 尝试找到src目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    src_dir = os.path.join(project_root, 'src')

    if os.path.exists(src_dir):
        sys.path.insert(0, src_dir)
        debug_print(f"Added src path: {src_dir}")

debug_print(f"sys.path after: {sys.path}")

# 确保插件模块可以导入
def _ensure_plugins_importable():
    try:
        import plugins.vivado.file_scanner
        import plugins.vivado.tcl_templates
        import plugins.vivado.packbin_templates
        debug_print("插件模块导入成功")
    except ImportError as e:
        info_print(f"插件模块导入警告: {e}")
        # 尝试手动添加路径
        if hasattr(sys, '_MEIPASS'):
            plugins_dir = os.path.join(sys._MEIPASS, 'plugins', 'vivado')
        else:
            # 开发模式
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            plugins_dir = os.path.join(project_root, 'src', 'plugins', 'vivado')

        if os.path.exists(plugins_dir):
            sys.path.insert(0, plugins_dir)
            debug_print(f"已添加插件目录到sys.path: {plugins_dir}")
            # 再次尝试导入
            try:
                import plugins.vivado.file_scanner
                import plugins.vivado.tcl_templates
                import plugins.vivado.packbin_templates
                debug_print("插件模块导入成功（添加路径后）")
            except ImportError as e2:
                error_print(f"插件模块导入仍失败: {e2}")

# 在适当的时机调用
_ensure_plugins_importable()