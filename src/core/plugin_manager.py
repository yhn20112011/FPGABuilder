#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
插件管理器
"""

import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Set, Tuple
import logging

from .plugin_base import (
    BasePlugin, FPGAVendorPlugin, IPCorePlugin, HLSPlugin,
    DocumentationPlugin, DeploymentPlugin, ToolPlugin, PluginType
)


class PluginManagerError(Exception):
    """插件管理器错误"""
    pass


class PluginNotFoundError(PluginManagerError):
    """插件未找到错误"""
    pass


class PluginManager:
    """插件管理器"""

    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        self.plugin_dirs = plugin_dirs or []
        self._plugins: Dict[str, BasePlugin] = {}
        self._vendor_plugins: Dict[str, FPGAVendorPlugin] = {}
        self._ip_plugins: Dict[str, IPCorePlugin] = {}
        self._hls_plugins: Dict[str, HLSPlugin] = {}
        self._doc_plugins: Dict[str, DocumentationPlugin] = {}
        self._deployment_plugins: Dict[str, DeploymentPlugin] = {}
        self._tool_plugins: Dict[str, ToolPlugin] = {}

        self.logger = logging.getLogger(__name__)

        # 添加默认插件目录
        self._add_default_plugin_dirs()

    def _add_default_plugin_dirs(self):
        """添加默认插件目录"""
        # 添加内置插件目录
        builtin_plugin_dir = Path(__file__).parent.parent / 'plugins'
        if builtin_plugin_dir.exists():
            self.plugin_dirs.append(builtin_plugin_dir)

        # 添加用户插件目录
        user_plugin_dir = Path.home() / '.fpga_builder' / 'plugins'
        self.plugin_dirs.append(user_plugin_dir)

    def discover_plugins(self) -> None:
        """发现所有插件"""
        self.logger.info("开始发现插件...")

        # 清空现有插件
        self._plugins.clear()
        self._vendor_plugins.clear()
        self._ip_plugins.clear()
        self._hls_plugins.clear()
        self._doc_plugins.clear()
        self._deployment_plugins.clear()
        self._tool_plugins.clear()

        # 遍历所有插件目录
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                self.logger.debug(f"插件目录不存在: {plugin_dir}")
                continue

            self.logger.info(f"扫描插件目录: {plugin_dir}")

            # 添加插件目录到Python路径
            if str(plugin_dir.parent) not in sys.path:
                sys.path.insert(0, str(plugin_dir.parent))

            # 查找插件模块
            for finder, module_name, is_pkg in pkgutil.iter_modules([str(plugin_dir)]):
                if not is_pkg:
                    continue

                try:
                    plugin_module = importlib.import_module(f"plugins.{module_name}")
                    self._register_plugin_module(plugin_module)
                except ImportError as e:
                    self.logger.error(f"导入插件模块失败: {module_name}, 错误: {e}")
                except Exception as e:
                    self.logger.error(f"注册插件失败: {module_name}, 错误: {e}")

        self.logger.info(f"插件发现完成，共发现 {len(self._plugins)} 个插件")

    def _register_plugin_module(self, plugin_module) -> None:
        """注册插件模块"""
        # 查找模块中定义的插件类
        for attr_name in dir(plugin_module):
            attr = getattr(plugin_module, attr_name)

            # 检查是否为插件类
            if (isinstance(attr, type) and
                issubclass(attr, BasePlugin) and
                attr != BasePlugin and
                hasattr(attr, '_is_registered')):

                try:
                    plugin_instance = attr()
                    self._register_plugin_instance(plugin_instance)
                except Exception as e:
                    self.logger.error(f"实例化插件失败: {attr_name}, 错误: {e}")

    def _register_plugin_instance(self, plugin_instance: BasePlugin) -> None:
        """注册插件实例"""
        plugin_name = plugin_instance.name

        # 检查插件是否已注册
        if plugin_name in self._plugins:
            self.logger.warning(f"插件已存在，跳过: {plugin_name}")
            return

        # 初始化插件
        try:
            if not plugin_instance.initialize():
                self.logger.error(f"插件初始化失败: {plugin_name}")
                return
        except Exception as e:
            self.logger.error(f"插件初始化异常: {plugin_name}, 错误: {e}")
            return

        # 根据插件类型注册到相应的字典
        plugin_type = plugin_instance.plugin_type

        if isinstance(plugin_instance, FPGAVendorPlugin):
            self._vendor_plugins[plugin_name] = plugin_instance
            self.logger.info(f"注册FPGA厂商插件: {plugin_name} ({plugin_instance.vendor})")
        elif isinstance(plugin_instance, IPCorePlugin):
            self._ip_plugins[plugin_name] = plugin_instance
            self.logger.info(f"注册IP核插件: {plugin_name}")
        elif isinstance(plugin_instance, HLSPlugin):
            self._hls_plugins[plugin_name] = plugin_instance
            self.logger.info(f"注册HLS插件: {plugin_name}")
        elif isinstance(plugin_instance, DocumentationPlugin):
            self._doc_plugins[plugin_name] = plugin_instance
            self.logger.info(f"注册文档插件: {plugin_name}")
        elif isinstance(plugin_instance, DeploymentPlugin):
            self._deployment_plugins[plugin_name] = plugin_instance
            self.logger.info(f"注册部署插件: {plugin_name}")
        elif isinstance(plugin_instance, ToolPlugin):
            self._tool_plugins[plugin_name] = plugin_instance
            self.logger.info(f"注册工具插件: {plugin_name}")
        else:
            self.logger.warning(f"未知插件类型: {plugin_name}")

        # 注册到总插件字典
        self._plugins[plugin_name] = plugin_instance

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件"""
        return self._plugins.get(plugin_name)

    def get_vendor_plugin(self, vendor_name: str) -> Optional[FPGAVendorPlugin]:
        """获取指定厂商的插件"""
        for plugin in self._vendor_plugins.values():
            if plugin.vendor.lower() == vendor_name.lower():
                return plugin
        return None

    def get_vendor_plugin_by_name(self, plugin_name: str) -> Optional[FPGAVendorPlugin]:
        """通过插件名称获取厂商插件"""
        return self._vendor_plugins.get(plugin_name)

    def get_ip_plugin(self, plugin_name: str) -> Optional[IPCorePlugin]:
        """获取IP核插件"""
        return self._ip_plugins.get(plugin_name)

    def get_hls_plugin(self, plugin_name: str) -> Optional[HLSPlugin]:
        """获取HLS插件"""
        return self._hls_plugins.get(plugin_name)

    def get_documentation_plugin(self, plugin_name: str) -> Optional[DocumentationPlugin]:
        """获取文档插件"""
        return self._doc_plugins.get(plugin_name)

    def get_deployment_plugin(self, plugin_name: str) -> Optional[DeploymentPlugin]:
        """获取部署插件"""
        return self._deployment_plugins.get(plugin_name)

    def get_tool_plugin(self, plugin_name: str) -> Optional[ToolPlugin]:
        """获取工具插件"""
        return self._tool_plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有插件"""
        return self._plugins.copy()

    def get_all_vendor_plugins(self) -> Dict[str, FPGAVendorPlugin]:
        """获取所有厂商插件"""
        return self._vendor_plugins.copy()

    def get_all_vendors(self) -> List[str]:
        """获取所有支持的厂商"""
        return [plugin.vendor for plugin in self._vendor_plugins.values()]

    def get_all_ip_plugins(self) -> Dict[str, IPCorePlugin]:
        """获取所有IP核插件"""
        return self._ip_plugins.copy()

    def get_all_hls_plugins(self) -> Dict[str, HLSPlugin]:
        """获取所有HLS插件"""
        return self._hls_plugins.copy()

    def get_all_documentation_plugins(self) -> Dict[str, DocumentationPlugin]:
        """获取所有文档插件"""
        return self._doc_plugins.copy()

    def get_all_deployment_plugins(self) -> Dict[str, DeploymentPlugin]:
        """获取所有部署插件"""
        return self._deployment_plugins.copy()

    def get_all_tool_plugins(self) -> Dict[str, ToolPlugin]:
        """获取所有工具插件"""
        return self._tool_plugins.copy()

    def get_plugins_by_type(self, plugin_type: PluginType) -> Dict[str, BasePlugin]:
        """根据类型获取插件"""
        plugins = {}

        for name, plugin in self._plugins.items():
            if plugin.plugin_type == plugin_type:
                plugins[name] = plugin

        return plugins

    def has_plugin(self, plugin_name: str) -> bool:
        """检查插件是否存在"""
        return plugin_name in self._plugins

    def has_vendor(self, vendor_name: str) -> bool:
        """检查厂商插件是否存在"""
        return self.get_vendor_plugin(vendor_name) is not None

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name not in self._plugins:
            return False

        plugin = self._plugins[plugin_name]

        try:
            # 清理插件
            plugin.cleanup()

            # 从相应字典中移除
            if isinstance(plugin, FPGAVendorPlugin):
                del self._vendor_plugins[plugin_name]
            elif isinstance(plugin, IPCorePlugin):
                del self._ip_plugins[plugin_name]
            elif isinstance(plugin, HLSPlugin):
                del self._hls_plugins[plugin_name]
            elif isinstance(plugin, DocumentationPlugin):
                del self._doc_plugins[plugin_name]
            elif isinstance(plugin, DeploymentPlugin):
                del self._deployment_plugins[plugin_name]
            elif isinstance(plugin, ToolPlugin):
                del self._tool_plugins[plugin_name]

            # 从总字典中移除
            del self._plugins[plugin_name]

            self.logger.info(f"插件已卸载: {plugin_name}")
            return True

        except Exception as e:
            self.logger.error(f"卸载插件失败: {plugin_name}, 错误: {e}")
            return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件"""
        if plugin_name not in self._plugins:
            return False

        # 先卸载插件
        if not self.unload_plugin(plugin_name):
            return False

        # 重新发现插件
        self.discover_plugins()

        # 检查插件是否重新加载成功
        return plugin_name in self._plugins

    def reload_all_plugins(self) -> bool:
        """重新加载所有插件"""
        self.logger.info("重新加载所有插件...")

        # 获取当前所有插件名称
        plugin_names = list(self._plugins.keys())

        # 清空插件字典
        self._plugins.clear()
        self._vendor_plugins.clear()
        self._ip_plugins.clear()
        self._hls_plugins.clear()
        self._doc_plugins.clear()
        self._deployment_plugins.clear()
        self._tool_plugins.clear()

        # 重新发现插件
        self.discover_plugins()

        # 检查是否所有插件都重新加载成功
        missing_plugins = [name for name in plugin_names if name not in self._plugins]

        if missing_plugins:
            self.logger.warning(f"以下插件未能重新加载: {missing_plugins}")
            return False

        self.logger.info("所有插件重新加载完成")
        return True

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件信息"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return None

        info = {
            'name': plugin.name,
            'type': plugin.plugin_type.value,
            'version': plugin.version,
            'description': plugin.description,
            'author': plugin.author,
            'initialized': True
        }

        # 添加特定类型插件的额外信息
        if isinstance(plugin, FPGAVendorPlugin):
            info.update({
                'vendor': plugin.vendor,
                'supported_families': plugin.supported_families,
                'supported_parts': plugin.supported_parts
            })
        elif isinstance(plugin, IPCorePlugin):
            info.update({
                'ip_family': plugin.ip_family
            })
        elif isinstance(plugin, HLSPlugin):
            info.update({
                'supported_languages': plugin.supported_languages
            })
        elif isinstance(plugin, DocumentationPlugin):
            info.update({
                'supported_formats': plugin.supported_formats
            })
        elif isinstance(plugin, DeploymentPlugin):
            info.update({
                'supported_targets': plugin.supported_targets
            })
        elif isinstance(plugin, ToolPlugin):
            info.update({
                'tool_name': plugin.tool_name,
                'tool_version': plugin.tool_version
            })

        return info

    def check_all_plugin_compatibility(self) -> Dict[str, Dict[str, Any]]:
        """检查所有插件的工具兼容性"""
        compatibility_report = {}

        for plugin_name, plugin in self._plugins.items():
            try:
                # 检查插件兼容性
                compatible, issues, tools = plugin.check_tool_compatibility()

                compatibility_report[plugin_name] = {
                    'plugin_type': plugin.plugin_type.value,
                    'compatible': compatible,
                    'issues': issues,
                    'tools': {
                        tool_name: {
                            'version': tool_info.version,
                            'path': str(tool_info.path),
                            'installed': tool_info.installed,
                            'compatible': tool_info.is_compatible() if tool_info.installed else False
                        }
                        for tool_name, tool_info in tools.items()
                    }
                }

                self.logger.info(f"插件兼容性检查: {plugin_name} - {'✅ 通过' if compatible else '❌ 失败'}")

            except Exception as e:
                self.logger.error(f"检查插件兼容性失败: {plugin_name}, 错误: {e}")
                compatibility_report[plugin_name] = {
                    'plugin_type': plugin.plugin_type.value,
                    'compatible': False,
                    'issues': [f"兼容性检查失败: {str(e)}"],
                    'tools': {}
                }

        return compatibility_report

    def get_compatibility_summary(self) -> str:
        """获取兼容性摘要报告"""
        report = self.check_all_plugin_compatibility()

        summary_lines = ["FPGABuilder 插件兼容性报告", "=" * 40]

        total_plugins = len(report)
        compatible_plugins = sum(1 for data in report.values() if data['compatible'])
        incompatible_plugins = total_plugins - compatible_plugins

        summary_lines.append(f"插件总数: {total_plugins}")
        summary_lines.append(f"兼容插件: {compatible_plugins} ✅")
        summary_lines.append(f"不兼容插件: {incompatible_plugins} ❌")
        summary_lines.append("")

        for plugin_name, data in report.items():
            status = "✅" if data['compatible'] else "❌"
            summary_lines.append(f"{status} {plugin_name} ({data['plugin_type']})")

            if data['issues']:
                summary_lines.append("  问题:")
                for issue in data['issues']:
                    summary_lines.append(f"    • {issue}")

            if data['tools']:
                summary_lines.append("  检测到的工具:")
                for tool_name, tool_info in data['tools'].items():
                    tool_status = "✅" if tool_info['compatible'] else "❌"
                    summary_lines.append(
                        f"    {tool_status} {tool_name}: {tool_info['version']}"
                    )

            summary_lines.append("")

        return "\n".join(summary_lines)

    def validate_config(self, plugin_name: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证插件配置"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return False, [f"插件不存在: {plugin_name}"]

        return plugin.validate_config(config)

    def shutdown(self) -> None:
        """关闭插件管理器"""
        self.logger.info("关闭插件管理器...")

        # 清理所有插件
        for plugin_name in list(self._plugins.keys()):
            try:
                self.unload_plugin(plugin_name)
            except Exception as e:
                self.logger.error(f"清理插件失败: {plugin_name}, 错误: {e}")

        self.logger.info("插件管理器已关闭")


# 全局插件管理器实例
_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    global _global_plugin_manager

    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
        _global_plugin_manager.discover_plugins()

    return _global_plugin_manager


def set_plugin_dirs(plugin_dirs: List[Path]) -> None:
    """设置插件目录"""
    global _global_plugin_manager

    if _global_plugin_manager is not None:
        raise PluginManagerError("插件管理器已初始化，无法设置插件目录")

    _global_plugin_manager = PluginManager(plugin_dirs)


def shutdown_plugin_manager() -> None:
    """关闭全局插件管理器"""
    global _global_plugin_manager

    if _global_plugin_manager is not None:
        _global_plugin_manager.shutdown()
        _global_plugin_manager = None