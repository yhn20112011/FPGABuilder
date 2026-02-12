#!/usr/bin/env python3
"""
FPGABuilder基本功能测试

此脚本测试FPGABuilder的核心功能，无需安装。
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


def test_imports():
    """测试导入"""
    print("测试导入...")

    modules_to_test = [
        "core",
        "core.config",
        "core.project",
        "core.plugin_base",
        "core.plugin_manager",
        "core.cli",
    ]

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"  [OK] {module_name}")
        except ImportError as e:
            print(f"  [FAIL] {module_name}: {e}")
            return False

    return True


def test_config_manager():
    """测试配置管理器"""
    print("\n测试配置管理器...")

    try:
        from core.config import ConfigManager

        config_mgr = ConfigManager()
        print("  ✅ ConfigManager类创建成功")

        # 测试默认配置模式
        schema = config_mgr._get_default_schema()
        if schema and 'project' in schema.get('properties', {}):
            print("  ✅ 默认配置模式有效")
        else:
            print("  ❌ 默认配置模式无效")
            return False

        # 测试创建默认配置
        default_config = config_mgr.create_default_config(
            project_name="test_project",
            vendor="xilinx",
            part="xc7z045ffg676-2"
        )

        if default_config['project']['name'] == 'test_project':
            print("  ✅ 默认配置创建成功")
        else:
            print("  ❌ 默认配置创建失败")
            return False

        return True

    except Exception as e:
        print(f"  ❌ 配置管理器测试失败: {e}")
        return False


def test_plugin_base():
    """测试插件基类"""
    print("\n测试插件基类...")

    try:
        from core.plugin_base import PluginType, VersionRange, ToolInfo

        # 测试PluginType枚举
        assert PluginType.VENDOR.value == "vendor"
        print("  ✅ PluginType枚举")

        # 测试VersionRange
        vr = VersionRange("1.0.0", "2.0.0", "1.5.0")
        assert vr.min_version == "1.0.0"
        assert vr.max_version == "2.0.0"
        print("  ✅ VersionRange类")

        # 测试ToolInfo
        ti = ToolInfo("test_tool", "1.0.0", Path("/fake/path"))
        assert ti.name == "test_tool"
        print("  ✅ ToolInfo类")

        return True

    except Exception as e:
        print(f"  ❌ 插件基类测试失败: {e}")
        return False


def test_plugin_manager():
    """测试插件管理器"""
    print("\n测试插件管理器...")

    try:
        from core.plugin_manager import PluginManager

        pm = PluginManager()
        print("  ✅ PluginManager类创建成功")

        # 尝试发现插件（可能没有插件）
        pm.discover_plugins()
        print(f"  ✅ 插件发现完成，找到 {len(pm.get_all_plugins())} 个插件")

        # 测试获取插件管理器函数
        from core.plugin_manager import get_plugin_manager
        global_pm = get_plugin_manager()
        assert global_pm is not None
        print("  ✅ 全局插件管理器")

        return True

    except Exception as e:
        print(f"  ❌ 插件管理器测试失败: {e}")
        return False


def test_cli():
    """测试CLI接口"""
    print("\n测试CLI接口...")

    try:
        from core.cli import CLI

        cli = CLI()
        print("  ✅ CLI类创建成功")

        # 测试CLI组创建
        from core.cli import cli as click_group
        assert click_group.name == "cli"
        print("  ✅ Click命令组")

        return True

    except Exception as e:
        print(f"  ❌ CLI测试失败: {e}")
        return False


def test_vivado_plugin():
    """测试Vivado插件"""
    print("\n测试Vivado插件...")

    try:
        # 尝试导入Vivado插件
        import plugins.vivado

        print("  ✅ Vivado插件模块导入成功")

        # 检查插件类
        from plugins.vivado import VivadoPlugin

        plugin = VivadoPlugin()
        print(f"  ✅ Vivado插件创建成功: {plugin.name}")

        # 测试初始化
        initialized = plugin.initialize()
        print(f"  ✅ Vivado插件初始化: {'成功' if initialized else '失败（预期中）'}")

        # 测试兼容性报告
        report = plugin.get_compatibility_report()
        if report and "插件:" in report:
            print("  ✅ 兼容性报告生成成功")
        else:
            print("  ⚠️  兼容性报告可能有问题")

        return True

    except ImportError as e:
        print(f"  ⚠️  Vivado插件导入失败（可能缺少依赖）: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Vivado插件测试失败: {e}")
        return False


def test_run_script():
    """测试运行脚本"""
    print("\n测试运行脚本...")

    try:
        # 检查run.py是否存在
        run_script = Path(__file__).parent / "run.py"
        if not run_script.exists():
            print("  ❌ run.py不存在")
            return False

        print("  ✅ run.py存在")

        # 检查Makefile是否存在
        makefile = Path(__file__).parent / "Makefile"
        if makefile.exists():
            print("  ✅ Makefile存在")
        else:
            print("  ⚠️  Makefile不存在")

        # 检查打包脚本
        package_script = Path(__file__).parent / "scripts" / "package.py"
        if package_script.exists():
            print("  ✅ 打包脚本存在")
        else:
            print("  ⚠️  打包脚本不存在")

        return True

    except Exception as e:
        print(f"  ❌ 运行脚本测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("FPGABuilder 基本功能测试")
    print("=" * 50)

    tests = [
        test_imports,
        test_config_manager,
        test_plugin_base,
        test_plugin_manager,
        test_cli,
        test_vivado_plugin,
        test_run_script,
    ]

    passed = 0
    failed = 0
    warnings = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"  ✅ 通过: {passed}")
    print(f"  ❌ 失败: {failed}")
    print(f"  ⚠️  警告: {warnings}")

    if failed == 0:
        print("\n✅ 所有基本测试通过！")
        print("\n下一步:")
        print("  1. 运行 'python run.py dev --version' 测试CLI")
        print("  2. 运行 'python run.py dev compatibility' 检查插件兼容性")
        print("  3. 运行 'make test' 运行完整测试套件")
        return 0
    else:
        print("\n❌ 有测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())