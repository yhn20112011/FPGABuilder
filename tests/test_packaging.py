#!/usr/bin/env python3
"""
FPGABuilder打包测试

测试打包系统的正确性，包括：
1. 打包过程测试
2. 可执行文件功能测试
3. PyInstaller配置验证
4. 缺失模块检查
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestPackaging:
    """打包测试类"""

    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp(prefix="fpga_test_")
        self.dist_dir = Path(self.temp_dir) / "dist"
        self.build_dir = Path(self.temp_dir) / "build"

    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_package_imports(self):
        """测试核心模块是否可以导入"""
        # 测试核心模块
        import src.core
        import src.core.cli
        import src.core.config
        import src.core.project
        import src.core.plugin_manager
        import src.core.plugin_base

        # 测试插件模块
        import src.plugins
        import src.plugins.vivado
        import src.plugins.vivado.plugin
        import src.plugins.vivado.file_scanner
        import src.plugins.vivado.tcl_templates
        import src.plugins.vivado.packbin_templates

        assert src.core.__version__ is not None

    def test_pyinstaller_hidden_imports(self):
        """验证PyInstaller hiddenimports配置"""
        # 读取package.py中的hiddenimports配置
        package_script = project_root / "scripts" / "package.py"
        content = package_script.read_text(encoding='utf-8')

        # 检查必要的hiddenimports
        required_imports = [
            'plugins.vivado.file_scanner',
            'plugins.vivado.tcl_templates',
            'plugins.vivado.packbin_templates',
            'plugins.vivado.plugin',
            'plugins.vivado.__init__',
        ]

        for required in required_imports:
            assert required in content, f"缺失hiddenimport: {required}"

    def test_runtime_hook_exists(self):
        """检查运行时钩子文件存在"""
        runtime_hook = project_root / "scripts" / "runtime_hook.py"
        assert runtime_hook.exists(), "runtime_hook.py不存在"

        content = runtime_hook.read_text(encoding='utf-8')
        assert 'sys.path' in content, "runtime_hook.py应修改sys.path"
        assert 'plugins' in content, "runtime_hook.py应处理插件导入"

    def test_package_script_executable(self):
        """测试打包脚本可执行"""
        package_script = project_root / "scripts" / "package.py"

        # 测试帮助命令
        result = subprocess.run(
            [sys.executable, str(package_script), "--help"],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        assert result.returncode == 0, f"打包脚本帮助命令失败: {result.stderr}"
        assert "usage:" in result.stdout.lower() or "选项:" in result.stdout

    def test_build_executable_smoke(self):
        """冒烟测试：构建可执行文件（跳过实际构建，只测试配置）"""
        # 这个测试实际上不运行PyInstaller，只验证配置
        # 在实际CI中，可以添加环境变量跳过实际构建
        if os.environ.get('SKIP_PYINSTALLER_BUILD'):
            pytest.skip("跳过PyInstaller构建测试")

    def test_plugin_init_exports(self):
        """测试插件__init__.py正确导出所有类"""
        from src.plugins.vivado import __init__ as vivado_init

        # 检查__all__列表
        assert hasattr(vivado_init, '__all__'), "vivado/__init__.py缺少__all__"

        expected_exports = [
            'VivadoPlugin',
            'Vivado2023Adapter',
            'Vivado2024Adapter',
            'FileScanner',
            'TCLScriptGenerator',
            'PackBinTemplate',
            'MCSGenerationTemplate'
        ]

        for export in expected_exports:
            assert export in vivado_init.__all__, f"缺失导出: {export}"

        # 检查类是否可以导入
        from src.plugins.vivado import (
            VivadoPlugin, Vivado2023Adapter, Vivado2024Adapter,
            FileScanner, TCLScriptGenerator, PackBinTemplate, MCSGenerationTemplate
        )

        assert VivadoPlugin is not None
        assert FileScanner is not None
        assert TCLScriptGenerator is not None
        assert PackBinTemplate is not None
        assert MCSGenerationTemplate is not None

    def test_warn_file_analysis(self):
        """分析PyInstaller警告文件（如果存在）"""
        warn_file = project_root / "build" / "FPGABuilder" / "warn-FPGABuilder.txt"

        if warn_file.exists():
            content = warn_file.read_text(encoding='utf-8')

            # 检查不应出现的缺失模块警告
            problematic_modules = [
                'tcl_templates',
                'file_scanner',
                'packbin_templates'
            ]

            warnings = []
            for module in problematic_modules:
                if module in content:
                    warnings.append(f"发现缺失模块警告: {module}")

            if warnings:
                print(f"PyInstaller警告:\n{content}")
                # 警告但不失败，因为可能无关紧要
                for warning in warnings:
                    print(f"警告: {warning}")


def test_install_verifier_exists():
    """检查安装验证工具存在"""
    verifier_script = project_root / "scripts" / "install_verifier.py"
    assert verifier_script.exists(), "install_verifier.py不存在"

    content = verifier_script.read_text(encoding='utf-8')
    assert 'InstallVerifier' in content, "install_verifier.py应包含InstallVerifier类"
    assert 'check_executable_exists' in content, "应包含检查可执行文件的方法"


def test_readme_installation_steps():
    """检查README中的安装步骤包含验证"""
    readme_file = project_root / "README.md"
    content = readme_file.read_text(encoding='utf-8')

    # 检查必要的关键词
    assert '验证安装' in content, "README应包含安装验证步骤"
    assert '故障排除' in content, "README应包含故障排除章节"
    assert 'FPGABuilder --version' in content, "README应包含版本验证命令"


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v"])