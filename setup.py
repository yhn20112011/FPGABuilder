#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os
import re

# 读取版本号
with open(os.path.join(os.path.dirname(__file__), 'src', 'core', '__init__.py'), 'r', encoding='utf-8') as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        version = '0.1.0'

# 读取README
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# 读取依赖
try:
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except FileNotFoundError:
    # 如果requirements.txt不存在，使用硬编码的依赖列表
    requirements = [
        'click>=8.0.0',
        'pyyaml>=6.0',
        'colorama>=0.4.6',
        'toml>=0.10.0',
        'jsonschema>=4.0.0',
        'pydantic>=2.0.0',
        'tqdm>=4.65.0',
        'rich>=13.0.0',
        'prompt-toolkit>=3.0.0',
        'questionary>=2.0.0',
        'python-dotenv>=1.0.0',
        'watchdog>=3.0.0',
        'pywin32>=305; sys_platform == "win32"',
        'gitpython>=3.1.0',
        'requests>=2.31.0',
        'aiohttp>=3.8.0',
    ]
    print("警告: requirements.txt未找到，使用默认依赖列表")

setup(
    name="FPGABuilder",
    version=version,
    author="FPGABuilder Team",
    author_email="support@example.com",
    description="跨平台FPGA自动构建工具链",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/FPGABuilder",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/FPGABuilder/issues",
        "Documentation": "https://yourusername.github.io/FPGABuilder/",
        "Source Code": "https://github.com/yourusername/FPGABuilder",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.tcl", "*.template", "*.md", "*.txt"],
        "fpga_builder": ["config/*.yaml", "config/templates/*", "templates/*"],
    },
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "FPGABuilder=core.cli:main",
            "fpgab=core.cli:main",  # 短别名
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "twine>=4.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
            "mkdocstrings>=0.23.0",
        ],
        "packaging": [
            "pyinstaller>=5.0.0",
            "setuptools>=65.0.0",
            "wheel>=0.40.0",
        ],
        "gui": [
            "windows-curses>=2.3.0; sys_platform == 'win32'",
            "curses>=2.2; sys_platform != 'win32'",
        ],
        "vivado": [
            # Vivado相关额外依赖
        ],
        "quartus": [
            # Quartus相关额外依赖
        ],
        "full": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
            "mkdocstrings>=0.23.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pyinstaller>=5.0.0",
            "windows-curses>=2.3.0; sys_platform == 'win32'",
        ],
    },
    keywords="fpga, build, automation, xilinx, vivado, quartus, hardware",
    license="MIT",
    platforms=["Windows", "Linux", "Mac OS-X"],
)