#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
插件基类定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union, Callable, Type
from dataclasses import dataclass, field
from pathlib import Path
import enum
import re
import subprocess
import sys
import logging

logger = logging.getLogger(__name__)


class PluginType(enum.Enum):
    """插件类型枚举"""
    VENDOR = "vendor"           # FPGA厂商插件
    IP_CORE = "ip_core"         # IP核插件
    HLS = "hls"                 # HLS插件
    DOCUMENTATION = "doc"       # 文档插件
    DEPLOYMENT = "deployment"   # 部署插件
    TOOL = "tool"               # 工具插件


@dataclass
class VersionRange:
    """版本范围"""
    min_version: str
    max_version: str
    recommended_version: Optional[str] = None

    def contains(self, version: str) -> bool:
        """检查版本是否在范围内"""
        # 简单版本比较，实际实现可能需要更复杂的版本解析
        return self.min_version <= version <= self.max_version

    def __str__(self) -> str:
        if self.recommended_version:
            return f"{self.min_version} - {self.max_version} (推荐: {self.recommended_version})"
        return f"{self.min_version} - {self.max_version}"


@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    version: str
    path: Path
    installed: bool = True
    version_range: Optional[VersionRange] = None

    def is_compatible(self) -> bool:
        """检查工具版本是否兼容"""
        if not self.installed:
            return False
        if self.version_range is None:
            return True
        return self.version_range.contains(self.version)


@dataclass
class BuildResult:
    """构建结果"""
    success: bool                       # 是否成功
    artifacts: Dict[str, str]           # 输出文件路径
    logs: Dict[str, str]                # 日志文件路径
    metrics: Dict[str, Any]             # 构建指标
    warnings: List[str] = None          # 警告信息
    errors: List[str] = None            # 错误信息
    duration: float = 0.0               # 构建时长（秒）

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


@dataclass
class IPCoreInfo:
    """IP核信息"""
    name: str                           # IP核名称
    version: str                        # 版本号
    vendor: str                         # 厂商
    description: str                    # 描述
    interfaces: List[str]               # 支持的接口
    parameters: Dict[str, Any]          # 参数定义
    file_path: Path                     # 文件路径
    dependencies: List[str] = None      # 依赖项

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class BasePlugin(ABC):
    """插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """插件类型"""
        pass

    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"

    @property
    def description(self) -> str:
        """插件描述"""
        return ""

    @property
    def author(self) -> str:
        """插件作者"""
        return ""

    def initialize(self) -> bool:
        """初始化插件"""
        return True

    def cleanup(self) -> bool:
        """清理插件"""
        return True

    @property
    def supported_tool_versions(self) -> Dict[str, VersionRange]:
        """支持的工具体版本范围"""
        return {}

    def detect_tool(self, tool_name: str) -> Optional[ToolInfo]:
        """检测工具安装情况和版本"""
        # 基类实现，子类应重写此方法
        return None

    def detect_all_tools(self) -> Dict[str, ToolInfo]:
        """检测所有相关工具"""
        tools = {}
        for tool_name in self.supported_tool_versions.keys():
            tool_info = self.detect_tool(tool_name)
            if tool_info:
                tools[tool_name] = tool_info
        return tools

    def check_tool_compatibility(self) -> Tuple[bool, List[str], Dict[str, ToolInfo]]:
        """检查工具兼容性"""
        tools = self.detect_all_tools()
        issues = []
        all_compatible = True

        for tool_name, tool_info in tools.items():
            if not tool_info.installed:
                issues.append(f"工具未安装: {tool_name}")
                all_compatible = False
            elif not tool_info.is_compatible():
                version_range = self.supported_tool_versions.get(tool_name)
                if version_range:
                    issues.append(
                        f"工具版本不兼容: {tool_name} {tool_info.version} "
                        f"(需要 {version_range})"
                    )
                    all_compatible = False

        return all_compatible, issues, tools

    def get_compatibility_report(self) -> str:
        """获取兼容性报告"""
        compatible, issues, tools = self.check_tool_compatibility()

        report_lines = [f"插件: {self.name}"]
        report_lines.append(f"兼容性: {'✅ 通过' if compatible else '❌ 失败'}")

        if tools:
            report_lines.append("\n检测到的工具:")
            for tool_name, tool_info in tools.items():
                status = "✅" if tool_info.is_compatible() else "❌"
                report_lines.append(
                    f"  {status} {tool_name}: {tool_info.version} "
                    f"(路径: {tool_info.path})"
                )

        if issues:
            report_lines.append("\n问题:")
            for issue in issues:
                report_lines.append(f"  • {issue}")

        if self.supported_tool_versions:
            report_lines.append("\n支持的版本范围:")
            for tool_name, version_range in self.supported_tool_versions.items():
                report_lines.append(f"  • {tool_name}: {version_range}")

        return "\n".join(report_lines)

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证配置"""
        return True, []


class FPGAVendorPlugin(BasePlugin):
    """FPGA厂商插件基类"""

    @property
    @abstractmethod
    def vendor(self) -> str:
        """支持的FPGA厂商"""
        pass

    @property
    def supported_families(self) -> List[str]:
        """支持的FPGA系列"""
        return []

    @property
    def supported_parts(self) -> List[str]:
        """支持的FPGA器件"""
        return []

    @abstractmethod
    def create_project(self, config: Dict[str, Any]) -> BuildResult:
        """创建工程"""
        pass

    @abstractmethod
    def synthesize(self, config: Dict[str, Any]) -> BuildResult:
        """综合"""
        pass

    @abstractmethod
    def implement(self, config: Dict[str, Any]) -> BuildResult:
        """实现（布局布线）"""
        pass

    @abstractmethod
    def generate_bitstream(self, config: Dict[str, Any]) -> BuildResult:
        """生成比特流"""
        pass

    @abstractmethod
    def program_device(self, config: Dict[str, Any]) -> BuildResult:
        """烧录设备"""
        pass

    def generate_tcl_script(self, config: Dict[str, Any]) -> str:
        """生成TCL脚本"""
        return ""

    def generate_reports(self, config: Dict[str, Any]) -> BuildResult:
        """生成报告"""
        pass

    def simulate(self, config: Dict[str, Any]) -> BuildResult:
        """仿真"""
        pass

    def get_available_ips(self) -> List[IPCoreInfo]:
        """获取可用的IP核"""
        return []


class IPCorePlugin(BasePlugin):
    """IP核插件基类"""

    @property
    @abstractmethod
    def ip_family(self) -> str:
        """IP核系列"""
        pass

    @abstractmethod
    def create_ip(self, config: Dict[str, Any]) -> BuildResult:
        """创建IP核"""
        pass

    @abstractmethod
    def package_ip(self, config: Dict[str, Any]) -> BuildResult:
        """打包IP核"""
        pass

    @abstractmethod
    def generate_documentation(self, config: Dict[str, Any]) -> BuildResult:
        """生成文档"""
        pass

    def validate_ip(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证IP核"""
        return True, []

    def get_ip_templates(self) -> List[Dict[str, Any]]:
        """获取IP核模板"""
        return []


class HLSPlugin(BasePlugin):
    """HLS插件基类"""

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """支持的HLS语言"""
        pass

    @abstractmethod
    def create_project(self, config: Dict[str, Any]) -> BuildResult:
        """创建HLS工程"""
        pass

    @abstractmethod
    def compile(self, config: Dict[str, Any]) -> BuildResult:
        """编译HLS工程"""
        pass

    @abstractmethod
    def cosimulate(self, config: Dict[str, Any]) -> BuildResult:
        """协同仿真"""
        pass

    @abstractmethod
    def export_ip(self, config: Dict[str, Any]) -> BuildResult:
        """导出IP核"""
        pass

    def validate_source(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证源代码"""
        return True, []


class DocumentationPlugin(BasePlugin):
    """文档插件基类"""

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """支持的文档格式"""
        pass

    @abstractmethod
    def generate_documentation(self, config: Dict[str, Any]) -> BuildResult:
        """生成文档"""
        pass

    def merge_documentation(self, config: Dict[str, Any]) -> BuildResult:
        """合并文档"""
        pass

    def publish_documentation(self, config: Dict[str, Any]) -> BuildResult:
        """发布文档"""
        pass


class DeploymentPlugin(BasePlugin):
    """部署插件基类"""

    @property
    @abstractmethod
    def supported_targets(self) -> List[str]:
        """支持的部署目标"""
        pass

    @abstractmethod
    def deploy(self, config: Dict[str, Any]) -> BuildResult:
        """部署"""
        pass

    def validate_deployment(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证部署配置"""
        return True, []

    def rollback(self, config: Dict[str, Any]) -> BuildResult:
        """回滚部署"""
        pass


class ToolPlugin(BasePlugin):
    """工具插件基类"""

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """工具名称"""
        pass

    @abstractmethod
    def execute(self, config: Dict[str, Any]) -> BuildResult:
        """执行工具"""
        pass

    @property
    def tool_version(self) -> str:
        """工具版本"""
        return ""

    def get_help(self) -> str:
        """获取工具帮助"""
        return ""


# 插件装饰器
def register_plugin(plugin_class):
    """插件注册装饰器"""
    plugin_class._is_registered = True
    return plugin_class


def plugin_info(name: str, plugin_type: PluginType, version: str = "1.0.0"):
    """插件信息装饰器"""
    def decorator(cls):
        cls._plugin_name = name
        cls._plugin_type = plugin_type
        cls._plugin_version = version
        return cls
    return decorator


# 工具检测实用函数
class ToolDetector:
    """工具检测器"""

    @staticmethod
    def find_executable(executable_name: str) -> Optional[Path]:
        """查找可执行文件"""
        # 检查系统PATH
        import shutil
        path = shutil.which(executable_name)
        if path:
            return Path(path)

        # 检查常见安装路径（Windows）
        if sys.platform == "win32":
            common_paths = [
                Path("C:/Xilinx/Vivado"),
                Path("C:/Xilinx/Vitis"),
                Path("C:/intelFPGA"),
                Path("C:/Altera"),
                Path("C:/lscc"),
            ]
            for base_path in common_paths:
                if base_path.exists():
                    # 递归查找可执行文件
                    for exe_path in base_path.rglob(f"{executable_name}.exe"):
                        return exe_path
                    for exe_path in base_path.rglob(f"{executable_name}.bat"):
                        return exe_path

        return None

    @staticmethod
    def get_version_from_executable(executable_path: Path, version_arg: str = "--version") -> Optional[str]:
        """从可执行文件获取版本"""
        try:
            result = subprocess.run(
                [str(executable_path), version_arg],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # 尝试从输出中提取版本号
                output = result.stdout + result.stderr
                # 查找类似 "Version 2023.1" 或 "v2023.1" 的版本
                version_patterns = [
                    r'Version\s+([\d.]+)',
                    r'v([\d.]+)',
                    r'([\d]{4}\.[\d]+)',
                    r'([\d]+\.[\d]+\.[\d]+)'
                ]
                for pattern in version_patterns:
                    match = re.search(pattern, output)
                    if match:
                        return match.group(1)
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            pass
        return None

    @staticmethod
    def detect_vivado() -> Optional[ToolInfo]:
        """检测Vivado安装"""
        vivado_exe = ToolDetector.find_executable("vivado")
        if not vivado_exe:
            return None

        version = ToolDetector.get_version_from_executable(vivado_exe)
        if not version:
            # 尝试从路径中提取版本
            path_str = str(vivado_exe)
            version_match = re.search(r'Vivado[/\\]([\d]{4}\.[\d]+)', path_str)
            if version_match:
                version = version_match.group(1)

        return ToolInfo(
            name="vivado",
            version=version or "unknown",
            path=vivado_exe
        )

    @staticmethod
    def detect_quartus() -> Optional[ToolInfo]:
        """检测Quartus安装"""
        quartus_exe = ToolDetector.find_executable("quartus")
        if not quartus_exe:
            return None

        version = ToolDetector.get_version_from_executable(quartus_exe)
        return ToolInfo(
            name="quartus",
            version=version or "unknown",
            path=quartus_exe
        )

    @staticmethod
    def detect_vitis_hls() -> Optional[ToolInfo]:
        """检测Vitis HLS安装"""
        vitis_hls_exe = ToolDetector.find_executable("vitis_hls")
        if not vitis_hls_exe:
            return None

        version = ToolDetector.get_version_from_executable(vitis_hls_exe)
        return ToolInfo(
            name="vitis_hls",
            version=version or "unknown",
            path=vitis_hls_exe
        )

    @staticmethod
    def detect_vivado_with_config(config: Dict[str, Any]) -> Optional[ToolInfo]:
        """根据配置检测Vivado安装"""
        fpga_config = config.get('fpga', {})
        vivado_path = fpga_config.get('vivado_path')
        vivado_version = fpga_config.get('vivado_version')

        # 获取Vivado设置
        vivado_settings = fpga_config.get('vivado_settings', {})
        target_version = vivado_settings.get('target_version', vivado_version)

        # 如果提供了路径，使用指定路径
        if vivado_path:
            path = Path(vivado_path)
            if path.exists():
                # 如果路径是文件，直接使用
                if path.is_file():
                    vivado_exe = path
                else:
                    # 如果路径是目录，查找vivado可执行文件
                    if sys.platform == "win32":
                        # Windows: 查找vivado.bat
                        exe_path = path / "vivado.bat"
                        if exe_path.exists():
                            vivado_exe = exe_path
                        else:
                            # 递归查找
                            for exe in path.rglob("vivado.bat"):
                                vivado_exe = exe
                                break
                            else:
                                vivado_exe = None
                    else:
                        # Linux: 查找vivado
                        exe_path = path / "vivado"
                        if exe_path.exists():
                            vivado_exe = exe_path
                        else:
                            for exe in path.rglob("vivado"):
                                vivado_exe = exe
                                break
                            else:
                                vivado_exe = None

                if vivado_exe and vivado_exe.exists():
                    # 获取版本
                    version = vivado_version
                    if not version:
                        version = ToolDetector.get_version_from_executable(vivado_exe)
                        if not version:
                            # 从路径中提取版本
                            path_str = str(vivado_exe)
                            version_match = re.search(r'Vivado[/\\]([\d]{4}\.[\d]+)', path_str)
                            if version_match:
                                version = version_match.group(1)

                    # 验证可执行文件
                    if not ToolDetector._validate_vivado_executable(vivado_exe):
                        logger.warning(f"Vivado可执行文件验证失败: {vivado_exe}")
                        # 继续，但记录警告

                    # 检查版本兼容性
                    version_compatible = True
                    if target_version and version != "unknown":
                        # 简单版本检查：主要版本匹配
                        target_major = target_version.split('.')[0]
                        actual_major = version.split('.')[0]
                        if target_major != actual_major:
                            version_compatible = False
                            logger.warning(
                                f"Vivado版本不匹配: 配置版本={target_version}, "
                                f"实际版本={version}"
                            )

                    return ToolInfo(
                        name="vivado",
                        version=version or "unknown",
                        path=vivado_exe,
                        version_range=VersionRange(
                            min_version="2018.0",
                            max_version="2024.2",
                            recommended_version="2023.2"
                        ) if version != "unknown" else None
                    )
            else:
                logger.warning(f"配置的Vivado路径不存在: {vivado_path}")

        # 如果没有提供路径或路径无效，回退到自动检测
        return ToolDetector.detect_vivado()

    @staticmethod
    def _validate_vivado_executable(executable_path: Path) -> bool:
        """验证Vivado可执行文件"""
        try:
            # 检查文件权限
            if not executable_path.is_file():
                return False

            # 尝试执行简单的版本检查
            result = subprocess.run(
                [str(executable_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # 如果返回0或者有输出，认为有效
            return result.returncode == 0 or len(result.stdout) > 0
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            return False


# 版本适配器基类
class VersionAdapter(ABC):
    """版本适配器基类"""

    def __init__(self, tool_info: ToolInfo):
        self.tool_info = tool_info
        self.version = tool_info.version

    @abstractmethod
    def adapt_command(self, command: List[str]) -> List[str]:
        """适配命令参数"""
        pass

    @abstractmethod
    def adapt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """适配配置"""
        pass

    @abstractmethod
    def adapt_output(self, output: str) -> str:
        """适配输出解析"""
        pass


# 版本适配器注册表
class VersionAdapterRegistry:
    """版本适配器注册表"""

    _adapters: Dict[str, Dict[str, Type[VersionAdapter]]] = {}

    @classmethod
    def register(cls, tool_name: str, version_pattern: str, adapter_class: Type[VersionAdapter]):
        """注册适配器"""
        if tool_name not in cls._adapters:
            cls._adapters[tool_name] = {}
        cls._adapters[tool_name][version_pattern] = adapter_class

    @classmethod
    def get_adapter(cls, tool_info: ToolInfo) -> Optional[VersionAdapter]:
        """获取适配器"""
        if tool_info.name not in cls._adapters:
            return None

        # 查找匹配的适配器
        for version_pattern, adapter_class in cls._adapters[tool_info.name].items():
            if re.match(version_pattern, tool_info.version):
                return adapter_class(tool_info)

        return None