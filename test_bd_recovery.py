#!/usr/bin/env python3
"""测试BD恢复模板生成"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.plugins.vivado.tcl_templates import BDRecoveryTemplate

# 模拟配置
config = {
    'project': {'name': 'project'},
    'fpga': {'part': 'xc7z045ffg676-2', 'top_module': 'system_wrapper'},
    'project_dir': './build'
}

bd_config = {
    'tcl_script': 'src/bd/system.tcl',
    'is_top': True,
    'generate_wrapper': True,
    'auto_wrapper': True,
    'wrapper_language': 'verilog'
}

template = BDRecoveryTemplate(config, bd_config)
script = template.render()
print("生成的BD恢复TCL脚本:")
print("=" * 80)
print(script)
print("=" * 80)

# 检查关键命令
required_commands = [
    'update_compile_order',
    'generate_target all',
    'make_wrapper',
    'add_files -norecurse',
    'set_property top'
]

print("\n检查关键命令:")
for cmd in required_commands:
    if cmd in script:
        print(f"  [OK] 找到: {cmd}")
    else:
        print(f"  [MISSING] 未找到: {cmd}")

# 检查包装器路径
if 'wrapper_path' in script:
    print("\n包装器路径变量已定义")
else:
    print("\n警告: 包装器路径变量未定义")