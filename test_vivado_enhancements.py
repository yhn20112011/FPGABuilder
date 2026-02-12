#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试Vivado插件增强功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.config import ConfigManager
from plugins.vivado.plugin import VivadoPlugin
from plugins.vivado.file_scanner import FileScanner
from plugins.vivado.tcl_templates import TCLScriptGenerator


def test_config_enhancements():
    """测试配置增强功能"""
    print("测试配置增强功能...")

    # 创建配置管理器
    config_manager = ConfigManager()

    # 创建测试配置
    test_config = {
        'project': {
            'name': 'test_project',
            'version': '1.0.0',
            'description': '测试项目'
        },
        'fpga': {
            'vendor': 'xilinx',
            'part': 'xc7z045ffg676-2',
            'vivado_version': '2023.2',
            'vivado_settings': {
                'target_language': 'verilog',
                'synthesis_flow': 'project'
            }
        },
        'source': {
            'hdl': [
                {
                    'pattern': '**/*.v',
                    'language': 'verilog',
                    'language_auto_detect': True,
                    'file_type': 'source'
                }
            ],
            'constraints': [
                {
                    'pattern': '**/*.xdc',
                    'recursive': True
                }
            ],
            'block_design': {
                'tcl_script': 'src/bd/system.tcl',
                'is_top': True,
                'auto_wrapper': True,
                'wrapper_name': 'system_wrapper',
                'wrapper_language': 'verilog'
            }
        },
        'build': {
            'synthesis': {
                'strategy': 'Vivado Synthesis Defaults'
            },
            'hooks': {
                'pre_synth': 'scripts/pre_synth.tcl',
                'post_bitstream': 'scripts/post_bitstream.tcl'
            }
        }
    }

    # 验证配置
    try:
        config_manager.validate_config(test_config)
        print("  [OK] 配置验证通过")
    except Exception as e:
        print(f"  [ERROR] 配置验证失败: {e}")
        return False

    # 测试配置获取
    vivado_version = config_manager.get('fpga.vivado_version')
    if vivado_version == '2023.2':
        print(f"  [OK] Vivado版本配置正确: {vivado_version}")
    else:
        print(f"  [ERROR] Vivado版本配置错误: {vivado_version}")
        return False

    return True


def test_file_scanner():
    """测试文件扫描器"""
    print("测试文件扫描器...")

    # 创建临时目录结构
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 创建测试文件
        hdl_dir = tmp_path / 'src' / 'hdl'
        hdl_dir.mkdir(parents=True)

        (hdl_dir / 'top.v').write_text('module top(); endmodule')
        (hdl_dir / 'submodule.v').write_text('module submodule(); endmodule')
        (hdl_dir / 'test_submodule.v').write_text('// 测试文件')

        constraints_dir = tmp_path / 'src' / 'constraints'
        constraints_dir.mkdir(parents=True)
        (constraints_dir / 'constraints.xdc').write_text('set_property ...')

        # 创建配置
        config = {
            'source': {
                'hdl': [
                    {
                        'pattern': 'src/hdl/**/*.v',
                        'language': 'verilog',
                        'exclude': ['**/test_*']
                    }
                ],
                'constraints': [
                    {
                        'pattern': 'src/constraints/**/*.xdc'
                    }
                ]
            }
        }

        # 扫描文件
        scanner = FileScanner(tmp_path)
        scanned_files = scanner.scan_files(config)

        hdl_files = scanned_files.get('hdl', [])
        constraint_files = scanned_files.get('constraints', [])

        print(f"  [OK] 找到 {len(hdl_files)} 个HDL文件 (排除测试文件)")
        print(f"  [OK] 找到 {len(constraint_files)} 个约束文件")

        # 检查排除功能
        test_files = [f for f in hdl_files if 'test' in f['path']]
        if not test_files:
            print("  [OK] 测试文件已正确排除")
        else:
            print(f"  [ERROR] 测试文件未排除: {test_files}")
            return False

    return True


def test_tcl_templates():
    """测试TCL模板"""
    print("测试TCL模板...")

    config = {
        'project': {
            'name': 'test_project',
            'version': '1.0.0'
        },
        'fpga': {
            'part': 'xc7z045ffg676-2',
            'top_module': 'top'
        },
        'source': {
            'block_design': {
                'tcl_script': 'system.tcl',
                'is_top': True,
                'wrapper_name': 'system_wrapper'
            }
        },
        'build': {
            'synthesis': {
                'strategy': 'Vivado Synthesis Defaults'
            },
            'hooks': {
                'pre_synth': 'pre_synth.tcl'
            }
        }
    }

    # 测试BasicProjectTemplate
    from plugins.vivado.tcl_templates import BasicProjectTemplate
    basic_template = BasicProjectTemplate(config)
    basic_tcl = basic_template.render()

    if 'create_project' in basic_tcl and 'xc7z045ffg676-2' in basic_tcl:
        print("  [OK] BasicProjectTemplate生成正确")
    else:
        print("  [ERROR] BasicProjectTemplate生成失败")
        return False

    # 测试BDRecoveryTemplate
    from plugins.vivado.tcl_templates import BDRecoveryTemplate
    bd_template = BDRecoveryTemplate(config, config['source']['block_design'])
    bd_tcl = bd_template.render()

    if 'Block Design恢复脚本' in bd_tcl and 'system_wrapper' in bd_tcl:
        print("  [OK] BDRecoveryTemplate生成正确")
    else:
        print("  [ERROR] BDRecoveryTemplate生成失败")
        return False

    # 测试CleanTemplate
    from plugins.vivado.tcl_templates import CleanTemplate
    clean_template = CleanTemplate(config, 'soft')
    clean_tcl = clean_template.render()

    if '软清理：删除构建文件' in clean_tcl:
        print("  [OK] CleanTemplate生成正确")
    else:
        print("  [ERROR] CleanTemplate生成失败")
        return False

    return True


def test_vivado_plugin():
    """测试Vivado插件增强"""
    print("测试Vivado插件增强...")

    config = {
        'project': {
            'name': 'test_plugin',
            'version': '1.0.0'
        },
        'fpga': {
            'vendor': 'xilinx',
            'part': 'xc7z045ffg676-2'
        }
    }

    # 创建插件实例
    plugin = VivadoPlugin()

    # 测试初始化（无Vivado安装时应返回False）
    initialized = plugin.initialize(config)
    if not initialized:
        print("  [OK] 插件初始化正确（无Vivado安装）")
    else:
        print("  [ERROR] 插件初始化异常")
        # 如果有Vivado安装，这是正常的

    # 测试scan_and_import_files方法
    try:
        scan_result = plugin.scan_and_import_files(config)
        print("  [OK] scan_and_import_files方法正常工作")
    except Exception as e:
        print(f"  [ERROR] scan_and_import_files方法异常: {e}")
        return False

    return True


def main():
    """主测试函数"""
    print("=" * 60)
    print("Vivado插件增强功能测试")
    print("=" * 60)

    tests = [
        test_config_enhancements,
        test_file_scanner,
        test_tcl_templates,
        test_vivado_plugin
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"  [PASS] {test_func.__name__}\n")
            else:
                failed += 1
                print(f"  [FAIL] {test_func.__name__}\n")
        except Exception as e:
            failed += 1
            print(f"  [ERROR] {test_func.__name__}: {e}\n")

    print("=" * 60)
    print(f"测试完成: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)