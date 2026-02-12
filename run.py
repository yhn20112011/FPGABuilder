#!/usr/bin/env python3
"""
FPGABuilder开发模式运行脚本

此脚本允许在不安装FPGABuilder的情况下直接运行工具。
使用方式：
  python run.py [命令] [参数...]

例如：
  python run.py --version
  python run.py init my_project --vendor xilinx
  python run.py build --help
"""

import sys
import os
import subprocess
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


def run_direct():
    """直接运行FPGABuilder"""
    from core.cli import main
    main()


def run_with_python():
    """通过python -m方式运行"""
    # 这种方法更接近实际安装后的运行方式
    cmd = [sys.executable, "-m", "fpga_builder.cli"] + sys.argv[1:]
    subprocess.run(cmd)


def setup_dev_environment():
    """设置开发环境"""
    print("设置FPGABuilder开发环境...")

    # 检查虚拟环境
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  警告：不在虚拟环境中运行，建议使用虚拟环境")

    # 检查依赖
    print("检查依赖...")
    try:
        import click
        import yaml
        import rich
        print("✅ 核心依赖已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("运行: pip install -r requirements.txt")
        return False

    return True


def run_tests():
    """运行测试"""
    print("运行测试...")
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    if len(sys.argv) > 2:
        cmd.extend(sys.argv[2:])
    subprocess.run(cmd)


def run_type_check():
    """运行类型检查"""
    print("运行类型检查...")
    cmd = [sys.executable, "-m", "mypy", "src/", "--ignore-missing-imports"]
    subprocess.run(cmd)


def run_lint():
    """运行代码检查"""
    print("运行代码检查...")
    cmd = [sys.executable, "-m", "flake8", "src/", "tests/", "--max-line-length=88"]
    subprocess.run(cmd)


def run_format():
    """格式化代码"""
    print("格式化代码...")
    cmd = [sys.executable, "-m", "black", "src/", "tests/"]
    subprocess.run(cmd)


def show_help():
    """显示帮助信息"""
    print("""
FPGABuilder 开发工具

使用方法:
  python run.py [选项] [命令] [参数...]

开发命令:
  dev                直接运行FPGABuilder（开发模式）
  test               运行测试
  lint               运行代码检查
  type-check         运行类型检查
  format             格式化代码
  setup              设置开发环境

常规命令:
  --version          显示版本
  --help             显示此帮助信息
  [任意CLI命令]      直接传递给FPGABuilder CLI

示例:
  python run.py dev --version
  python run.py dev init my_project --vendor xilinx
  python run.py test
  python run.py lint
  python run.py format
""")


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]

    if command == "dev":
        # 移除dev参数，将剩余参数传递给CLI
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        run_direct()
    elif command == "test":
        run_tests()
    elif command == "lint":
        run_lint()
    elif command == "type-check":
        run_type_check()
    elif command == "format":
        run_format()
    elif command == "setup":
        setup_dev_environment()
    elif command == "--help" or command == "-h":
        show_help()
    elif command == "--version" or command == "-v":
        # 直接导入并显示版本
        sys.argv = ["--version"]
        run_direct()
    else:
        # 假设是直接传递给FPGABuilder的命令
        # 但需要移除脚本名参数
        sys.argv = sys.argv[1:]
        run_direct()


if __name__ == "__main__":
    main()