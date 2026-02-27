#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FPGABuilder启动脚本
用于PyInstaller打包，解决导入问题
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

debug_print("FPGABuilder Launcher starting...")

# 设置路径
if hasattr(sys, '_MEIPASS'):
    # PyInstaller环境
    base_path = sys._MEIPASS
    debug_print(f"PyInstaller mode, _MEIPASS: {base_path}")

    # 添加包路径
    core_path = os.path.join(base_path, 'core')
    plugins_path = os.path.join(base_path, 'plugins')

    if core_path not in sys.path:
        sys.path.insert(0, core_path)
    if plugins_path not in sys.path:
        sys.path.insert(0, plugins_path)
    if base_path not in sys.path:
        sys.path.insert(0, base_path)

    debug_print(f"sys.path configured: {sys.path}")
else:
    # 开发模式
    debug_print("Development mode")
    # 添加src目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    src_dir = os.path.join(project_root, 'src')

    if os.path.exists(src_dir) and src_dir not in sys.path:
        sys.path.insert(0, src_dir)

# 导入并运行主模块
try:
    # 导入cli模块
    from core.cli import main
    debug_print("Successfully imported core.cli module")

    # 运行主函数
    main()

except ImportError as e:
    error_print(f"Import error: {e}")
    debug_print(f"Current sys.path: {sys.path}")

    # 尝试列出目录内容
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
        debug_print(f"Contents of {base_path}:")
        try:
            for item in os.listdir(base_path):
                debug_print(f"  {item}")
                if item == 'core':
                    core_dir = os.path.join(base_path, 'core')
                    if os.path.isdir(core_dir):
                        debug_print(f"  Contents of core directory:")
                        for subitem in os.listdir(core_dir):
                            debug_print(f"    {subitem}")
        except Exception as list_err:
            error_print(f"Error listing directory: {list_err}")

    # 重新抛出错误
    raise

except Exception as e:
    error_print(f"Error running FPGABuilder: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)