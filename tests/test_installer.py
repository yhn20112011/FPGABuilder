#!/usr/bin/env python3
"""
FPGABuilder安装程序测试

测试安装程序相关功能，包括：
1. Inno Setup脚本语法验证
2. 安装流程模拟
3. 环境变量配置测试
4. 卸载清理测试
"""

import os
import sys
import re
import tempfile
import shutil
from pathlib import Path
import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestInstaller:
    """安装程序测试类"""

    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp(prefix="installer_test_")

    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def extract_iss_content(self):
        """从package.py中提取Inno Setup脚本内容"""
        package_script = project_root / "scripts" / "package.py"
        content = package_script.read_text(encoding='utf-8')

        # 查找离线安装程序的ISS内容
        # 查找 build_windows_offline_installer 方法中的 iss_content
        pattern = r'iss_content = r"""(.*?)"""'
        matches = re.findall(pattern, content, re.DOTALL)

        if len(matches) >= 2:
            # 第二个匹配应该是离线安装程序（第一个是普通安装程序）
            return matches[1]
        elif matches:
            return matches[0]
        else:
            return None

    def test_iss_syntax_basic(self):
        """基本Inno Setup语法验证"""
        iss_content = self.extract_iss_content()
        assert iss_content is not None, "无法提取Inno Setup脚本内容"

        # 检查必要的节（section）
        required_sections = [
            '[Setup]',
            '[Languages]',
            '[Tasks]',
            '[Files]',
            '[Icons]',
            '[Run]',
            '[Code]'
        ]

        for section in required_sections:
            assert section in iss_content, f"缺失Inno Setup节: {section}"

        # 检查必要的定义
        required_defines = [
            '#define MyAppName',
            '#define MyAppVersion',
            '#define MyAppPublisher',
            '#define MyAppURL',
            '#define MyAppExeName'
        ]

        for define in required_defines:
            assert define in iss_content, f"缺失定义: {define}"

    def test_iss_code_functions(self):
        """检查Inno Setup [Code]节中的函数"""
        iss_content = self.extract_iss_content()
        assert iss_content is not None

        # 检查必要的函数
        required_functions = [
            'procedure AddToPath',
            'procedure RemoveFromPath',
            'function InitializeSetup',
            'procedure CurStepChanged',
            'procedure CurUninstallStepChanged'
        ]

        for func in required_functions:
            assert func in iss_content, f"缺失函数: {func}"

        # 检查环境变量广播函数（我们添加的）
        assert 'BroadcastEnvironmentChange' in iss_content, "缺失环境变量广播函数"
        assert 'SendMessageTimeout' in iss_content, "缺失SendMessageTimeout调用"
        assert 'WM_SETTINGCHANGE' in iss_content, "缺失WM_SETTINGCHANGE消息"

    def test_iss_path_management(self):
        """检查PATH环境变量管理逻辑"""
        iss_content = self.extract_iss_content()
        assert iss_content is not None

        # 检查AddToPath函数中的关键逻辑
        add_to_path_section = re.search(r'procedure AddToPath.*?end;', iss_content, re.DOTALL)
        assert add_to_path_section is not None, "找不到AddToPath函数"

        add_to_path_code = add_to_path_section.group(0)

        # 检查必要的操作
        required_operations = [
            'RegQueryStringValue',
            'RegWriteStringValue',
            'IsAdminLoggedOn',
            'Log('
        ]

        for op in required_operations:
            assert op in add_to_path_code, f"AddToPath中缺失操作: {op}"

        # 检查广播调用
        assert 'BroadcastEnvironmentChange()' in add_to_path_code, "AddToPath中缺失广播调用"

    def test_iss_postinstall_verification(self):
        """检查安装后验证步骤"""
        iss_content = self.extract_iss_content()
        assert iss_content is not None

        # 查找[Run]节
        run_section_match = re.search(r'\[Run\](.*?)(?=\n\[|\Z)', iss_content, re.DOTALL)
        assert run_section_match is not None, "找不到[Run]节"

        run_section = run_section_match.group(1)

        # 检查验证条目
        verification_entries = [
            '--version',
            '验证安装',
            'postinstall',
            'nowait',
            'skipifsilent'
        ]

        for entry in verification_entries:
            assert entry in run_section, f"[Run]节中缺失验证条目: {entry}"

        # 确保有多个运行条目（原始启动条目 + 验证条目）
        lines = [line.strip() for line in run_section.split('\n') if line.strip()]
        # 至少应该有2个Filename条目
        filename_lines = [line for line in lines if line.startswith('Filename:')]
        assert len(filename_lines) >= 2, f"[Run]节应至少包含2个条目，实际: {len(filename_lines)}"

    def test_iss_admin_privileges(self):
        """检查管理员权限设置"""
        iss_content = self.extract_iss_content()
        assert iss_content is not None

        # 检查[Setup]节中的管理员权限设置
        setup_section_match = re.search(r'\[Setup\](.*?)(?=\n\[|\Z)', iss_content, re.DOTALL)
        assert setup_section_match is not None, "找不到[Setup]节"

        setup_section = setup_section_match.group(1)

        required_setup_options = [
            'PrivilegesRequired=admin',
            'PrivilegesRequiredOverridesAllowed=dialog'
        ]

        for option in required_setup_options:
            assert option in setup_section, f"[Setup]节中缺失选项: {option}"

    def test_iss_compression_settings(self):
        """检查压缩设置"""
        iss_content = self.extract_iss_content()
        assert iss_content is not None

        # 检查压缩设置（离线安装程序应使用更好的压缩）
        setup_section_match = re.search(r'\[Setup\](.*?)(?=\n\[|\Z)', iss_content, re.DOTALL)
        assert setup_section_match is not None

        setup_section = setup_section_match.group(1)

        # 离线安装程序应使用lzma2/ultra64压缩
        assert 'Compression=lzma2/ultra64' in setup_section or 'Compression=lzma' in setup_section

    def test_iss_task_add_to_path(self):
        """检查"添加到PATH"任务"""
        iss_content = self.extract_iss_content()
        assert iss_content is not None

        # 检查[Tasks]节
        tasks_section_match = re.search(r'\[Tasks\](.*?)(?=\n\[|\Z)', iss_content, re.DOTALL)
        assert tasks_section_match is not None, "找不到[Tasks]节"

        tasks_section = tasks_section_match.group(1)

        # 检查"添加到PATH"任务
        assert 'addtopath' in tasks_section.lower(), "缺失addtopath任务"
        assert '将FPGABuilder添加到系统PATH' in tasks_section or 'Add to PATH' in tasks_section

    def test_iss_variable_syntax(self):
        """检查Inno Setup变量语法正确性"""
        iss_content = self.extract_iss_content()
        assert iss_content is not None

        # 检查常见的语法问题
        problematic_patterns = [
            r'\{\{\{',  # 三重花括号
            r'\}\}\}',  # 三重花括号
        ]

        for pattern in problematic_patterns:
            matches = re.findall(pattern, iss_content)
            if matches:
                print(f"警告: 发现可能的问题模式: {pattern}")
                print(f"匹配: {matches[:5]}")

        # 检查预处理变量语法
        # Inno Setup预处理变量应为 {#VariableName}
        preprocessor_vars = re.findall(r'\{\#\w+\}', iss_content)
        assert len(preprocessor_vars) > 0, "应包含预处理变量"

    def test_package_script_integration(self):
        """测试打包脚本与Inno Setup的集成"""
        package_script = project_root / "scripts" / "package.py"
        content = package_script.read_text(encoding='utf-8')

        # 检查build_windows_offline_installer方法是否存在
        assert 'def build_windows_offline_installer' in content, "缺失离线安装程序构建方法"

        # 检查Inno Setup编译器路径检测逻辑
        assert 'iscc.exe' in content, "应包含Inno Setup编译器检测"

        # 检查版本号替换
        assert '{version}' in content, "应包含版本号占位符"

    def test_install_verifier_integration(self):
        """检查安装验证工具的文档集成"""
        readme_file = project_root / "README.md"
        content = readme_file.read_text(encoding='utf-8')

        # 检查故障排除章节是否提到安装验证工具
        assert 'install_verifier.py' in content, "README应提到安装验证工具"
        assert '验证工具' in content, "README应提到验证工具"

        # 检查安装验证工具脚本存在
        verifier_script = project_root / "scripts" / "install_verifier.py"
        assert verifier_script.exists(), "安装验证工具不存在"


def test_environment_broadcast_function():
    """测试环境变量广播函数完整性"""
    package_script = project_root / "scripts" / "package.py"
    content = package_script.read_text(encoding='utf-8')

    # 查找BroadcastEnvironmentChange函数
    broadcast_func = re.search(r'procedure BroadcastEnvironmentChange.*?end;', content, re.DOTALL)
    assert broadcast_func is not None, "找不到BroadcastEnvironmentChange函数"

    func_code = broadcast_func.group(0)

    # 检查函数内容
    assert 'SendMessageTimeout' in func_code, "应调用SendMessageTimeout"
    assert 'HWND_BROADCAST' in func_code, "应使用HWND_BROADCAST"
    assert 'WM_SETTINGCHANGE' in func_code, "应使用WM_SETTINGCHANGE"
    assert 'Environment' in func_code, "应发送'Environment'消息"
    assert 'Log(' in func_code, "应记录日志"


def test_uninstall_cleanup():
    """测试卸载清理逻辑"""
    package_script = project_root / "scripts" / "package.py"
    content = package_script.read_text(encoding='utf-8')

    # 查找RemoveFromPath函数
    remove_func = re.search(r'procedure RemoveFromPath.*?end;', content, re.DOTALL)
    assert remove_func is not None, "找不到RemoveFromPath函数"

    func_code = remove_func.group(0)

    # 检查卸载逻辑
    assert 'CurUninstallStepChanged' in content, "应处理卸载步骤变更"
    assert 'usPostUninstall' in content, "应在卸载后清理"


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v"])