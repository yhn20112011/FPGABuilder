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
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

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
        "": ["*.yaml", "*.yml", "*.tcl", "*.template", "*.md"],
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
    },
    keywords="fpga, build, automation, xilinx, vivado, quartus, hardware",
    license="MIT",
    platforms=["Windows", "Linux", "Mac OS-X"],
)