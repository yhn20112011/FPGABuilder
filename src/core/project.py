#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目管理模块
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import git
from .config import ConfigManager, ConfigError


class ProjectError(Exception):
    """项目错误异常"""
    pass


class ProjectManager:
    """项目管理器"""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.project_path = None
        self.project_config = None

    def set_project_path(self, project_path: Union[str, Path]) -> None:
        """设置项目路径"""
        self.project_path = Path(project_path).resolve()
        self._load_project_config()

    def _load_project_config(self) -> None:
        """加载项目配置"""
        if self.project_path is None:
            raise ProjectError("未设置项目路径")

        config_file = self.config_manager.find_config_file(self.project_path)
        if config_file is None:
            raise ProjectError(f"未找到项目配置文件: {self.project_path}")

        try:
            self.project_config = self.config_manager.load_config(config_file)
        except ConfigError as e:
            raise ProjectError(f"加载项目配置失败: {e}")

    def create_project(self, project_name: str, target_path: Union[str, Path],
                      vendor: str, part: str, template: str = 'basic') -> Path:
        """创建新项目"""
        target_path = Path(target_path)
        project_path = target_path / project_name

        # 检查项目目录是否已存在
        if project_path.exists():
            raise ProjectError(f"项目目录已存在: {project_path}")

        try:
            # 创建项目目录结构
            self._create_project_structure(project_path)

            # 创建默认配置
            config = self.config_manager.create_default_config(
                project_name, vendor, part, template
            )

            # 保存配置文件
            config_file = project_path / 'fpga_project.yaml'
            self.config_manager.save_config(config, config_file)

            # 设置项目路径和配置
            self.project_path = project_path
            self.project_config = config

            # 创建必要的模板文件
            self._create_template_files(project_path, template)

            return project_path

        except Exception as e:
            # 清理创建的项目目录
            if project_path.exists():
                shutil.rmtree(project_path, ignore_errors=True)
            raise ProjectError(f"创建项目失败: {e}")

    def _create_project_structure(self, project_path: Path) -> None:
        """创建项目目录结构"""
        directories = [
            'src/hdl',
            'src/constraints',
            'src/ip',
            'src/tb',  # 测试平台
            'ip_repo',
            'lib',
            'docs',
            'build/reports',
            'build/bitstreams',
            'build/logs',
            'build/checkpoints',
            'tests',
            'scripts'
        ]

        for directory in directories:
            (project_path / directory).mkdir(parents=True, exist_ok=True)

        # 创建.gitkeep文件以确保空目录被提交
        for directory in directories:
            (project_path / directory / '.gitkeep').touch(exist_ok=True)

    def _create_template_files(self, project_path: Path, template: str) -> None:
        """创建模板文件"""
        # 创建README.md
        readme_content = f"""# {project_path.name}

FPGA项目：{project_path.name}

## 项目描述

基于{template.upper()}模板创建的FPGA项目。

## 目录结构

- `src/hdl/` - HDL源代码
- `src/constraints/` - 约束文件
- `src/ip/` - IP核文件
- `src/tb/` - 测试平台
- `ip_repo/` - 第三方IP核仓库
- `lib/` - 第三方库
- `docs/` - 项目文档
- `build/` - 构建输出
- `tests/` - 测试文件
- `scripts/` - 脚本文件

## 构建说明

使用FPGABuilder构建项目：

```bash
# 进入项目目录
cd {project_path.name}

# 构建项目
FPGABuilder build

# 生成比特流
FPGABuilder bitstream
```

## 许可证

MIT License
"""

        with open(project_path / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)

        # 创建.gitignore文件
        gitignore_content = """# FPGA生成文件
/.Xil
*.log
*.jou
*.str
*.dcp
*.bit
*.bin
*.ltx
*.mcs
*.prm
*.xpr
*.hw
*.hwdef
*.xsa
*.xpfm

# 构建输出
/build/
*.egg-info/
__pycache__/
*.py[cod]

# 环境文件
.env
.venv
env/

# 编辑器文件
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db
"""

        with open(project_path / '.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)

        # 根据模板创建示例文件
        if template == 'zynq':
            self._create_zynq_template_files(project_path)
        elif template == 'basic':
            self._create_basic_template_files(project_path)

    def _create_zynq_template_files(self, project_path: Path) -> None:
        """创建Zynq模板文件"""
        # 创建示例Verilog顶层文件
        top_module = self.project_config.get('fpga.top_module', 'top')
        verilog_content = f"""// {top_module}.v
// Zynq FPGA顶层模块

module {top_module} (
    input wire clk,
    input wire rst_n,
    output wire [7:0] leds
);

// 时钟和复位处理
reg [31:0] counter;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        counter <= 32'h0;
    end else begin
        counter <= counter + 1;
    end
end

// LED显示计数器高8位
assign leds = counter[31:24];

endmodule
"""

        with open(project_path / 'src/hdl' / f'{top_module}.v', 'w', encoding='utf-8') as f:
            f.write(verilog_content)

        # 创建约束文件示例
        constraints_content = """# 时钟约束
create_clock -name clk -period 10.000 [get_ports clk]

# 引脚约束
set_property PACKAGE_PIN Y9 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]

set_property PACKAGE_PIN T22 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

set_property PACKAGE_PIN {U14 V14 V15 W15} [get_ports {leds[*]}]
set_property IOSTANDARD LVCMOS33 [get_ports {leds[*]}]
"""

        with open(project_path / 'src/constraints' / 'constraints.xdc', 'w', encoding='utf-8') as f:
            f.write(constraints_content)

    def _create_basic_template_files(self, project_path: Path) -> None:
        """创建基础模板文件"""
        top_module = self.project_config.get('fpga.top_module', 'top')
        verilog_content = f"""// {top_module}.v
// FPGA顶层模块

module {top_module} (
    input wire clk,
    input wire rst_n,
    output wire [3:0] leds
);

// 简单计数器示例
reg [23:0] counter;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        counter <= 24'h0;
    end else begin
        counter <= counter + 1;
    end
end

// LED显示计数器高4位
assign leds = counter[23:20];

endmodule
"""

        with open(project_path / 'src/hdl' / f'{top_module}.v', 'w', encoding='utf-8') as f:
            f.write(verilog_content)

    def initialize_git_repo(self) -> bool:
        """初始化Git仓库"""
        if self.project_path is None:
            raise ProjectError("未设置项目路径")

        try:
            repo = git.Repo.init(self.project_path)

            # 添加初始提交
            repo.git.add(all=True)
            repo.index.commit("Initial commit: Project created with FPGABuilder")

            return True
        except Exception as e:
            raise ProjectError(f"初始化Git仓库失败: {e}")

    def add_git_submodule(self, path: str, url: str, branch: Optional[str] = None) -> bool:
        """添加Git子模块"""
        if self.project_path is None:
            raise ProjectError("未设置项目路径")

        try:
            repo = git.Repo(self.project_path)

            submodule_path = Path(self.project_path) / path
            if submodule_path.exists():
                raise ProjectError(f"子模块路径已存在: {path}")

            # 添加子模块
            if branch:
                repo.create_submodule(path, path, url=url, branch=branch)
            else:
                repo.create_submodule(path, path, url=url)

            # 更新子模块
            repo.git.submodule('update', '--init', '--recursive')

            return True
        except Exception as e:
            raise ProjectError(f"添加Git子模块失败: {e}")

    def update_git_submodules(self) -> bool:
        """更新Git子模块"""
        if self.project_path is None:
            raise ProjectError("未设置项目路径")

        try:
            repo = git.Repo(self.project_path)
            repo.git.submodule('update', '--init', '--recursive')
            repo.git.submodule('foreach', 'git', 'pull', 'origin', 'master')
            return True
        except Exception as e:
            raise ProjectError(f"更新Git子模块失败: {e}")

    def get_source_files(self) -> List[Path]:
        """获取所有源文件"""
        if self.project_path is None or self.project_config is None:
            raise ProjectError("项目未初始化")

        source_files = []
        source_config = self.project_config.get('source', {})

        # 获取HDL文件
        hdl_files = source_config.get('hdl', [])
        for hdl_config in hdl_files:
            pattern = hdl_config.get('path')
            if pattern:
                files = list(self.project_path.glob(pattern))
                source_files.extend(files)

        # 获取约束文件
        constraint_files = source_config.get('constraints', [])
        for constraint_config in constraint_files:
            pattern = constraint_config.get('path')
            if pattern:
                files = list(self.project_path.glob(pattern))
                source_files.extend(files)

        return source_files

    def validate_project(self) -> Dict[str, Any]:
        """验证项目结构"""
        if self.project_path is None:
            raise ProjectError("未设置项目路径")

        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'details': {}
        }

        # 检查必要的目录
        required_dirs = ['src/hdl', 'src/constraints', 'build']
        for dir_name in required_dirs:
            dir_path = self.project_path / dir_name
            if not dir_path.exists():
                validation_result['valid'] = False
                validation_result['errors'].append(f"缺少必要目录: {dir_name}")

        # 检查配置文件
        config_file = self.project_path / 'fpga_project.yaml'
        if not config_file.exists():
            validation_result['valid'] = False
            validation_result['errors'].append("缺少配置文件: fpga_project.yaml")

        # 检查源文件
        source_files = self.get_source_files()
        if not source_files:
            validation_result['warnings'].append("未找到源文件")

        validation_result['details']['source_files'] = [
            str(f.relative_to(self.project_path)) for f in source_files
        ]

        return validation_result

    def clean_build_files(self) -> bool:
        """清理构建文件"""
        if self.project_path is None:
            raise ProjectError("未设置项目路径")

        build_dir = self.project_path / 'build'
        if build_dir.exists():
            try:
                shutil.rmtree(build_dir)
                build_dir.mkdir(parents=True, exist_ok=True)

                # 重新创建必要的子目录
                for subdir in ['reports', 'bitstreams', 'logs', 'checkpoints']:
                    (build_dir / subdir).mkdir(exist_ok=True)
                    (build_dir / subdir / '.gitkeep').touch(exist_ok=True)

                return True
            except Exception as e:
                raise ProjectError(f"清理构建文件失败: {e}")

        return True

    def export_project(self, export_path: Union[str, Path]) -> Path:
        """导出项目"""
        if self.project_path is None:
            raise ProjectError("未设置项目路径")

        export_path = Path(export_path)

        try:
            # 创建导出目录
            export_path.mkdir(parents=True, exist_ok=True)

            # 复制项目文件（排除构建文件）
            exclude_patterns = [
                'build/**',
                '.git/**',
                '__pycache__/**',
                '*.pyc',
                '*.log',
                '*.jou'
            ]

            # 使用shutil.copytree（简化实现）
            for item in self.project_path.iterdir():
                if item.name == 'build':
                    continue
                if item.is_file():
                    shutil.copy2(item, export_path / item.name)
                elif item.is_dir() and item.name != '.git':
                    shutil.copytree(item, export_path / item.name,
                                   dirs_exist_ok=True)

            return export_path
        except Exception as e:
            raise ProjectError(f"导出项目失败: {e}")

    def get_project_info(self) -> Dict[str, Any]:
        """获取项目信息"""
        if self.project_path is None or self.project_config is None:
            raise ProjectError("项目未初始化")

        project_config = self.project_config.get('project', {})
        fpga_config = self.project_config.get('fpga', {})

        source_files = self.get_source_files()

        return {
            'name': project_config.get('name', 'Unknown'),
            'version': project_config.get('version', '1.0.0'),
            'description': project_config.get('description', ''),
            'path': str(self.project_path),
            'fpga_vendor': fpga_config.get('vendor', 'Unknown'),
            'fpga_part': fpga_config.get('part', 'Unknown'),
            'top_module': fpga_config.get('top_module', 'Unknown'),
            'source_file_count': len(source_files),
            'source_files': [str(f.relative_to(self.project_path)) for f in source_files[:10]],  # 只显示前10个
            'has_git': (self.project_path / '.git').exists()
        }