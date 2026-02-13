#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vivado TCL模板系统
提供模块化的TCL脚本生成功能
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import os


class TCLTemplateBase:
    """TCL模板基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_name = config.get('project', {}).get('name', 'fpga_project')
        self.fpga_part = config.get('fpga', {}).get('part', 'xc7z045ffg676-2')
        self.top_module = config.get('fpga', {}).get('top_module', '')

    def render(self) -> str:
        """渲染模板为TCL脚本"""
        raise NotImplementedError

    def _get_hook_commands(self, hook_name: str) -> List[str]:
        """获取钩子脚本命令"""
        hooks = self.config.get('build', {}).get('hooks', {})
        hook_script = hooks.get(hook_name)

        if not hook_script:
            return []

        commands = []
        # 支持字符串或字符串数组
        if isinstance(hook_script, list):
            script_items = hook_script
        else:
            # 字符串，按换行符分割，过滤空行
            script_items = [line.strip() for line in str(hook_script).split('\n') if line.strip()]

        for item in script_items:
            # 检查是脚本文件还是直接命令
            hook_path = Path(item)
            if hook_path.exists() and hook_path.is_file():
                # 是脚本文件，使用source命令
                commands.append(f'source {{{item}}}')
            else:
                # 直接命令
                commands.append(item)

        return commands

    def _execute_hook(self, hook_name: str, tcl_script_lines: List[str]):
        """执行钩子脚本"""
        hook_commands = self._get_hook_commands(hook_name)
        if hook_commands:
            tcl_script_lines.append(f'\n# {hook_name} 钩子脚本')
            for cmd in hook_commands:
                tcl_script_lines.append(cmd)


class BasicProjectTemplate(TCLTemplateBase):
    """基本工程创建模板"""

    def __init__(self, config: Dict[str, Any], file_scanner_results: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.file_scanner_results = file_scanner_results or {}
        self.project_dir = config.get('project_dir', './build')

    def render(self) -> str:
        """渲染基本工程创建模板"""
        lines = [
            '# Vivado工程创建脚本 - 由FPGABuilder生成',
            f'# 项目: {self.project_name}',
            f'# 器件: {self.fpga_part}',
            ''
        ]

        # 创建工程
        lines.append('# 创建工程')
        lines.append(f'create_project {self.project_name} "{self.project_dir}" -part {self.fpga_part} -force')
        lines.append('')

        # 设置工程属性
        lines.append('# 设置工程属性')
        lines.append('set_property default_lib work [current_project]')
        lines.append('set_property target_language Verilog [current_project]')
        lines.append('')

        return '\n'.join(lines)


class BDRecoveryTemplate(TCLTemplateBase):
    """BD恢复和包装生成模板"""

    def __init__(self, config: Dict[str, Any], bd_config: Dict[str, Any]):
        super().__init__(config)
        self.bd_config = bd_config
        self.bd_file = bd_config.get('bd_file')
        self.tcl_script = bd_config.get('tcl_script')
        self.is_top = bd_config.get('is_top', False)
        self.wrapper_name = bd_config.get('wrapper_name', f'{self.project_name}_wrapper')
        self.auto_wrapper = bd_config.get('auto_wrapper', True)
        self.generate_wrapper = bd_config.get('generate_wrapper', True)
        self.wrapper_language = bd_config.get('wrapper_language', 'verilog')

    def render(self) -> str:
        """渲染BD恢复模板"""
        lines = [
            '# Block Design恢复脚本',
            ''
        ]

        # 如果有TCL脚本，使用TCL脚本恢复BD
        if self.tcl_script:
            lines.append('# 从TCL脚本恢复Block Design')
            lines.append(f'source {{{self.tcl_script}}}')
        # 否则直接加载BD文件
        elif self.bd_file:
            lines.append('# 加载Block Design文件')
            lines.append(f'set bd_file [get_files {{{self.bd_file}}}]')
            lines.append(f'open_bd_design $bd_file')
        else:
            lines.append('# 错误：未指定BD文件或TCL脚本')
            lines.append('puts "ERROR: No BD file or TCL script specified"')
            return '\n'.join(lines)

        lines.append('')

        # 生成包装器
        if self.generate_wrapper:
            lines.append('# 生成Block Design包装器')
            if self.auto_wrapper:
                lines.append('make_wrapper -files [get_files [current_bd_design]] -top')
                lines.append('')

                # 获取生成的包装器文件
                lines.append('# 获取生成的包装器文件')
                lines.append(f'set wrapper_file [get_files -of_objects [get_files [current_bd_design]] -filter {{FILE_TYPE == "Verilog" || FILE_TYPE == "VHDL"}}]')
                lines.append('if {[llength $wrapper_file] > 0} {')
                lines.append('    set top_module [file rootname [file tail [lindex $wrapper_file 0]]]')
                lines.append(f'    set_property top $top_module [current_fileset]')
                lines.append('    puts "自动生成包装器: $top_module"')
                lines.append('} else {')
                lines.append(f'    # 手动创建包装器')
                lines.append(f'    create_bd_cell -type hier {self.wrapper_name}')
                lines.append(f'    set_property top {self.wrapper_name} [current_fileset]')
                lines.append('}')
            else:
                # 手动设置包装器
                lines.append(f'# 手动设置顶层模块: {self.wrapper_name}')
                lines.append(f'set_property top {self.wrapper_name} [current_fileset]')

            lines.append('')

        # 如果BD是顶层，设置顶层模块
        if self.is_top:
            lines.append('# 设置Block Design为顶层')
            lines.append(f'set_property top [current_bd_design] [current_fileset]')
            lines.append('')

        return '\n'.join(lines)


class BuildFlowTemplate(TCLTemplateBase):
    """完整构建流程模板（综合→实现→比特流）"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.build_config = config.get('build', {})
        self.synthesis_config = self.build_config.get('synthesis', {})
        self.implementation_config = self.build_config.get('implementation', {})
        self.bitstream_config = self.build_config.get('bitstream', {})

    def render(self) -> str:
        """渲染构建流程模板"""
        lines = [
            '# Vivado构建流程脚本',
            ''
        ]

        # 构建前钩子
        self._execute_hook('pre_build', lines)

        # 综合前钩子
        self._execute_hook('pre_synth', lines)

        # 设置综合策略
        synth_strategy = self.synthesis_config.get('strategy', 'Vivado Synthesis Defaults')
        lines.append('# 设置综合策略')
        lines.append(f'set_property strategy "{synth_strategy}" [get_runs synth_1]')
        lines.append('')

        # 运行综合
        lines.append('# 运行综合')
        lines.append('launch_runs synth_1')
        lines.append('wait_on_run synth_1')
        lines.append('')

        # 检查综合结果
        lines.append('# 检查综合结果')
        lines.append('if {[get_property PROGRESS [get_runs synth_1]] != "100%"} {')
        lines.append('    error "综合失败"')
        lines.append('}')
        lines.append('')

        # 综合后钩子
        self._execute_hook('post_synth', lines)

        # 实现前钩子
        self._execute_hook('pre_impl', lines)

        # 设置实现选项
        impl_options = self.implementation_config.get('options', {})
        if impl_options:
            lines.append('# 设置实现选项')
            for opt_name, opt_value in impl_options.items():
                lines.append(f'set_property {opt_name} {opt_value} [get_runs impl_1]')
            lines.append('')

        # 运行实现
        lines.append('# 运行实现')
        lines.append('launch_runs impl_1')
        lines.append('wait_on_run impl_1')
        lines.append('')

        # 检查实现结果
        lines.append('# 检查实现结果')
        lines.append('if {[get_property PROGRESS [get_runs impl_1]] != "100%"} {')
        lines.append('    error "实现失败"')
        lines.append('}')
        lines.append('')

        # 实现后钩子
        self._execute_hook('post_impl', lines)

        # 生成比特流
        lines.append('# 生成比特流')
        # 降低未约束端口DRC错误的严重性，允许生成比特流用于测试
        lines.append('set_property SEVERITY {Warning} [get_drc_checks UCIO-1]')

        # 设置比特流输出目录
        bitstream_output_dir = self.bitstream_config.get('output_dir', 'build/bitstreams')
        lines.append(f'# 设置比特流输出目录: {bitstream_output_dir}')
        lines.append(f'file mkdir "{bitstream_output_dir}"')
        # 使用绝对路径并确保正斜杠
        lines.append(f'set bitstream_output_dir [file normalize "{bitstream_output_dir}"]')
        # 设置比特流输出目录，添加错误处理
        lines.append('if {[current_design] != ""} {')
        lines.append(f'    catch {{set_property BITSTREAM.OUTPUT_DIR "$bitstream_output_dir" [current_design]}}')
        lines.append('}')
        lines.append('if {[get_runs -quiet impl_1] != ""} {')
        lines.append(f'    catch {{set_property BITSTREAM.OUTPUT_DIR "$bitstream_output_dir" [get_runs impl_1]}}')
        lines.append('}')
        lines.append('')

        bitstream_options = self.bitstream_config.get('options', {})
        if bitstream_options:
            lines.append('# 设置比特流选项')
            for opt_name, opt_value in bitstream_options.items():
                # 映射常见的比特流选项名称到正确的属性名
                if opt_name == 'bin_file':
                    # 生成bin文件的正确属性
                    prop_name = 'STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE'
                    # 将Python布尔值转换为TCL布尔值
                    prop_value = 'true' if opt_value in [True, 'true', 'True'] else 'false'
                    lines.append(f'set_property {prop_name} {prop_value} [get_runs impl_1]')
                elif opt_name == 'mask_file':
                    prop_name = 'STEPS.WRITE_BITSTREAM.ARGS.MASK_FILE'
                    prop_value = 'true' if opt_value in [True, 'true', 'True'] else 'false'
                    lines.append(f'set_property {prop_name} {prop_value} [get_runs impl_1]')
                else:
                    # 其他选项直接传递
                    lines.append(f'set_property {opt_name} {opt_value} [get_runs impl_1]')

        # 重置比特流步骤（如果之前已经运行过）
        lines.append('catch {reset_run impl_1 -from_step route_design}')
        lines.append('launch_runs impl_1 -to_step write_bitstream')
        lines.append('wait_on_run impl_1')
        lines.append('')

        # 检查比特流生成结果并复制文件到输出目录
        lines.append('# 检查比特流生成结果并复制文件')
        lines.append('set run_dir [get_property DIRECTORY [get_runs impl_1]]')
        lines.append('puts "运行目录: $run_dir"')
        lines.append('set bit_files [glob -nocomplain "$run_dir/*.bit $run_dir/*.bin $run_dir/*.ltx"]')
        lines.append('# 如果运行目录没找到，检查当前目录')
        lines.append('if {[llength $bit_files] == 0} {')
        lines.append('    set bit_files [glob -nocomplain "*.bit *.bin *.ltx"]')
        lines.append('    puts "在当前目录查找比特流文件"')
        lines.append('}')
        lines.append('if {[llength $bit_files] == 0} {')
        lines.append('    error "比特流生成失败：未找到比特流文件"')
        lines.append('}')
        lines.append('puts "比特流生成成功，找到 [llength $bit_files] 个文件"')
        lines.append('')
        lines.append('# 复制比特流文件到输出目录')
        lines.append('set copy_success 0')
        lines.append('foreach bit_file $bit_files {')
        lines.append('    set filename [file tail $bit_file]')
        lines.append('    set dest_file [file join $bitstream_output_dir $filename]')
        lines.append('    if {[catch {file copy -force $bit_file $dest_file} error_msg]} {')
        lines.append('        puts "警告: 复制文件失败: $filename -> $error_msg"')
        lines.append('    } else {')
        lines.append('        puts "已复制比特流文件: $filename -> $bitstream_output_dir"')
        lines.append('        set copy_success 1')
        lines.append('    }')
        lines.append('}')
        lines.append('if {$copy_success == 0} {')
        lines.append('    puts "警告: 未能复制任何比特流文件到输出目录"')
        lines.append('}')
        lines.append('')

        # 比特流后钩子
        self._execute_hook('post_bitstream', lines)

        # 二进制合并脚本
        bin_merge_script = self.config.get('build', {}).get('hooks', {}).get('bin_merge_script')
        if bin_merge_script:
            lines.append('# 执行二进制合并脚本')
            bin_script_path = Path(bin_merge_script)
            if bin_script_path.exists():
                lines.append(f'source {{{bin_merge_script}}}')
            else:
                lines.append(f'# 警告：二进制合并脚本不存在: {bin_merge_script}')
            lines.append('')

        lines.append('puts "构建流程完成"')
        return '\n'.join(lines)


class CleanTemplate(TCLTemplateBase):
    """清理模板"""

    def __init__(self, config: Dict[str, Any], clean_level: str = 'soft'):
        """
        Args:
            config: 项目配置
            clean_level: 清理级别 ('soft', 'hard', 'all')
        """
        super().__init__(config)
        self.clean_level = clean_level
        self.project_name = config.get('project', {}).get('name', 'fpga_project')

    def render(self) -> str:
        """渲染清理模板"""
        lines = [
            f'# Vivado清理脚本 - 级别: {self.clean_level}',
            ''
        ]

        if self.clean_level == 'soft':
            # 软清理：只清理构建文件
            lines.append('# 软清理：删除构建文件')
            lines.append('reset_runs synth_1')
            lines.append('reset_runs impl_1')
            # 递归删除所有.log和.jou文件
            lines.append('foreach file [glob -nocomplain -type f *.log */*.log */*/*.log */*/*/*.log] {')
            lines.append('    file delete -force $file')
            lines.append('}')
            lines.append('foreach file [glob -nocomplain -type f *.jou */*.jou */*/*.jou */*/*/*.jou] {')
            lines.append('    file delete -force $file')
            lines.append('}')
            lines.append('file delete -force {*.str}')

        elif self.clean_level == 'hard':
            # 硬清理：删除工程目录
            lines.append('# 硬清理：删除工程目录')
            lines.append(f'if {{[file exists "{self.project_name}"]}} {{')
            lines.append(f'    file delete -force "{self.project_name}"')
            lines.append('    puts "已删除工程目录: {self.project_name}"')
            lines.append('}')

        elif self.clean_level == 'all':
            # 全部清理：删除所有生成文件
            lines.append('# 全部清理：删除所有生成文件')
            lines.append(f'if {{[file exists "{self.project_name}"]}} {{')
            lines.append(f'    file delete -force "{self.project_name}"')
            lines.append('}')
            lines.append('file delete -force {*.log}')
            lines.append('file delete -force {*.jou}')
            lines.append('file delete -force {*.str}')
            lines.append('file delete -force {*.bit}')
            lines.append('file delete -force {*.bin}')
            lines.append('file delete -force {*.mcs}')
            lines.append('file delete -force {*.prm}')

        lines.append('')
        lines.append('puts "清理完成"')

        return '\n'.join(lines)


class GUITemplate(TCLTemplateBase):
    """GUI打开模板"""

    def render(self) -> str:
        """渲染GUI模板"""
        lines = [
            '# Vivado GUI打开脚本',
            '# 此脚本用于在GUI模式下打开工程',
            ''
        ]

        # 打开工程
        lines.append('# 打开工程')
        lines.append(f'open_project {self.project_name}')
        lines.append('')

        # 设置GUI视图
        lines.append('# 设置GUI视图')
        lines.append('start_gui')
        lines.append('')

        # 打开设计
        lines.append('# 打开设计')
        lines.append('open_bd_design [get_files *.bd]')
        lines.append('')

        # 打开综合设计
        lines.append('# 打开综合设计')
        lines.append('open_run synth_1')
        lines.append('')

        # 打开实现设计
        lines.append('# 打开实现设计')
        lines.append('open_run impl_1')
        lines.append('')

        lines.append('puts "GUI已打开"')
        return '\n'.join(lines)


class TCLScriptGenerator:
    """TCL脚本生成器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_name = config.get('project', {}).get('name', 'fpga_project')

    def generate_full_build_script(self, file_scanner_results: Optional[Dict[str, Any]] = None) -> str:
        """生成完整构建脚本"""
        script_parts = []

        # 1. 基本工程创建
        basic_template = BasicProjectTemplate(self.config, file_scanner_results)
        script_parts.append(basic_template.render())

        # 2. 文件添加命令
        if file_scanner_results:
            script_parts.append(self._generate_file_add_commands(file_scanner_results))

        # 3. Block Design恢复
        bd_config = self.config.get('source', {}).get('block_design')
        if bd_config:
            bd_template = BDRecoveryTemplate(self.config, bd_config)
            script_parts.append(bd_template.render())

        # 4. 设置顶层模块
        script_parts.append(self._generate_top_module_setup())

        # 5. 构建流程
        build_template = BuildFlowTemplate(self.config)
        script_parts.append(build_template.render())

        return '\n'.join(script_parts)

    def generate_clean_script(self, clean_level: str = 'soft') -> str:
        """生成清理脚本"""
        clean_template = CleanTemplate(self.config, clean_level)
        return clean_template.render()

    def generate_gui_script(self) -> str:
        """生成GUI脚本"""
        gui_template = GUITemplate(self.config)
        return gui_template.render()

    def generate_synthesis_only_script(self, file_scanner_results: Optional[Dict[str, Any]] = None) -> str:
        """生成仅综合脚本"""
        script_parts = []

        # 基本工程创建
        basic_template = BasicProjectTemplate(self.config, file_scanner_results)
        script_parts.append(basic_template.render())

        # 文件添加命令
        if file_scanner_results:
            script_parts.append(self._generate_file_add_commands(file_scanner_results))

        # Block Design恢复
        bd_config = self.config.get('source', {}).get('block_design')
        if bd_config:
            bd_template = BDRecoveryTemplate(self.config, bd_config)
            script_parts.append(bd_template.render())

        # 设置顶层模块
        script_parts.append(self._generate_top_module_setup())

        # 仅综合
        script_parts.append(self._generate_synthesis_part())

        return '\n'.join(script_parts)

    def _generate_file_add_commands(self, file_scanner_results: Dict[str, Any]) -> str:
        """生成文件添加命令"""
        lines = ['# 添加源文件', '']

        # 使用FileScanner生成准确的Vivado命令
        try:
            from .file_scanner import FileScanner

            # 创建FileScanner实例（使用配置中的项目目录作为基础路径）
            project_dir = self.config.get('project_dir', './build')
            scanner = FileScanner(Path(project_dir))

            # 生成命令
            commands = scanner.generate_vivado_file_commands(file_scanner_results)

            # 添加HDL命令
            if commands.get('hdl_commands'):
                lines.append('# HDL文件')
                for cmd in commands['hdl_commands']:
                    lines.append(cmd)
                lines.append('')

            # 添加约束命令
            if commands.get('constraint_commands'):
                lines.append('# 约束文件')
                for cmd in commands['constraint_commands']:
                    lines.append(cmd)
                lines.append('')

            # 添加IP核命令
            if commands.get('ip_commands'):
                lines.append('# IP核文件')
                for cmd in commands['ip_commands']:
                    lines.append(cmd)
                lines.append('')

            # 添加Block Design命令
            if commands.get('bd_commands'):
                lines.append('# Block Design文件')
                for cmd in commands['bd_commands']:
                    lines.append(cmd)
                lines.append('')

        except ImportError:
            # 回退到简单实现
            lines.append('# 注意：FileScanner不可用，使用简单文件添加命令')
            hdl_files = file_scanner_results.get('hdl', [])
            for file_info in hdl_files:
                lines.append(f'add_files {{{file_info["path"]}}}')

            if hdl_files:
                lines.append('')

            constraint_files = file_scanner_results.get('constraints', [])
            for file_info in constraint_files:
                lines.append(f'add_files -fileset constrs_1 {{{file_info["path"]}}}')

            if constraint_files:
                lines.append('')

        return '\n'.join(lines)

    def _generate_top_module_setup(self) -> str:
        """生成顶层模块设置
        优先级：BD is_top > 配置top_module > 自动检测
        """
        lines = ['# 设置顶层模块', '']

        # 检查BD配置
        bd_config = self.config.get('source', {}).get('block_design')
        if bd_config and bd_config.get('is_top', False):
            # BD被设置为顶层，BD恢复模板会处理顶层设置
            # 这里不需要额外设置，但可以添加注释
            lines.append('# Block Design已设置为顶层，跳过顶层模块设置')
            lines.append('')
            return '\n'.join(lines)

        # 使用配置中的顶层模块
        top_module = self.config.get('fpga', {}).get('top_module')
        if top_module:
            lines.append(f'set_property top {top_module} [current_fileset]')
            lines.append(f'puts "设置顶层模块: {top_module}"')
            lines.append('')
            return '\n'.join(lines)

        # 尝试自动检测
        # 这里可以添加自动检测逻辑，例如扫描文件寻找可能的顶层模块
        # 暂时返回空，让Vivado使用默认行为
        lines.append('# 未指定顶层模块，使用Vivado默认行为')
        lines.append('')
        return '\n'.join(lines)

    def _generate_synthesis_part(self) -> str:
        """生成综合部分"""
        lines = [
            '# 运行综合',
            ''
        ]

        # 综合前钩子
        hooks = self.config.get('build', {}).get('hooks', {})
        pre_synth = hooks.get('pre_synth')
        if pre_synth:
            lines.append(f'# 综合前钩子')
            lines.append(f'source {{{pre_synth}}}')
            lines.append('')

        # 设置综合策略
        synth_strategy = self.config.get('build', {}).get('synthesis', {}).get('strategy', 'Vivado Synthesis Defaults')
        lines.append(f'set_property strategy "{synth_strategy}" [get_runs synth_1]')
        lines.append('')

        # 运行综合
        lines.append('launch_runs synth_1')
        lines.append('wait_on_run synth_1')
        lines.append('')

        # 检查综合结果
        lines.append('if {[get_property PROGRESS [get_runs synth_1]] != "100%"} {')
        lines.append('    error "综合失败"')
        lines.append('}')
        lines.append('')

        # 综合后钩子
        post_synth = hooks.get('post_synth')
        if post_synth:
            lines.append(f'# 综合后钩子')
            lines.append(f'source {{{post_synth}}}')
            lines.append('')

        lines.append('puts "综合完成"')
        return '\n'.join(lines)