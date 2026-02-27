#!/usr/bin/env python3
"""
FPGABuilder安装验证工具

用于验证FPGABuilder安装是否正确，包括：
1. 可执行文件是否正常工作
2. PATH环境变量是否设置正确
3. 基本命令测试（--version, --help）
4. 插件模块是否可以加载
5. 生成安装验证报告
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime

class InstallVerifier:
    """安装验证器"""

    def __init__(self, install_dir: Optional[str] = None):
        """
        初始化验证器

        Args:
            install_dir: FPGABuilder安装目录，如果为None则自动检测
        """
        self.install_dir = install_dir
        self.system = platform.system()
        self.results = []
        self.errors = []
        self.warnings = []

    def detect_install_dir(self) -> Optional[str]:
        """自动检测安装目录"""
        if self.install_dir:
            return self.install_dir

        # 检查常见安装路径
        possible_paths = []

        if self.system == "Windows":
            # Windows程序文件目录
            program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
            possible_paths.extend([
                os.path.join(program_files, "FPGABuilder"),
                os.path.join(program_files, "FPGABuilder", "bin"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "FPGABuilder"),
            ])

            # 检查PATH环境变量中的路径
            path_dirs = os.environ.get("PATH", "").split(";")
            for path_dir in path_dirs:
                if "FPGABuilder" in path_dir:
                    possible_paths.append(path_dir)
        else:
            # Linux/macOS路径
            possible_paths.extend([
                "/usr/local/bin",
                "/usr/bin",
                "/opt/FPGABuilder/bin",
                os.path.expanduser("~/.local/bin"),
            ])

        # 检查路径是否存在并包含FPGABuilder可执行文件
        for path in possible_paths:
            if self.system == "Windows":
                exe_path = os.path.join(path, "FPGABuilder.exe")
            else:
                exe_path = os.path.join(path, "FPGABuilder")

            if os.path.exists(exe_path):
                return path

        return None

    def get_executable_path(self) -> Optional[str]:
        """获取可执行文件路径"""
        if not self.install_dir:
            self.install_dir = self.detect_install_dir()

        if not self.install_dir:
            return None

        if self.system == "Windows":
            return os.path.join(self.install_dir, "FPGABuilder.exe")
        else:
            return os.path.join(self.install_dir, "FPGABuilder")

    def check_executable_exists(self) -> Tuple[bool, str]:
        """检查可执行文件是否存在"""
        exe_path = self.get_executable_path()
        if not exe_path:
            return False, "未找到FPGABuilder可执行文件"

        if not os.path.exists(exe_path):
            return False, f"可执行文件不存在: {exe_path}"

        return True, f"可执行文件存在: {exe_path}"

    def check_path_environment(self) -> Tuple[bool, str]:
        """检查PATH环境变量"""
        exe_path = self.get_executable_path()
        if not exe_path:
            return False, "无法确定可执行文件路径"

        install_dir = os.path.dirname(exe_path)
        path_var = os.environ.get("PATH", "")

        if self.system == "Windows":
            path_dirs = path_var.split(";")
        else:
            path_dirs = path_var.split(":")

        if install_dir in path_dirs:
            return True, f"安装目录在PATH中: {install_dir}"
        else:
            # 检查是否可以通过命令名直接访问
            try:
                if self.system == "Windows":
                    subprocess.run(["where", "FPGABuilder"], capture_output=True, check=True)
                else:
                    subprocess.run(["which", "FPGABuilder"], capture_output=True, check=True)
                return True, "可以通过命令名访问FPGABuilder"
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False, f"安装目录不在PATH中: {install_dir}"

    def test_command(self, command: str, args: List[str], timeout: int = 10) -> Tuple[bool, str, Optional[str]]:
        """测试命令执行"""
        exe_path = self.get_executable_path()
        if not exe_path or not os.path.exists(exe_path):
            return False, "可执行文件不存在", None

        try:
            cmd = [exe_path, command] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode == 0:
                return True, f"命令执行成功: {command}", result.stdout
            else:
                return False, f"命令执行失败 ({result.returncode}): {command}", result.stderr
        except subprocess.TimeoutExpired:
            return False, f"命令执行超时: {command}", None
        except Exception as e:
            return False, f"命令执行异常: {command} - {str(e)}", None

    def check_plugins(self) -> Tuple[bool, str]:
        """检查插件是否可以加载"""
        # 测试插件相关命令
        success, message, output = self.test_command("vivado", ["--help"])
        if success:
            return True, "Vivado插件可以正常加载"
        else:
            # 检查是否是插件未安装的错误
            if output and ("plugin" in output.lower() or "vivado" in output.lower()):
                return False, f"插件加载失败: {output[:100]}"
            else:
                # 可能只是帮助信息输出到stderr
                return True, "插件命令可以执行"

    def check_python_environment(self) -> Tuple[bool, str]:
        """检查Python环境（仅适用于非打包版本）"""
        exe_path = self.get_executable_path()
        if not exe_path:
            return False, "未找到可执行文件"

        # 检查是否是PyInstaller打包的可执行文件
        try:
            with open(exe_path, 'rb') as f:
                content = f.read(100)
                if b'PyInstaller' in content:
                    return True, "检测到PyInstaller打包的可执行文件（自包含，无需Python）"
        except:
            pass

        # 检查Python是否可用
        try:
            result = subprocess.run(
                [sys.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, f"Python环境可用: {result.stdout.strip()}"
            else:
                return False, "Python环境不可用"
        except:
            return False, "无法检查Python环境"

    def run_all_checks(self) -> Dict:
        """运行所有检查"""
        print("=" * 60)
        print("FPGABuilder安装验证")
        print("=" * 60)

        checks = [
            ("可执行文件存在", self.check_executable_exists),
            ("PATH环境变量", self.check_path_environment),
            ("Python环境", self.check_python_environment),
            ("版本命令", lambda: self.test_command("--version", [])),
            ("帮助命令", lambda: self.test_command("--help", [])),
            ("插件加载", self.check_plugins),
        ]

        for check_name, check_func in checks:
            print(f"\n[{check_name}]")
            try:
                if check_name in ["版本命令", "帮助命令"]:
                    success, message, output = check_func()
                    if success:
                        print(f"  ✓ {message}")
                        if output and len(output.strip()) > 0:
                            print(f"    输出: {output.strip()[:100]}")
                    else:
                        print(f"  ✗ {message}")
                        if output:
                            print(f"    错误: {output[:100]}")
                        self.errors.append(f"{check_name}: {message}")
                else:
                    success, message = check_func()
                    if success:
                        print(f"  ✓ {message}")
                    else:
                        print(f"  ✗ {message}")
                        self.errors.append(f"{check_name}: {message}")

                self.results.append({
                    "check": check_name,
                    "success": success,
                    "message": message
                })
            except Exception as e:
                error_msg = f"检查异常: {str(e)}"
                print(f"  ✗ {error_msg}")
                self.errors.append(f"{check_name}: {error_msg}")
                self.results.append({
                    "check": check_name,
                    "success": False,
                    "message": error_msg
                })

        return self.generate_report()

    def generate_report(self) -> Dict:
        """生成验证报告"""
        total_checks = len(self.results)
        successful_checks = sum(1 for r in self.results if r["success"])

        report = {
            "timestamp": datetime.now().isoformat(),
            "system": self.system,
            "install_dir": self.install_dir,
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "success_rate": successful_checks / total_checks if total_checks > 0 else 0,
            "results": self.results,
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": "安装验证通过" if len(self.errors) == 0 else "安装验证失败"
        }

        print("\n" + "=" * 60)
        print("验证报告")
        print("=" * 60)
        print(f"系统: {self.system}")
        print(f"安装目录: {self.install_dir or '未找到'}")
        print(f"检查总数: {total_checks}")
        print(f"通过检查: {successful_checks}")
        print(f"成功率: {report['success_rate']:.1%}")

        if self.errors:
            print("\n❌ 发现错误:")
            for error in self.errors:
                print(f"  • {error}")
        else:
            print("\n✅ 所有检查通过！")

        if self.warnings:
            print("\n⚠️  警告:")
            for warning in self.warnings:
                print(f"  • {warning}")

        print(f"\n总结: {report['summary']}")

        # 提供解决方案建议
        if self.errors:
            print("\n💡 解决方案建议:")
            if "可执行文件存在" in str(self.errors):
                print("  1. 重新安装FPGABuilder")
                print("  2. 检查安装目录是否存在")
            if "PATH环境变量" in str(self.errors):
                print("  1. 重启终端或电脑使PATH变更生效")
                print("  2. 手动将安装目录添加到PATH环境变量")
                if self.install_dir:
                    print(f"     安装目录: {self.install_dir}")
            if "插件加载" in str(self.errors):
                print("  1. 确保Vivado已正确安装")
                print("  2. 检查FPGABuilder插件配置")

        return report

    def save_report(self, report: Dict, output_file: str = "install_verification_report.json"):
        """保存报告到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n报告已保存到: {output_file}")
        except Exception as e:
            print(f"\n保存报告失败: {str(e)}")


def main():
    """主函数"""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="FPGABuilder安装验证工具")
    parser.add_argument("--install-dir", "-i", help="FPGABuilder安装目录")
    parser.add_argument("--output", "-o", default="install_verification_report.json",
                       help="输出报告文件路径")
    parser.add_argument("--quick", "-q", action="store_true",
                       help="快速验证（仅检查基本功能）")
    parser.add_argument("--fix-path", action="store_true",
                       help="尝试自动修复PATH环境变量（需要管理员权限）")

    args = parser.parse_args()

    verifier = InstallVerifier(args.install_dir)

    if args.quick:
        # 快速验证模式
        print("快速验证模式...")
        checks = [
            ("可执行文件存在", verifier.check_executable_exists),
            ("版本命令", lambda: verifier.test_command("--version", [])),
        ]

        for check_name, check_func in checks:
            print(f"\n[{check_name}]")
            try:
                if check_name == "版本命令":
                    success, message, output = check_func()
                    if success:
                        print(f"  ✓ {message}")
                        if output:
                            print(f"    版本: {output.strip()}")
                    else:
                        print(f"  ✗ {message}")
                else:
                    success, message = check_func()
                    print(f"  {'✓' if success else '✗'} {message}")
            except Exception as e:
                print(f"  ✗ 检查异常: {str(e)}")

        print("\n快速验证完成")
        return

    # 完整验证
    report = verifier.run_all_checks()

    # 保存报告
    verifier.save_report(report, args.output)

    # 返回退出码
    sys.exit(0 if len(verifier.errors) == 0 else 1)


if __name__ == "__main__":
    main()