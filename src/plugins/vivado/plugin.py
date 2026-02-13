#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Xilinx Vivado插件实现
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from core.plugin_base import (
    FPGAVendorPlugin,
    register_plugin,
    plugin_info,
    PluginType,
    BuildResult,
    VersionRange,
    ToolInfo,
    ToolDetector,
    VersionAdapter,
    VersionAdapterRegistry
)

# 导入本地模块
try:
    from .file_scanner import FileScanner
    from .tcl_templates import TCLScriptGenerator
    from .packbin_templates import PackBinTemplate, MCSGenerationTemplate
except ImportError:
    # 用于测试或开发环境
    from file_scanner import FileScanner
    from tcl_templates import TCLScriptGenerator
    # 注意：packbin_templates可能不存在于测试环境
    PackBinTemplate = None
    MCSGenerationTemplate = None


@plugin_info(name="vivado", plugin_type=PluginType.VENDOR, version="1.0.0")
@register_plugin
class VivadoPlugin(FPGAVendorPlugin):
    """Xilinx Vivado插件"""

    def __init__(self):
        super().__init__()
        self._tool_info: Optional[ToolInfo] = None
        self._adapter: Optional[VersionAdapter] = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "vivado"

    @property
    def plugin_type(self):
        return PluginType.VENDOR

    @property
    def vendor(self) -> str:
        return "xilinx"

    @property
    def description(self) -> str:
        return "Xilinx Vivado设计套件插件"

    @property
    def author(self) -> str:
        return "FPGABuilder Team"

    @property
    def supported_families(self) -> List[str]:
        return [
            "zynq-7000", "zynq-ultrascale+", "versal",
            "artix-7", "kintex-7", "virtex-7",
            "spartan-7", "artix-ultrascale", "kintex-ultrascale",
            "virtex-ultrascale"
        ]

    @property
    def supported_parts(self) -> List[str]:
        # 这里可以动态生成或从文件加载
        return [
            "xc7z045ffg676-2",
            "xc7z020clg400-1",
            "xc7a35tftg256-1",
            "xc7k325tffg900-2"
        ]

    @property
    def supported_tool_versions(self) -> Dict[str, VersionRange]:
        """支持的Vivado版本范围"""
        return {
            "vivado": VersionRange(
                min_version="2018.0",
                max_version="2024.2",
                recommended_version="2023.2"
            )
        }

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """初始化插件，检测Vivado安装和版本"""
        if self._initialized and config is None:
            return True

        # 如果有配置，使用配置驱动的检测
        if config:
            self._tool_info = ToolDetector.detect_vivado_with_config(config)
        else:
            # 否则使用自动检测
            self._tool_info = ToolDetector.detect_vivado()

        if not self._tool_info or not self._tool_info.installed:
            print("[WARN]  Vivado未检测到，插件功能受限")
            self._tool_info = ToolInfo(
                name="vivado",
                version="unknown",
                path=Path(""),
                installed=False
            )
            self._initialized = True
            return False

        print(f"[OK] 检测到Vivado: {self._tool_info.version} ({self._tool_info.path})")

        # 检查版本兼容性
        version_range = self.supported_tool_versions.get("vivado")
        if version_range and not self._tool_info.is_compatible():
            print(f"[WARN]  Vivado版本 {self._tool_info.version} 不在支持范围内")
            print(f"   支持范围: {version_range}")
            # 继续运行，但可能某些功能不可用

        # 获取版本适配器
        self._adapter = VersionAdapterRegistry.get_adapter(self._tool_info)
        if self._adapter:
            print(f"[OK] 使用版本适配器: {self._adapter.__class__.__name__}")

        self._initialized = True
        return True

    def detect_tool(self, tool_name: str) -> Optional[ToolInfo]:
        """检测Vivado工具"""
        if tool_name == "vivado":
            return ToolDetector.detect_vivado()
        elif tool_name == "vitis_hls":
            return ToolDetector.detect_vitis_hls()
        return None


    def _run_vivado_tcl(self, tcl_script: str, script_name: str = "build.tcl") -> BuildResult:
        """运行Vivado TCL脚本"""
        import subprocess
        import tempfile
        import os
        from pathlib import Path

        if not self._tool_info or not self._tool_info.installed:
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法运行TCL脚本"]
            )

        # 创建临时TCL文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tcl', delete=False, encoding='utf-8') as f:
            f.write(tcl_script)
            tcl_file = f.name

        try:
            # 处理Vivado可执行文件路径
            vivado_path = self._tool_info.path
            # 如果路径是目录，则追加可执行文件名
            if vivado_path.is_dir():
                vivado_path = vivado_path / 'vivado'
                if os.name == 'nt':  # Windows
                    vivado_path = vivado_path.with_suffix('.bat')
            # 如果路径是文件但扩展名不对，尝试修正
            elif vivado_path.is_file():
                # 已经是文件，直接使用
                pass
            else:
                # 路径不存在，尝试猜测
                if os.name == 'nt':
                    vivado_path = vivado_path / 'vivado.bat'
                else:
                    vivado_path = vivado_path / 'vivado'

            cmd = [str(vivado_path), '-mode', 'batch', '-source', tcl_file]
            print(f"执行Vivado命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 收集输出
            logs = {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': str(result.returncode)
            }

            success = result.returncode == 0
            artifacts = {'tcl_script': tcl_file}

            if success:
                print("Vivado TCL脚本执行成功")
            else:
                print(f"Vivado TCL脚本执行失败，返回码: {result.returncode}")
                if result.stderr:
                    print(f"错误输出: {result.stderr[:500]}")

            return BuildResult(
                success=success,
                artifacts=artifacts,
                logs=logs,
                metrics={'execution_time': 0.0},
                warnings=[] if success else ["TCL脚本执行失败"],
                errors=[] if success else [f"Vivado返回非零退出码: {result.returncode}"]
            )

        except Exception as e:
            return BuildResult(
                success=False,
                artifacts={},
                logs={'exception': str(e)},
                metrics={},
                errors=[f"执行Vivado TCL脚本时发生异常: {e}"]
            )
        finally:
            # 清理临时文件
            try:
                os.unlink(tcl_file)
            except:
                pass

    def synthesize(self, config: Dict[str, Any]) -> BuildResult:
        """综合"""
        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法运行综合"]
            )

        print("运行Vivado综合...")

        # 生成TCL脚本
        tcl_script = self.generate_tcl_script(config)

        # 修改脚本，只运行综合（不运行实现和比特流生成）
        # 简单的处理：移除实现和比特流生成部分
        lines = tcl_script.split('\n')
        synth_lines = []
        for line in lines:
            if 'impl_1' in line or 'write_bitstream' in line:
                continue
            synth_lines.append(line)

        # 添加只运行综合的命令
        synth_tcl = '\n'.join(synth_lines)

        # 执行TCL脚本
        result = self._run_vivado_tcl(synth_tcl, "synthesize.tcl")

        # 如果成功，添加综合特定的工件
        if result.success:
            result.artifacts['synthesis_report'] = '综合报告生成'
            print("Vivado综合完成")
        else:
            print("Vivado综合失败")

        return result

    def implement(self, config: Dict[str, Any]) -> BuildResult:
        """实现（布局布线）"""
        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法运行实现"]
            )

        print("运行Vivado实现...")

        return BuildResult(
            success=True,
            artifacts={"implementation": "completed"},
            logs={"implementation": "实现完成"},
            metrics={}
        )

    def generate_bitstream(self, config: Dict[str, Any]) -> BuildResult:
        """生成比特流"""
        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法生成比特流"]
            )

        print("生成比特流...")

        return BuildResult(
            success=True,
            artifacts={"bitstream": "generated"},
            logs={"bitstream": "比特流生成完成"},
            metrics={}
        )


    def generate_tcl_script(self, config: Dict[str, Any]) -> str:
        """生成TCL脚本（向后兼容方法）"""
        # 使用新的模板系统生成脚本
        generator = TCLScriptGenerator(config)

        # 扫描文件（简化版本）
        scanner = FileScanner()
        scanned_files = scanner.scan_files(config)

        # 生成完整构建脚本
        tcl_script = generator.generate_full_build_script(scanned_files)

        return tcl_script

    def get_compatibility_report(self) -> str:
        """获取兼容性报告"""
        report = super().get_compatibility_report()

        # 添加Vivado特定信息
        if self._tool_info:
            report += f"\n\nVivado路径: {self._tool_info.path}"
            if self._adapter:
                report += f"\n使用的适配器: {self._adapter.__class__.__name__}"

        return report

    def scan_and_import_files(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """扫描并导入源文件"""
        print("扫描源文件...")

        # 创建文件扫描器
        scanner = FileScanner()
        scanned_files = scanner.scan_files(config)

        # 生成Vivado命令
        file_commands = scanner.generate_vivado_file_commands(scanned_files)

        # 分析依赖关系
        hdl_files = scanned_files.get('hdl', [])
        if hdl_files:
            sorted_files = scanner.analyze_dependencies(hdl_files)
            print(f"找到 {len(sorted_files)} 个HDL文件，已按依赖关系排序")

        print(f"扫描完成: {len(hdl_files)} HDL文件, {len(scanned_files.get('constraints', []))} 约束文件")

        return {
            'scanned_files': scanned_files,
            'file_commands': file_commands,
            'sorted_hdl_files': sorted_files if hdl_files else []
        }

    def restore_bd_from_tcl(self, tcl_script_path: str, config: Dict[str, Any]) -> BuildResult:
        """从TCL脚本恢复Block Design"""
        print(f"从TCL脚本恢复Block Design: {tcl_script_path}")

        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法恢复BD"]
            )

        # 生成TCL脚本
        bd_config = config.get('source', {}).get('block_design', {})
        if not bd_config:
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["配置中未找到Block Design配置"]
            )

        # 使用模板生成BD恢复脚本
        from .tcl_templates import BDRecoveryTemplate
        bd_template = BDRecoveryTemplate(config, bd_config)
        bd_tcl = bd_template.render()

        # 执行TCL脚本
        result = self._run_vivado_tcl(bd_tcl, "bd_restore.tcl")

        if result.success:
            result.artifacts['bd_restored'] = 'Block Design恢复完成'
            print("Block Design恢复成功")
        else:
            print("Block Design恢复失败")

        return result

    def generate_bd_wrapper(self, config: Dict[str, Any], wrapper_name: str = None) -> BuildResult:
        """生成Block Design包装文件"""
        print("生成Block Design包装器...")

        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法生成包装器"]
            )

        bd_config = config.get('source', {}).get('block_design', {})
        if not bd_config:
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["配置中未找到Block Design配置"]
            )

        # 使用模板生成包装器生成脚本
        from .tcl_templates import BDRecoveryTemplate

        # 如果指定了包装器名称，更新配置
        if wrapper_name:
            bd_config = bd_config.copy()
            bd_config['wrapper_name'] = wrapper_name

        bd_template = BDRecoveryTemplate(config, bd_config)
        wrapper_tcl = bd_template.render()

        # 执行TCL脚本
        result = self._run_vivado_tcl(wrapper_tcl, "generate_wrapper.tcl")

        if result.success:
            result.artifacts['wrapper_generated'] = '包装器生成完成'
            print("Block Design包装器生成成功")
        else:
            print("Block Design包装器生成失败")

        return result

    def prepare_and_open_gui(self, config: Dict[str, Any]) -> BuildResult:
        """准备工程并打开GUI（创建工程、导入文件、恢复BD，但不运行综合）"""
        print("准备Vivado工程并打开GUI...")

        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法准备工程"]
            )

        # 扫描文件
        scan_result = self.scan_and_import_files(config)

        # 生成工程准备脚本（不含GUI命令）
        from .tcl_templates import TCLScriptGenerator
        generator = TCLScriptGenerator(config)
        tcl_script = generator.generate_preparation_script_without_gui(scan_result['scanned_files'])

        # 执行TCL脚本（批处理模式创建工程）
        result = self._run_vivado_tcl(tcl_script, "prepare_gui.tcl")

        if result.success:
            # 工程创建成功，打开GUI
            print("工程准备完成，正在打开Vivado GUI...")
            gui_result = self.open_gui(config)

            if gui_result.success:
                result.artifacts.update({
                    'project_prepared': '工程准备完成',
                    'scanned_files_count': f"{len(scan_result.get('sorted_hdl_files', []))} HDL文件",
                    'gui_opened': 'GUI已启动',
                    'gui_process_id': gui_result.artifacts.get('gui_process_id', 'unknown')
                })
                result.logs.update(gui_result.logs)
                print("Vivado工程准备完成，GUI已打开")
            else:
                result.success = False
                result.errors.extend(gui_result.errors)
                result.warnings.extend(gui_result.warnings)
                print("工程准备完成，但打开GUI失败")
        else:
            print("Vivado工程准备失败")

        return result

    def open_gui(self, config: Dict[str, Any]) -> BuildResult:
        """打开Vivado GUI界面"""
        print("打开Vivado GUI...")

        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法打开GUI"]
            )

        # 生成GUI打开脚本
        from .tcl_templates import GUITemplate
        gui_template = GUITemplate(config)
        gui_tcl = gui_template.render()

        # 创建临时TCL文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tcl', delete=False, encoding='utf-8') as f:
            f.write(gui_tcl)
            tcl_file = f.name

        try:
            # 构建GUI模式命令
            vivado_path = self._tool_info.path
            if vivado_path.is_dir():
                vivado_path = vivado_path / 'vivado'
                if os.name == 'nt':
                    vivado_path = vivado_path.with_suffix('.bat')

            cmd = [str(vivado_path), '-mode', 'gui', '-source', tcl_file]
            print(f"打开Vivado GUI: {' '.join(cmd)}")

            # 启动Vivado GUI（不等待完成）
            process = subprocess.Popen(cmd)

            return BuildResult(
                success=True,
                artifacts={'gui_process_id': str(process.pid), 'tcl_script': tcl_file},
                logs={'command': ' '.join(cmd)},
                metrics={}
            )
        except Exception as e:
            return BuildResult(
                success=False,
                artifacts={},
                logs={'exception': str(e)},
                metrics={},
                errors=[f"打开Vivado GUI失败: {e}"]
            )

    def prepare_project_only(self, config: Dict[str, Any]) -> BuildResult:
        """仅准备工程（创建工程、导入文件、恢复BD，但不打开GUI）"""
        print("准备Vivado工程（仅创建工程，不打开GUI）...")

        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法准备工程"]
            )

        # 扫描文件
        scan_result = self.scan_and_import_files(config)

        # 生成工程准备脚本（不含GUI命令）
        from .tcl_templates import TCLScriptGenerator
        generator = TCLScriptGenerator(config)
        tcl_script = generator.generate_preparation_script_without_gui(scan_result['scanned_files'])

        # 执行TCL脚本（批处理模式创建工程）
        result = self._run_vivado_tcl(tcl_script, "prepare_project.tcl")

        if result.success:
            result.artifacts.update({
                'project_prepared': '工程准备完成（未打开GUI）',
                'scanned_files_count': f"{len(scan_result.get('sorted_hdl_files', []))} HDL文件",
                'project_location': f"{config.get('project_dir', './build')}/{config.get('project', {}).get('name', 'fpga_project')}",
                'project_file': f"{config.get('project_dir', './build')}/{config.get('project', {}).get('name', 'fpga_project')}/{config.get('project', {}).get('name', 'fpga_project')}.xpr"
            })
            print("Vivado工程准备完成（未打开GUI）")
        else:
            print("Vivado工程准备失败")

        return result

    def clean_project(self, config: Dict[str, Any], clean_level: str = 'soft') -> BuildResult:
        """清理构建文件"""
        print(f"清理项目，级别: {clean_level}")

        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法清理项目"]
            )

        # 生成清理脚本
        from .tcl_templates import CleanTemplate
        clean_template = CleanTemplate(config, clean_level)
        clean_tcl = clean_template.render()

        # 执行清理脚本
        result = self._run_vivado_tcl(clean_tcl, f"clean_{clean_level}.tcl")

        if result.success:
            result.artifacts['cleaned'] = f'项目清理完成（级别: {clean_level}）'
            print(f"项目清理完成（级别: {clean_level}）")
        else:
            print(f"项目清理失败（级别: {clean_level}）")

        return result

    def create_project(self, config: Dict[str, Any]) -> BuildResult:
        """创建Vivado工程"""
        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法创建工程"]
            )

        # 适配配置（如果需要）
        adapted_config = config
        if self._adapter:
            adapted_config = self._adapter.adapt_config(config)

        print(f"创建Vivado工程: {config.get('project', {}).get('name', '未命名')}")

        # 扫描文件
        scan_result = self.scan_and_import_files(adapted_config)

        # 生成完整构建脚本
        generator = TCLScriptGenerator(adapted_config)
        tcl_script = generator.generate_full_build_script(scan_result['scanned_files'])

        # 执行TCL脚本
        result = self._run_vivado_tcl(tcl_script, "create_project.tcl")

        # 如果成功，添加额外的工件信息
        if result.success:
            result.artifacts.update({
                'project_created': '工程创建完成',
                'scanned_files_count': f"{len(scan_result.get('sorted_hdl_files', []))} HDL文件"
            })
            print("Vivado工程创建成功")
        else:
            print("Vivado工程创建失败")

        return result

    def synthesize(self, config: Dict[str, Any]) -> BuildResult:
        """综合"""
        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法运行综合"]
            )

        print("运行Vivado综合...")

        # 扫描文件
        scan_result = self.scan_and_import_files(config)

        # 生成仅综合脚本
        generator = TCLScriptGenerator(config)
        tcl_script = generator.generate_synthesis_only_script(scan_result['scanned_files'])

        # 执行TCL脚本
        result = self._run_vivado_tcl(tcl_script, "synthesize.tcl")

        # 如果成功，添加综合特定的工件
        if result.success:
            result.artifacts['synthesis_report'] = '综合报告生成'
            print("Vivado综合完成")
        else:
            print("Vivado综合失败")

        return result

    def implement(self, config: Dict[str, Any]) -> BuildResult:
        """实现（布局布线）"""
        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法运行实现"]
            )

        print("运行Vivado实现...")

        # 生成构建流程脚本（仅实现部分）
        from .tcl_templates import BuildFlowTemplate
        build_template = BuildFlowTemplate(config)
        build_tcl = build_template.render()

        # 修改脚本，只保留实现部分（简化处理）
        lines = build_tcl.split('\n')
        impl_lines = []
        in_impl_section = False

        for line in lines:
            if '运行实现' in line or 'pre_impl' in line:
                in_impl_section = True
            elif '生成比特流' in line or 'post_bitstream' in line:
                in_impl_section = False

            if in_impl_section or not line.strip() or line.strip().startswith('#'):
                impl_lines.append(line)

        impl_tcl = '\n'.join(impl_lines)

        # 添加打开工程命令
        project_name = config.get('project', {}).get('name', 'fpga_project')
        project_dir = config.get('project_dir', './build')
        # 使用正斜杠构建路径，避免转义问题，添加.xpr扩展名
        project_path = f'{project_dir}/{project_name}.xpr'.replace('\\', '/')
        open_cmd = f'open_project "{project_path}"'
        impl_tcl = f'{open_cmd}\n{impl_tcl}'

        # 执行TCL脚本
        result = self._run_vivado_tcl(impl_tcl, "implement.tcl")

        if result.success:
            result.artifacts['implementation'] = '实现完成'
            print("Vivado实现完成")
        else:
            print("Vivado实现失败")

        return result

    def generate_bitstream(self, config: Dict[str, Any]) -> BuildResult:
        """生成比特流"""
        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法生成比特流"]
            )

        print("生成比特流...")

        # 生成构建流程脚本（仅比特流部分）
        from .tcl_templates import BuildFlowTemplate
        build_template = BuildFlowTemplate(config)
        build_tcl = build_template.render()

        # 修改脚本，只保留比特流部分（简化处理）
        lines = build_tcl.split('\n')
        bitstream_lines = []
        in_bitstream_section = False

        for line in lines:
            if '生成比特流' in line or 'post_impl' in line:
                in_bitstream_section = True
            elif '构建流程完成' in line:
                in_bitstream_section = False

            if in_bitstream_section or not line.strip() or line.strip().startswith('#'):
                bitstream_lines.append(line)

        bitstream_tcl = '\n'.join(bitstream_lines)

        # 添加打开工程命令
        project_name = config.get('project', {}).get('name', 'fpga_project')
        project_dir = config.get('project_dir', './build')
        # 使用正斜杠构建路径，避免转义问题，添加.xpr扩展名
        project_path = f'{project_dir}/{project_name}.xpr'.replace('\\', '/')
        open_cmd = f'open_project "{project_path}"'
        bitstream_tcl = f'{open_cmd}\n{bitstream_tcl}'

        # 执行TCL脚本
        result = self._run_vivado_tcl(bitstream_tcl, "generate_bitstream.tcl")

        if result.success:
            result.artifacts['bitstream'] = '比特流生成完成'
            print("比特流生成完成")
        else:
            print("比特流生成失败")

        return result

    def packbin(self, config: Dict[str, Any]) -> BuildResult:
        """生成二进制合并文件（boot.bin）"""
        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法生成二进制合并文件"]
            )

        print("生成二进制合并文件...")

        # 检查PackBinTemplate是否可用
        if PackBinTemplate is None:
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["PackBinTemplate不可用，二进制合并功能无法使用"]
            )

        # 从配置中获取二进制文件设置
        bin_config = config.get('build', {}).get('bin_merge', {})
        if not bin_config:
            # 尝试从hooks中获取
            hooks = config.get('build', {}).get('hooks', {})
            bin_merge_script = hooks.get('bin_merge_script')
            if bin_merge_script:
                # 如果有脚本，直接执行
                return self._run_vivado_tcl(
                    f'source {{{bin_merge_script}}}',
                    "bin_merge.tcl"
                )
            else:
                return BuildResult(
                    success=False,
                    artifacts={},
                    logs={},
                    metrics={},
                    errors=["配置中未找到二进制合并设置"]
                )

        # 生成TCL脚本
        try:
            bin_template = PackBinTemplate(config, bin_config)
            bin_tcl = bin_template.render()
        except Exception as e:
            return BuildResult(
                success=False,
                artifacts={},
                logs={'exception': str(e)},
                metrics={},
                errors=[f"生成二进制合并脚本失败: {e}"]
            )

        # 执行TCL脚本
        result = self._run_vivado_tcl(bin_tcl, "packbin.tcl")

        if result.success:
            result.artifacts['bin_file'] = '二进制合并文件生成完成'
            print("二进制合并文件生成完成")
        else:
            print("二进制合并文件生成失败")

        return result

    def generate_mcs_file(self, config: Dict[str, Any], flash_config: Optional[Dict[str, Any]] = None) -> BuildResult:
        """生成MCS文件（用于Flash编程）"""
        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法生成MCS文件"]
            )

        print("生成MCS文件...")

        # 检查MCSGenerationTemplate是否可用
        if MCSGenerationTemplate is None:
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["MCSGenerationTemplate不可用，Flash编程功能无法使用"]
            )

        # 获取Flash配置
        if not flash_config:
            flash_config = config.get('build', {}).get('flash', {})

        # 生成TCL脚本
        try:
            mcs_template = MCSGenerationTemplate(config, flash_config)
            mcs_tcl = mcs_template.render()
        except Exception as e:
            return BuildResult(
                success=False,
                artifacts={},
                logs={'exception': str(e)},
                metrics={},
                errors=[f"生成MCS脚本失败: {e}"]
            )

        # 执行TCL脚本
        result = self._run_vivado_tcl(mcs_tcl, "generate_mcs.tcl")

        if result.success:
            result.artifacts['mcs_file'] = 'MCS文件生成完成'
            print("MCS文件生成完成")
        else:
            print("MCS文件生成失败")

        return result

    def program_device(self, config: Dict[str, Any], flash_mode: bool = False) -> BuildResult:
        """烧录设备（支持Flash模式）"""
        if not self.initialize(config):
            return BuildResult(
                success=False,
                artifacts={},
                logs={},
                metrics={},
                errors=["Vivado未检测到，无法烧录设备"]
            )

        if flash_mode:
            print("烧录设备到Flash...")
            # 首先生成MCS文件
            mcs_result = self.generate_mcs_file(config)
            if not mcs_result.success:
                return mcs_result

            # 然后执行Flash烧录
            # TODO: 实现实际的Flash烧录逻辑
            return BuildResult(
                success=True,
                artifacts={'flash_programmed': 'Flash烧录完成'},
                logs={'flash': '设备已烧录到Flash'},
                metrics={}
            )
        else:
            print("烧录设备到FPGA...")
            # 原有的JTAG烧录逻辑
            # TODO: 实现JTAG烧录
            return BuildResult(
                success=True,
                artifacts={'jtag_programmed': 'JTAG烧录完成'},
                logs={'jtag': '设备已通过JTAG烧录'},
                metrics={}
            )


# Vivado版本适配器
class Vivado2023Adapter(VersionAdapter):
    """Vivado 2023.x适配器"""

    def adapt_command(self, command: List[str]) -> List[str]:
        """适配命令参数"""
        # Vivado 2023.x没有特别的命令变化
        return command

    def adapt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """适配配置"""
        adapted_config = config.copy()

        # Vivado 2023.x特定的配置适配
        build_config = adapted_config.get('build', {})
        synthesis_config = build_config.get('synthesis', {})

        # 设置2023.x推荐的综合策略
        if 'strategy' not in synthesis_config:
            synthesis_config['strategy'] = 'Vivado Synthesis 2023'

        return adapted_config

    def adapt_output(self, output: str) -> str:
        """适配输出解析"""
        # 处理Vivado 2023.x的输出格式
        return output


class Vivado2019Adapter(VersionAdapter):
    """Vivado 2019.x适配器"""

    def adapt_command(self, command: List[str]) -> List[str]:
        """适配命令参数"""
        # Vivado 2019.x命令参数
        adapted_command = command.copy()
        if "vivado" in command[0]:
            # 确保使用批处理模式
            if "-mode" not in command:
                adapted_command.append("-mode")
                adapted_command.append("batch")
        return adapted_command

    def adapt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """适配配置"""
        adapted_config = config.copy()

        # Vivado 2019.x特定的配置适配
        build_config = adapted_config.get('build', {})
        synthesis_config = build_config.get('synthesis', {})

        # 设置2019.x推荐的综合策略
        if 'strategy' not in synthesis_config:
            synthesis_config['strategy'] = 'Vivado Synthesis 2019'

        return adapted_config

    def adapt_output(self, output: str) -> str:
        """适配输出解析"""
        # Vivado 2019.x的输出格式处理
        return output


class Vivado2024Adapter(VersionAdapter):
    """Vivado 2024.x适配器"""

    def adapt_command(self, command: List[str]) -> List[str]:
        """适配命令参数"""
        # Vivado 2024.x可能需要不同的参数
        adapted_command = command.copy()
        if "vivado" in command[0]:
            # 添加新版本的标志
            adapted_command.append("-mode")
            adapted_command.append("batch")
        return adapted_command

    def adapt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """适配配置"""
        adapted_config = config.copy()

        # Vivado 2024.x特定的配置适配
        build_config = adapted_config.get('build', {})
        synthesis_config = build_config.get('synthesis', {})

        # 设置2024.x推荐的综合策略
        if 'strategy' not in synthesis_config:
            synthesis_config['strategy'] = 'Vivado Synthesis 2024'

        # 添加新版本特有的选项
        synthesis_config['advanced'] = {
            'enable_dsp_utilization': True,
            'use_dsp48e2': True
        }

        return adapted_config

    def adapt_output(self, output: str) -> str:
        """适配输出解析"""
        # 处理Vivado 2024.x的输出格式
        # 可能输出格式有变化
        return output.replace("INFO:", "[INFO]").replace("WARNING:", "[WARNING]")


# 注册版本适配器
VersionAdapterRegistry.register("vivado", r"2019\..*", Vivado2019Adapter)
VersionAdapterRegistry.register("vivado", r"2023\..*", Vivado2023Adapter)
VersionAdapterRegistry.register("vivado", r"2024\..*", Vivado2024Adapter)