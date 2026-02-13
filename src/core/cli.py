#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FPGABuilder命令行接口
"""

import os
import sys
import click
from pathlib import Path
from typing import Optional

from .config import ConfigManager
from .project import ProjectManager
from .plugin_manager import PluginManager
# 直接导入Vivado插件以避免插件发现问题
try:
    from plugins.vivado.plugin import VivadoPlugin
except ImportError:
    VivadoPlugin = None


class CLI:
    """命令行接口类"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.project_manager = ProjectManager()
        self.plugin_manager = PluginManager()

    def run(self, args=None):
        """运行命令行接口"""
        if args is None:
            args = sys.argv[1:]

        # 使用Click实现命令行解析
        cli()

    @staticmethod
    def _execute_hook(hook_config, hook_name):
        """执行钩子命令并处理错误"""
        import subprocess
        import shutil
        from pathlib import Path

        if not hook_config:
            return True  # 无钩子配置，继续

        click.echo(f"执行 {hook_name} 钩子...")

        # 支持字符串或字符串数组
        if isinstance(hook_config, list):
            commands = hook_config
        else:
            # 字符串，按换行符分割，过滤空行
            commands = [cmd.strip() for cmd in str(hook_config).split('\n') if cmd.strip()]

        for cmd in commands:
            click.echo(f"  运行: {cmd}")

            # 检查是否为文件路径
            cmd_path = Path(cmd)
            if cmd_path.exists() and cmd_path.is_file():
                # 如果是脚本文件，根据扩展名决定如何执行
                if cmd_path.suffix in ['.py', '.pyw']:
                    # Python脚本
                    full_cmd = [sys.executable, str(cmd_path)]
                elif cmd_path.suffix in ['.sh', '.bash']:
                    # Shell脚本
                    if os.name == 'nt':
                        full_cmd = ['bash', str(cmd_path)]
                    else:
                        full_cmd = ['bash', str(cmd_path)]
                elif cmd_path.suffix in ['.tcl']:
                    # TCL脚本，通过Vivado执行？这里简单使用source命令
                    # 实际应该在Vivado环境中执行，这里跳过文件检查
                    click.echo(f"  警告: TCL脚本应在Vivado环境中执行，跳过")
                    continue
                else:
                    # 其他文件，尝试作为可执行文件
                    full_cmd = [str(cmd_path)]
            else:
                # 直接命令
                # 在Windows上使用shell=True，以便支持内部命令
                full_cmd = cmd
                shell = True

            try:
                # 执行命令
                if isinstance(full_cmd, list):
                    # 列表形式，使用subprocess.run
                    result = subprocess.run(full_cmd, capture_output=True, text=True, shell=False)
                else:
                    # 字符串形式，使用shell
                    result = subprocess.run(full_cmd, capture_output=True, text=True, shell=True)

                if result.returncode != 0:
                    click.echo(f"  错误: 钩子命令执行失败 (退出码: {result.returncode})")
                    click.echo(f"  标准输出: {result.stdout}")
                    click.echo(f"  标准错误: {result.stderr}")

                    # 询问用户是否继续
                    if not click.confirm(f"{hook_name} 钩子执行失败，是否继续构建？", default=False):
                        return False
                    else:
                        click.echo("  用户选择继续构建")
                else:
                    click.echo(f"  成功: {result.stdout}")

            except Exception as e:
                click.echo(f"  异常: 执行钩子命令时出错: {e}")
                if not click.confirm(f"{hook_name} 钩子执行出错，是否继续构建？", default=False):
                    return False
                else:
                    click.echo("  用户选择继续构建")

        return True  # 继续构建


# Click命令组
@click.group()
@click.version_option(version="0.2.0", prog_name="FPGABuilder")
@click.option('-c', '--config', type=click.Path(exists=True),
              help='指定配置文件')
@click.option('-v', '--verbose', is_flag=True, help='详细输出')
@click.pass_context
def cli(ctx, config, verbose):
    """FPGABuilder - FPGA自动构建工具链"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose

    # 初始化配置
    if config:
        ctx.obj['config_manager'] = ConfigManager(config_path=Path(config))
    else:
        ctx.obj['config_manager'] = ConfigManager()

    # 初始化插件管理器
    ctx.obj['plugin_manager'] = PluginManager()
    ctx.obj['plugin_manager'].discover_plugins()


# init命令
@cli.command()
@click.argument('project_name')
@click.option('--vendor', type=click.Choice(['xilinx', 'altera', 'lattice']),
              default='xilinx', help='FPGA厂商')
@click.option('--part', help='FPGA器件型号')
@click.option('--template', type=click.Choice(['basic', 'zynq', 'versal']),
              default='basic', help='工程模板')
@click.option('--path', type=click.Path(), default='.',
              help='工程创建路径')
@click.pass_context
def init(ctx, project_name, vendor, part, template, path):
    """初始化新的FPGA工程"""
    config_manager = ctx.obj['config_manager']

    click.echo(f"初始化工程: {project_name}")
    click.echo(f"FPGA厂商: {vendor}")
    click.echo(f"器件型号: {part}")
    click.echo(f"模板: {template}")

    # 创建工程目录
    project_path = Path(path) / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    # 生成基础工程配置
    config = {
        'project': {
            'name': project_name,
            'version': '1.0.0',
            'description': f'{project_name} FPGA工程'
        },
        'fpga': {
            'vendor': vendor,
            'part': part
        },
        'template': template
    }

    # 根据模板类型增强配置
    if template == 'zynq':
        # Zynq模板特有配置
        config['fpga']['family'] = 'zynq-7000'
        config['fpga']['top_module'] = f'{project_name}_wrapper'
        # 添加建议的Zynq构建配置
        config['build'] = {
            'synthesis': {'strategy': 'Vivado Synthesis Defaults'},
            'implementation': {'options': {}},
            'bitstream': {'options': {'bin_file': True}}
        }
        # 添加Zynq特定约束文件提示
        config['source'] = {
            'hdl': [{'path': 'src/hdl/**/*.v', 'language': 'verilog'}],
            'constraints': [{'path': 'src/constraints/*.xdc', 'type': 'xilinx'}]
        }
    elif template == 'versal':
        # Versal模板配置
        config['fpga']['family'] = 'versal'
        config['fpga']['top_module'] = f'{project_name}_wrapper'
    # basic模板保持默认配置

    # 保存配置
    config_path = project_path / 'fpga_project.yaml'
    config_manager.save_config(config, config_path)

    # 创建标准工程结构
    click.echo("创建工程目录结构...")
    create_project_structure(path, project_name)

    # 根据模板创建示例文件
    if template == 'zynq':
        # 创建示例Zynq顶层文件
        example_hdl_dir = project_path / 'src' / 'hdl'
        example_hdl_dir.mkdir(parents=True, exist_ok=True)
        example_top_file = example_hdl_dir / f'{project_name}_top.v'
        with open(example_top_file, 'w', encoding='utf-8') as f:
            f.write(f'''// {project_name} 顶层模块
// 由FPGABuilder自动生成

module {project_name}_top (
    input wire clk,
    input wire rst_n,
    input wire [7:0] data_in,
    output wire [7:0] data_out,
    output wire valid_out
);

    // 示例：简单的流水线寄存器
    reg [7:0] data_reg;
    reg valid_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_reg <= 8'h0;
            valid_reg <= 1'b0;
        end else begin
            data_reg <= data_in;
            valid_reg <= 1'b1;
        end
    end

    assign data_out = data_reg;
    assign valid_out = valid_reg;

endmodule
''')
        click.echo(f"创建示例顶层文件: {example_top_file}")

        # 创建示例约束文件
        example_constraint_dir = project_path / 'src' / 'constraints'
        example_constraint_dir.mkdir(parents=True, exist_ok=True)
        example_constraint_file = example_constraint_dir / 'clocks.xdc'
        with open(example_constraint_file, 'w', encoding='utf-8') as f:
            f.write(f'''# {project_name} 时钟和引脚约束
# 由FPGABuilder自动生成
# 基于ZC706开发板（xc7z045ffg676-2）的示例引脚分配
# 实际使用请根据硬件修改引脚分配

# 时钟约束（板上125MHz时钟）
create_clock -name clk -period 8.000 [get_ports clk]

# 电气标准约束
set_property IOSTANDARD LVCMOS33 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports data_in[*]]
set_property IOSTANDARD LVCMOS33 [get_ports data_out[*]]
set_property IOSTANDARD LVCMOS33 [get_ports valid_out]

# 引脚分配（ZC706开发板示例引脚 - 简化版本，实际使用请修改）
# 时钟引脚
set_property PACKAGE_PIN AC21 [get_ports clk]
# 复位引脚
set_property PACKAGE_PIN AB10 [get_ports rst_n]
# 数据输入引脚（示例：所有data_in位连接到同一引脚，实际应分别分配）
set_property PACKAGE_PIN AA10 [get_ports data_in[*]]
# 数据输出引脚（示例：所有data_out位连接到同一引脚，实际应分别分配）
set_property PACKAGE_PIN AB11 [get_ports data_out[*]]
# 有效输出引脚
set_property PACKAGE_PIN AC11 [get_ports valid_out]

# 降低DRC检查严重性，避免未约束端口错误
# 在实际设计中，应为所有端口添加正确的引脚约束
set_property SEVERITY {{Warning}} [get_drc_checks UCIO-1]
''')
        click.echo(f"创建示例约束文件: {example_constraint_file}")

        # 提示信息
        click.echo("\n" + "="*60)
        click.echo("Zynq工程创建完成！")
        click.echo("下一步：")
        click.echo(f"  1. 进入工程目录: cd {project_path}")
        click.echo(f"  2. 编辑约束文件: {example_constraint_file}")
        click.echo(f"     - 根据实际硬件修改引脚分配")
        click.echo(f"     - 为所有端口添加正确的引脚约束")
        click.echo("  3. 运行构建: FPGABuilder build")
        click.echo("  4. 如有DRC错误，请参考约束文件中的注释")
        click.echo("="*60)

    click.echo(f"工程已创建: {project_path}")
    click.echo(f"配置文件: {config_path}")


# create命令
@cli.command()
@click.option('--type', type=click.Choice(['project', 'ip', 'hls']),
              default='project', help='创建类型')
@click.option('--name', help='名称')
@click.option('--output', type=click.Path(), default='.',
              help='输出路径')
@click.pass_context
def create(ctx, type, name, output):
    """创建工程结构或IP核"""
    click.echo(f"创建 {type}: {name}")

    if type == 'project':
        # 创建标准工程结构
        create_project_structure(output, name)
    elif type == 'ip':
        # 创建IP核
        create_ip_core(output, name)
    elif type == 'hls':
        # 创建HLS工程
        create_hls_project(output, name)


# config命令
@cli.command()
@click.option('--gui/--no-gui', default=True,
              help='使用图形界面配置')
@click.pass_context
def config(ctx, gui):
    """配置工程"""
    if gui:
        click.echo("启动交互式配置界面...")
        # 调用menuconfig界面
        run_menuconfig()
    else:
        click.echo("文本模式配置")
        # 显示当前配置
        show_config()


# build命令
@cli.command()
@click.option('--target', type=click.Choice(['synth', 'impl', 'bitstream', 'all']),
              default='all', help='构建目标')
@click.option('--jobs', '-j', default=4, help='并行作业数')
@click.pass_context
def build(ctx, target, jobs):
    """构建工程"""
    click.echo(f"构建目标: {target}")
    click.echo(f"并行作业: {jobs}")

    # 获取配置管理器和插件管理器
    config_manager = ctx.obj['config_manager']
    plugin_manager = ctx.obj['plugin_manager']

    # 查找配置文件
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件 (fpga_project.yaml)")
        return

    # 加载配置
    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 获取FPGA厂商
    vendor = config.get('fpga', {}).get('vendor', 'xilinx')
    if vendor not in ['xilinx', 'altera', 'lattice']:
        click.echo(f"[ERROR] 不支持的FPGA厂商: {vendor}")
        return

    # 执行pre-build钩子（如果有）
    hooks = config.get('build', {}).get('hooks', {})
    pre_build_hook = hooks.get('pre_build')
    if pre_build_hook:
        if not CLI._execute_hook(pre_build_hook, 'pre-build'):
            click.echo("构建被用户取消")
            return

    # 获取插件（临时直接实例化Vivado插件，避免插件发现问题）
    plugin = None
    if vendor == 'xilinx':
        if VivadoPlugin is None:
            click.echo("[ERROR] 无法导入Vivado插件")
            return
        plugin = VivadoPlugin()
    else:
        click.echo(f"[ERROR] 暂不支持的FPGA厂商: {vendor}")
        return

    # 执行构建目标
    try:
        if target == 'all':
            click.echo("运行综合...")
            synth_result = plugin.synthesize(config)
            if not synth_result.success:
                click.echo("[ERROR] 综合失败")
                return
            click.echo("运行实现...")
            impl_result = plugin.implement(config)
            if not impl_result.success:
                click.echo("[ERROR] 实现失败")
                return
            click.echo("生成比特流...")
            bit_result = plugin.generate_bitstream(config)
            if not bit_result.success:
                click.echo("[ERROR] 比特流生成失败")
                return
            click.echo("[OK] 构建完成")
            # 执行post-bitstream钩子（如果有）
            post_bitstream_hook = hooks.get('post_bitstream')
            if post_bitstream_hook:
                if not CLI._execute_hook(post_bitstream_hook, 'post-bitstream'):
                    click.echo("警告: post-bitstream钩子执行失败，但构建已完成")
        elif target == 'synth':
            click.echo("运行综合...")
            result = plugin.synthesize(config)
            if result.success:
                click.echo("[OK] 综合完成")
            else:
                click.echo("[ERROR] 综合失败")
        elif target == 'impl':
            click.echo("运行实现...")
            result = plugin.implement(config)
            if result.success:
                click.echo("[OK] 实现完成")
            else:
                click.echo("[ERROR] 实现失败")
        elif target == 'bitstream':
            click.echo("生成比特流...")
            result = plugin.generate_bitstream(config)
            if result.success:
                click.echo("[OK] 比特流生成完成")
                # 执行post-bitstream钩子（如果有）
                post_bitstream_hook = hooks.get('post_bitstream')
                if post_bitstream_hook:
                    if not CLI._execute_hook(post_bitstream_hook, 'post-bitstream'):
                        click.echo("警告: post-bitstream钩子执行失败，但构建已完成")
            else:
                click.echo("[ERROR] 比特流生成失败")
    except Exception as e:
        click.echo(f"[ERROR] 构建过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


# synth命令
@cli.command()
@click.option('--jobs', '-j', default=4, help='并行作业数')
@click.pass_context
def synth(ctx, jobs):
    """运行综合"""
    click.echo(f"运行综合，作业数: {jobs}")
    run_synthesis(jobs)


# impl命令
@cli.command()
@click.option('--jobs', '-j', default=4, help='并行作业数')
@click.pass_context
def impl(ctx, jobs):
    """运行实现（布局布线）"""
    click.echo(f"运行实现，作业数: {jobs}")
    run_implementation(jobs)


# bitstream命令
@cli.command()
@click.pass_context
def bitstream(ctx):
    """生成比特流"""
    click.echo("生成比特流")
    run_bitstream_generation()


# program命令
@cli.command()
@click.option('--cable', default='xilinx_tcf', help='编程电缆类型')
@click.option('--target', default='hw_server:3121', help='硬件服务器地址')
@click.option('--bitfile', type=click.Path(exists=True),
              help='比特流文件路径')
@click.pass_context
def program(ctx, cable, target, bitfile):
    """烧录设备"""
    click.echo(f"烧录设备，电缆: {cable}, 目标: {target}")
    if bitfile:
        click.echo(f"使用比特流文件: {bitfile}")
    program_device(cable, target, bitfile)


# ip命令组
@cli.group()
def ip():
    """IP核管理"""
    pass


@ip.command()
@click.argument('name')
@click.option('--type', help='IP核类型')
@click.option('--interface', help='接口类型')
def create(name, type, interface):
    """创建IP核"""
    click.echo(f"创建IP核: {name}")
    click.echo(f"类型: {type}")
    click.echo(f"接口: {interface}")
    create_ip_core(name, type, interface)


@ip.command()
@click.argument('name')
@click.option('--output', type=click.Path(), default='.',
              help='输出路径')
def package(name, output):
    """打包IP核"""
    click.echo(f"打包IP核: {name}")
    click.echo(f"输出路径: {output}")
    package_ip_core(name, output)


# hls命令组
@cli.group()
def hls():
    """HLS工程管理"""
    pass


@hls.command()
@click.argument('name')
@click.option('--language', default='c++', help='HLS语言')
def create(name, language):
    """创建HLS工程"""
    click.echo(f"创建HLS工程: {name}")
    click.echo(f"语言: {language}")
    create_hls_project(name, language)


@hls.command()
@click.argument('name')
@click.option('--solution', default='solution1', help='解决方案名称')
def compile(name, solution):
    """编译HLS工程"""
    click.echo(f"编译HLS工程: {name}")
    click.echo(f"解决方案: {solution}")
    compile_hls_project(name, solution)


@cli.command()
@click.pass_context
def gui(ctx):
    """打开厂商开发工具GUI（准备工程、导入文件、恢复BD，但不运行综合）"""
    click.echo("准备工程并打开厂商开发工具GUI...")

    # 获取配置管理器和插件管理器
    config_manager = ctx.obj['config_manager']
    plugin_manager = ctx.obj['plugin_manager']

    # 查找配置文件
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件 (fpga_project.yaml)")
        return

    # 加载配置
    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 获取FPGA厂商
    vendor = config.get('fpga', {}).get('vendor', 'xilinx')
    if vendor not in ['xilinx', 'altera', 'lattice']:
        click.echo(f"[ERROR] 不支持的FPGA厂商: {vendor}")
        return

    # 获取插件（临时直接实例化Vivado插件，避免插件发现问题）
    plugin = None
    if vendor == 'xilinx':
        if VivadoPlugin is None:
            click.echo("[ERROR] 无法导入Vivado插件")
            return
        plugin = VivadoPlugin()
        # 调用prepare_and_open_gui方法
        result = plugin.prepare_and_open_gui(config)
    else:
        click.echo(f"[ERROR] 暂不支持的FPGA厂商: {vendor}")
        return

    # 处理结果
    if result.success:
        click.echo("[OK] 工程准备完成，GUI已打开")
        if result.artifacts:
            for key, value in result.artifacts.items():
                click.echo(f"  {key}: {value}")
    else:
        click.echo("[ERROR] 工程准备或GUI打开失败")
        if result.errors:
            for error in result.errors:
                click.echo(f"  {error}")


# vivado命令组
@cli.group()
def vivado():
    """Vivado特定命令"""
    pass


@vivado.command()
@click.pass_context
def gui(ctx):
    """打开Vivado GUI界面"""
    click.echo("打开Vivado GUI...")

    # 获取配置
    config_manager = ctx.obj['config_manager']
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件")
        return

    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 创建Vivado插件实例
    if VivadoPlugin is None:
        click.echo("[ERROR] 无法导入Vivado插件")
        return

    plugin = VivadoPlugin()
    result = plugin.open_gui(config)

    if result.success:
        click.echo("[OK] Vivado GUI已启动")
    else:
        click.echo("[ERROR] 打开Vivado GUI失败")
        if result.errors:
            for error in result.errors:
                click.echo(f"  {error}")


@vivado.command()
@click.option('--level', type=click.Choice(['soft', 'hard', 'all']),
              default='soft', help='清理级别')
@click.pass_context
def clean(ctx, level):
    """清理构建文件"""
    click.echo(f"清理构建文件，级别: {level}")

    # 获取配置
    config_manager = ctx.obj['config_manager']
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件")
        return

    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 创建Vivado插件实例
    if VivadoPlugin is None:
        click.echo("[ERROR] 无法导入Vivado插件")
        return

    plugin = VivadoPlugin()
    result = plugin.clean_project(config, level)

    if result.success:
        click.echo(f"[OK] 清理完成（级别: {level}）")
    else:
        click.echo(f"[ERROR] 清理失败（级别: {level}）")
        if result.errors:
            for error in result.errors:
                click.echo(f"  {error}")


@vivado.command()
@click.option('--steps', type=click.Choice(['synth', 'impl', 'bitstream', 'all']),
              default='all', help='构建步骤')
@click.option('--jobs', '-j', default=4, help='并行作业数')
@click.pass_context
def build(ctx, steps, jobs):
    """完整构建流程"""
    click.echo(f"运行Vivado构建，步骤: {steps}, 作业数: {jobs}")

    # 获取配置
    config_manager = ctx.obj['config_manager']
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件")
        return

    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 创建Vivado插件实例
    if VivadoPlugin is None:
        click.echo("[ERROR] 无法导入Vivado插件")
        return

    plugin = VivadoPlugin()

    if steps == 'all':
        # 完整构建流程
        click.echo("运行综合...")
        synth_result = plugin.synthesize(config)
        if not synth_result.success:
            click.echo("[ERROR] 综合失败")
            return

        click.echo("运行实现...")
        impl_result = plugin.implement(config)
        if not impl_result.success:
            click.echo("[ERROR] 实现失败")
            return

        click.echo("生成比特流...")
        bit_result = plugin.generate_bitstream(config)
        if not bit_result.success:
            click.echo("[ERROR] 比特流生成失败")
            return

        click.echo("[OK] 构建完成")
    elif steps == 'synth':
        click.echo("运行综合...")
        result = plugin.synthesize(config)
        if result.success:
            click.echo("[OK] 综合完成")
        else:
            click.echo("[ERROR] 综合失败")
    elif steps == 'impl':
        click.echo("运行实现...")
        result = plugin.implement(config)
        if result.success:
            click.echo("[OK] 实现完成")
        else:
            click.echo("[ERROR] 实现失败")
    elif steps == 'bitstream':
        click.echo("生成比特流...")
        result = plugin.generate_bitstream(config)
        if result.success:
            click.echo("[OK] 比特流生成完成")
        else:
            click.echo("[ERROR] 比特流生成失败")


@vivado.command()
@click.pass_context
def import_files(ctx):
    """自动扫描并导入源文件"""
    click.echo("扫描并导入源文件...")

    # 获取配置
    config_manager = ctx.obj['config_manager']
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件")
        return

    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 创建Vivado插件实例
    if VivadoPlugin is None:
        click.echo("[ERROR] 无法导入Vivado插件")
        return

    plugin = VivadoPlugin()
    scan_result = plugin.scan_and_import_files(config)

    hdl_count = len(scan_result.get('scanned_files', {}).get('hdl', []))
    constraint_count = len(scan_result.get('scanned_files', {}).get('constraints', []))
    ip_count = len(scan_result.get('scanned_files', {}).get('ip_cores', []))

    click.echo(f"[OK] 扫描完成: {hdl_count} HDL文件, {constraint_count} 约束文件, {ip_count} IP核")
    click.echo("文件已准备好导入Vivado工程")


@vivado.command()
@click.option('--cable', default='xilinx_tcf', help='编程电缆类型')
@click.option('--target', default='hw_server:3121', help='硬件服务器地址')
@click.option('--bitfile', type=click.Path(exists=True),
              help='比特流文件路径')
@click.option('--flash', is_flag=True, help='烧录到Flash')
@click.pass_context
def program(ctx, cable, target, bitfile, flash):
    """烧录设备"""
    click.echo(f"烧录设备，电缆: {cable}, 目标: {target}")

    # 获取配置
    config_manager = ctx.obj['config_manager']
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件")
        return

    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 创建Vivado插件实例
    if VivadoPlugin is None:
        click.echo("[ERROR] 无法导入Vivado插件")
        return

    plugin = VivadoPlugin()

    # 更新配置中的编程选项
    if cable:
        config['programming'] = config.get('programming', {})
        config['programming']['cable'] = cable
    if target:
        config['programming'] = config.get('programming', {})
        config['programming']['target'] = target
    if bitfile:
        config['programming'] = config.get('programming', {})
        config['programming']['bitfile'] = bitfile
    if flash:
        config['programming'] = config.get('programming', {})
        config['programming']['flash'] = flash

    result = plugin.program_device(config, flash_mode=flash)

    if result.success:
        click.echo("[OK] 设备烧录完成")
    else:
        click.echo("[ERROR] 设备烧录失败")
        if result.errors:
            for error in result.errors:
                click.echo(f"  {error}")


@vivado.command()
@click.option('--type', type=click.Choice(['timing', 'utilization', 'power', 'all']),
              default='all', help='报告类型')
@click.option('--output', type=click.Path(), default='build/reports',
              help='输出目录')
@click.pass_context
def report(ctx, type, output):
    """生成构建报告"""
    click.echo(f"生成构建报告，类型: {type}, 输出: {output}")

    # 获取配置
    config_manager = ctx.obj['config_manager']
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件")
        return

    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    click.echo("[INFO] 报告生成功能开发中...")
    # TODO: 实现报告生成功能


@vivado.command()
@click.pass_context
def synth(ctx):
    """运行综合"""
    click.echo("运行Vivado综合...")

    # 获取配置
    config_manager = ctx.obj['config_manager']
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件")
        return

    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 创建Vivado插件实例
    if VivadoPlugin is None:
        click.echo("[ERROR] 无法导入Vivado插件")
        return

    plugin = VivadoPlugin()

    click.echo("运行综合...")
    result = plugin.synthesize(config)
    if result.success:
        click.echo("[OK] 综合完成")
    else:
        click.echo("[ERROR] 综合失败")


@vivado.command()
@click.pass_context
def impl(ctx):
    """运行实现（布局布线）"""
    click.echo("运行Vivado实现...")

    # 获取配置
    config_manager = ctx.obj['config_manager']
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件")
        return

    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 创建Vivado插件实例
    if VivadoPlugin is None:
        click.echo("[ERROR] 无法导入Vivado插件")
        return

    plugin = VivadoPlugin()

    click.echo("运行实现...")
    result = plugin.implement(config)
    if result.success:
        click.echo("[OK] 实现完成")
    else:
        click.echo("[ERROR] 实现失败")


@vivado.command()
@click.pass_context
def bitstream(ctx):
    """生成比特流"""
    click.echo("生成Vivado比特流...")

    # 获取配置
    config_manager = ctx.obj['config_manager']
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件")
        return

    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 创建Vivado插件实例
    if VivadoPlugin is None:
        click.echo("[ERROR] 无法导入Vivado插件")
        return

    plugin = VivadoPlugin()

    click.echo("生成比特流...")
    result = plugin.generate_bitstream(config)
    if result.success:
        click.echo("[OK] 比特流生成完成")
    else:
        click.echo("[ERROR] 比特流生成失败")


@vivado.command()
@click.option('--output', type=click.Path(), default='boot.bin',
              help='输出文件路径')
@click.option('--fsbl', type=click.Path(exists=True),
              help='FSBL文件路径')
@click.option('--fsbl-offset', default='0x00000000',
              help='FSBL偏移地址')
@click.option('--bitstream', type=click.Path(exists=True),
              help='比特流文件路径')
@click.option('--bitstream-offset', default='0x00100000',
              help='比特流偏移地址')
@click.option('--uboot', type=click.Path(exists=True),
              help='U-Boot文件路径')
@click.option('--uboot-offset', default='0x00200000',
              help='U-Boot偏移地址')
@click.option('--atf', type=click.Path(exists=True),
              help='ATF文件路径')
@click.option('--atf-offset', default='0x00300000',
              help='ATF偏移地址')
@click.option('--use-tcl/--use-script', default=True,
              help='使用TCL脚本或Python脚本')
@click.pass_context
def packbin(ctx, output, fsbl, fsbl_offset, bitstream, bitstream_offset,
            uboot, uboot_offset, atf, atf_offset, use_tcl):
    """生成二进制合并文件（boot.bin）"""
    click.echo("生成二进制合并文件...")

    # 获取配置
    config_manager = ctx.obj['config_manager']
    config_file = config_manager.find_config_file(Path.cwd())
    if not config_file:
        click.echo("[ERROR] 未找到项目配置文件")
        return

    try:
        config = config_manager.load_config(config_file)
    except Exception as e:
        click.echo(f"[ERROR] 加载配置文件失败: {e}")
        return

    # 创建Vivado插件实例
    if VivadoPlugin is None:
        click.echo("[ERROR] 无法导入Vivado插件")
        return

    plugin = VivadoPlugin()

    # 如果提供了命令行参数，更新配置
    if fsbl or bitstream or uboot or atf:
        bin_config = config.get('build', {}).get('bin_merge', {})
        if fsbl:
            bin_config['fsbl_path'] = str(fsbl)
            bin_config['fsbl_offset'] = fsbl_offset
        if bitstream:
            bin_config['bitstream_path'] = str(bitstream)
            bin_config['bitstream_offset'] = bitstream_offset
        if uboot:
            bin_config['uboot_path'] = str(uboot)
            bin_config['uboot_offset'] = uboot_offset
        if atf:
            bin_config['atf_path'] = str(atf)
            bin_config['atf_offset'] = atf_offset
        bin_config['output_path'] = str(output)

        # 更新配置
        if 'build' not in config:
            config['build'] = {}
        config['build']['bin_merge'] = bin_config

    # 执行packbin
    if use_tcl:
        # 使用TCL脚本（通过插件）
        result = plugin.packbin(config)
    else:
        # 使用Python脚本
        click.echo("使用Python脚本合并二进制文件...")
        try:
            import sys
            sys.path.append(str(Path(__file__).parent.parent))
            from scripts.merge_bin import BinMerger

            merger = BinMerger(output, 'zynq')
            if fsbl:
                merger.add_component(fsbl, fsbl_offset, 'fsbl', 'FSBL')
            if bitstream:
                merger.add_component(bitstream, bitstream_offset, 'bitstream', 'Bitstream')
            if uboot:
                merger.add_component(uboot, uboot_offset, 'uboot', 'U-Boot')
            if atf:
                merger.add_component(atf, atf_offset, 'atf', 'ATF')

            merger.merge_with_bootgen()
            result = type('obj', (object,), {'success': True, 'artifacts': {}, 'logs': {}})()
            result.success = True
            result.artifacts = {'bin_file': output}
            result.logs = {'method': 'python_script'}
        except Exception as e:
            click.echo(f"[ERROR] Python脚本执行失败: {e}")
            result = type('obj', (object,), {'success': False, 'errors': []})()
            result.success = False
            result.errors = [str(e)]

    if result.success:
        click.echo(f"[OK] 二进制合并文件生成完成: {output}")
        if result.artifacts:
            for key, value in result.artifacts.items():
                click.echo(f"  工件: {key} = {value}")
    else:
        click.echo("[ERROR] 二进制合并文件生成失败")
        if hasattr(result, 'errors') and result.errors:
            for error in result.errors:
                click.echo(f"  {error}")


# docs命令
@cli.command()
@click.option('--format', type=click.Choice(['mkdocs', 'doxygen', 'all']),
              default='mkdocs', help='文档格式')
@click.option('--output', type=click.Path(), default='docs',
              help='输出路径')
@click.pass_context
def docs(ctx, format, output):
    """生成文档"""
    click.echo(f"生成文档，格式: {format}, 输出: {output}")
    generate_documentation(format, output)


# clean命令
@cli.command()
@click.option('--all', is_flag=True, help='清理所有生成文件')
@click.pass_context
def clean(ctx, all):
    """清理构建文件"""
    if all:
        click.echo("清理所有生成文件")
        clean_all()
    else:
        click.echo("清理构建文件")
        clean_build()


# pack命令
@cli.command()
@click.option('--format', type=click.Choice(['zip', 'tar', 'installer']),
              default='zip', help='打包格式')
@click.option('--output', type=click.Path(), default='.',
              help='输出路径')
@click.pass_context
def pack(ctx, format, output):
    """打包发布"""
    click.echo(f"打包发布，格式: {format}, 输出: {output}")
    package_project(format, output)


@cli.command()
@click.option('--plugin', '-p', help='指定插件名称')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.pass_context
def compatibility(ctx, plugin, verbose):
    """检查插件兼容性"""
    from .plugin_manager import get_plugin_manager

    pm = get_plugin_manager()

    if plugin:
        # 检查特定插件
        plugin_instance = pm.get_plugin(plugin)
        if not plugin_instance:
            click.echo(f"[ERROR] 插件未找到: {plugin}")
            return

        click.echo(f"检查插件兼容性: {plugin}")
        report = plugin_instance.get_compatibility_report()
        click.echo(report)
    else:
        # 检查所有插件
        click.echo("检查所有插件兼容性...")
        summary = pm.get_compatibility_summary()
        click.echo(summary)

        if verbose:
            click.echo("\n" + "=" * 60)
            click.echo("详细兼容性报告:")
            detailed_report = pm.check_all_plugin_compatibility()

            for plugin_name, data in detailed_report.items():
                click.echo(f"\n{plugin_name}:")
                click.echo(f"  类型: {data['plugin_type']}")
                click.echo(f"  兼容: {'[OK] 是' if data['compatible'] else '[ERROR] 否'}")

                if data['tools']:
                    click.echo("  检测到的工具:")
                    for tool_name, tool_info in data['tools'].items():
                        status = "[OK]" if tool_info['compatible'] else "[ERROR]"
                        click.echo(f"    {status} {tool_name}: {tool_info['version']}")
                        if tool_info['path']:
                            click.echo(f"      路径: {tool_info['path']}")


# debug命令组
@cli.group()
def debug():
    """调试命令"""
    pass


# debug子命令示例
@debug.command()
@click.pass_context
def info(ctx):
    """显示调试信息"""
    click.echo("调试信息命令 - 开发中")


@debug.command()
@click.option('--level', type=click.Choice(['basic', 'detailed', 'full']),
              default='basic', help='详细级别')
@click.pass_context
def status(ctx, level):
    """显示系统状态"""
    click.echo(f"系统状态检查 - 级别: {level}")
    click.echo("状态检查功能开发中...")


@debug.command()
@click.option('--tests', '-t', is_flag=True, help='运行测试')
@click.option('--reports', '-r', is_flag=True, help='生成报告')
@click.pass_context
def verify(ctx, tests, reports):
    """验证系统配置"""
    click.echo("验证系统配置...")
    if tests:
        click.echo("运行测试...")
    if reports:
        click.echo("生成报告...")
    click.echo("验证功能开发中...")


# 工具函数
def create_project_structure(path, name):
    """创建标准工程结构"""
    base_path = Path(path) / name

    directories = [
        'src/hdl',
        'src/constraints',
        'src/ip',
        'ip_repo',
        'lib',
        'docs',
        'build/reports',
        'build/bitstreams',
        'build/logs',
        'tests'
    ]

    for directory in directories:
        (base_path / directory).mkdir(parents=True, exist_ok=True)

    click.echo(f"工程结构已创建: {base_path}")


def create_ip_core(name, ip_type, interface):
    """创建IP核"""
    # 实现IP核创建逻辑
    pass


def run_menuconfig():
    """运行menuconfig界面"""
    # 实现menuconfig界面
    pass


def show_config():
    """显示当前配置"""
    # 实现配置显示
    pass


def run_synthesis(jobs):
    """运行综合"""
    click.echo(f"运行综合，作业数: {jobs}")
    # 实现综合逻辑


def run_implementation(jobs):
    """运行实现"""
    click.echo(f"运行实现，作业数: {jobs}")
    # 实现实现逻辑


def run_bitstream_generation():
    """生成比特流"""
    click.echo("生成比特流")
    # 实现比特流生成逻辑


def program_device(cable, target, bitfile):
    """烧录设备"""
    click.echo(f"烧录设备: {cable}, {target}")
    # 实现烧录逻辑


def create_hls_project(name, language):
    """创建HLS工程"""
    # 实现HLS工程创建
    pass


def compile_hls_project(name, solution):
    """编译HLS工程"""
    # 实现HLS编译
    pass


def generate_documentation(format, output):
    """生成文档"""
    # 实现文档生成逻辑
    pass


def clean_all():
    """清理所有生成文件"""
    import os
    import shutil
    import glob
    from pathlib import Path

    cwd = Path.cwd()
    print(f"清理所有生成文件: {cwd}")

    # 删除build文件夹
    build_dir = cwd / "build"
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir)
            print(f"已删除构建目录: {build_dir}")
        except Exception as e:
            print(f"删除构建目录失败: {e}")

    # 删除所有.log和.jou文件
    log_files = list(cwd.glob("*.log")) + list(cwd.glob("*.jou"))
    for file in log_files:
        try:
            os.remove(file)
            print(f"已删除日志文件: {file}")
        except Exception as e:
            print(f"删除日志文件失败 {file}: {e}")

    # 递归查找并删除子目录中的.log和.jou文件
    for root, dirs, files in os.walk(cwd):
        for file in files:
            if file.endswith('.log') or file.endswith('.jou'):
                file_path = Path(root) / file
                try:
                    os.remove(file_path)
                    print(f"已删除日志文件: {file_path}")
                except Exception as e:
                    print(f"删除日志文件失败 {file_path}: {e}")

    print("所有生成文件清理完成")


def clean_build():
    """清理构建文件"""
    import os
    import shutil
    from pathlib import Path

    cwd = Path.cwd()
    print(f"清理构建文件: {cwd}")

    # 删除build文件夹
    build_dir = cwd / "build"
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir)
            print(f"已删除构建目录: {build_dir}")
        except Exception as e:
            print(f"删除构建目录失败: {e}")

    # 删除当前目录的.log和.jou文件
    log_files = list(cwd.glob("*.log")) + list(cwd.glob("*.jou"))
    for file in log_files:
        try:
            os.remove(file)
            print(f"已删除日志文件: {file}")
        except Exception as e:
            print(f"删除日志文件失败 {file}: {e}")

    print("构建文件清理完成")


def package_project(format, output):
    """打包项目"""
    # 实现打包逻辑
    pass


def main():
    """主函数"""
    cli()


if __name__ == '__main__':
    main()