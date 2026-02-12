#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vivado文件扫描器
支持通配符路径模式匹配和文件类型检测
"""

import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import fnmatch


class FileScanner:
    """文件扫描器，支持通配符路径模式匹配和文件类型检测"""

    # 文件扩展名到语言的映射
    EXTENSION_TO_LANGUAGE = {
        '.v': 'verilog',
        '.vh': 'verilog',
        '.sv': 'systemverilog',
        '.svh': 'systemverilog',
        '.vhd': 'vhdl',
        '.vhdl': 'vhdl',
        '.xdc': 'constraint',
        '.tcl': 'tcl',
        '.bd': 'block_design',
        '.xci': 'ip_core',
        '.xco': 'ip_core',
        '.xml': 'xml'
    }

    # 语言到默认扩展名的映射
    LANGUAGE_TO_EXTENSION = {
        'verilog': ['.v', '.vh'],
        'systemverilog': ['.sv', '.svh'],
        'vhdl': ['.vhd', '.vhdl'],
        'constraint': ['.xdc'],
        'tcl': ['.tcl']
    }

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化文件扫描器

        Args:
            base_path: 基础路径，所有相对路径都基于此路径
        """
        self.base_path = base_path or Path.cwd()

    def scan_files(self, config: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        扫描配置文件中的文件

        Args:
            config: 项目配置

        Returns:
            扫描结果字典，包含hdl、constraints等文件列表
        """
        results = {
            'hdl': [],
            'constraints': [],
            'ip_cores': [],
            'block_designs': []
        }

        source_config = config.get('source', {})

        # 扫描HDL文件
        hdl_configs = source_config.get('hdl', [])
        for hdl_config in hdl_configs:
            hdl_files = self._scan_hdl_files(hdl_config)
            results['hdl'].extend(hdl_files)

        # 扫描约束文件
        constraint_configs = source_config.get('constraints', [])
        for constraint_config in constraint_configs:
            constraint_files = self._scan_constraint_files(constraint_config)
            results['constraints'].extend(constraint_files)

        # 扫描IP核文件
        ip_configs = source_config.get('ip_cores', [])
        for ip_config in ip_configs:
            ip_files = self._scan_ip_files(ip_config)
            results['ip_cores'].extend(ip_files)

        # 扫描Block Design文件
        bd_config = source_config.get('block_design')
        if bd_config:
            bd_files = self._scan_block_design_files(bd_config)
            results['block_designs'].extend(bd_files)

        return results

    def _scan_hdl_files(self, hdl_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """扫描HDL文件"""
        files = []

        # 优先使用pattern字段
        pattern = hdl_config.get('pattern')
        if pattern:
            matched_files = self._expand_pattern(pattern, hdl_config.get('exclude', []))
        else:
            # 使用path字段
            path = hdl_config.get('path')
            if not path:
                return files

            # 检查path是文件还是目录模式
            path_obj = Path(path)
            if self._is_pattern(path):
                matched_files = self._expand_pattern(path, hdl_config.get('exclude', []))
            else:
                # 单个文件
                matched_files = [path_obj] if path_obj.exists() else []

        # 处理每个匹配的文件
        for file_path in matched_files:
            if not file_path.exists():
                continue

            # 确定语言
            language = hdl_config.get('language', 'auto')
            if language == 'auto':
                language = self._detect_language(file_path)

            # 确定文件类型
            file_type = hdl_config.get('file_type', 'source')

            file_info = {
                'path': str(file_path),
                'absolute_path': str(file_path.absolute()),
                'relative_path': str(file_path.relative_to(self.base_path) if file_path.is_relative_to(self.base_path) else file_path),
                'language': language,
                'file_type': file_type,
                'include_dirs': hdl_config.get('include_dirs', []),
                'size': file_path.stat().st_size if file_path.exists() else 0
            }
            files.append(file_info)

        return files

    def _scan_constraint_files(self, constraint_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """扫描约束文件"""
        files = []

        path = constraint_config.get('path')
        if not path:
            return files

        # 检查是否是模式
        if self._is_pattern(path):
            matched_files = self._expand_pattern(path, constraint_config.get('exclude', []))
        else:
            # 单个文件
            path_obj = Path(path)
            matched_files = [path_obj] if path_obj.exists() else []

        for file_path in matched_files:
            if not file_path.exists():
                continue

            file_info = {
                'path': str(file_path),
                'absolute_path': str(file_path.absolute()),
                'relative_path': str(file_path.relative_to(self.base_path) if file_path.is_relative_to(self.base_path) else file_path),
                'type': constraint_config.get('type', 'xdc'),
                'size': file_path.stat().st_size if file_path.exists() else 0
            }
            files.append(file_info)

        return files

    def _scan_ip_files(self, ip_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """扫描IP核文件"""
        files = []

        path = ip_config.get('path')
        if not path:
            return files

        path_obj = Path(path)
        if not path_obj.exists():
            return files

        # 如果是目录，查找IP核文件
        if path_obj.is_dir():
            # 查找所有IP核相关文件
            ip_files = []
            # XCI文件（现代IP核格式）
            ip_files.extend(list(path_obj.rglob('*.xci')))
            # XCO文件（旧版IP核格式）
            ip_files.extend(list(path_obj.rglob('*.xco')))
            # component.xml文件（IP核目录标识）
            ip_files.extend(list(path_obj.rglob('component.xml')))
            # IP核目录（包含.xci文件的目录）
            for subdir in path_obj.rglob('*'):
                if subdir.is_dir():
                    # 检查目录中是否有.xci文件
                    if any(subdir.glob('*.xci')):
                        ip_files.append(subdir / 'component.xml' if (subdir / 'component.xml').exists() else subdir)
        else:
            # 单个文件
            if path_obj.suffix.lower() in ['.xci', '.xco']:
                ip_files = [path_obj]
            elif path_obj.name == 'component.xml':
                ip_files = [path_obj]
            else:
                ip_files = []

        for file_path in ip_files:
            # 确定文件类型
            if file_path.suffix.lower() == '.xci':
                file_type = 'xci'
            elif file_path.suffix.lower() == '.xco':
                file_type = 'xco'
            elif file_path.name == 'component.xml':
                file_type = 'ip_dir'
            else:
                file_type = ip_config.get('type', 'unknown')

            file_info = {
                'name': ip_config.get('name', file_path.stem),
                'path': str(file_path),
                'absolute_path': str(file_path.absolute()),
                'relative_path': str(file_path.relative_to(self.base_path) if file_path.is_relative_to(self.base_path) else file_path),
                'type': file_type,
                'size': file_path.stat().st_size if file_path.exists() else 0,
                'is_directory': file_path.is_dir()
            }
            files.append(file_info)

        return files

    def _scan_block_design_files(self, bd_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """扫描Block Design文件"""
        files = []

        # 检查bd_file
        bd_file = bd_config.get('bd_file')
        if bd_file:
            bd_path = Path(bd_file)
            if bd_path.exists():
                file_info = {
                    'type': 'bd',
                    'path': str(bd_path),
                    'absolute_path': str(bd_path.absolute()),
                    'relative_path': str(bd_path.relative_to(self.base_path) if bd_path.is_relative_to(self.base_path) else bd_path),
                    'is_top': bd_config.get('is_top', False),
                    'wrapper_name': bd_config.get('wrapper_name'),
                    'auto_wrapper': bd_config.get('auto_wrapper', True)
                }
                files.append(file_info)

        # 检查tcl_script
        tcl_script = bd_config.get('tcl_script')
        if tcl_script:
            tcl_path = Path(tcl_script)
            if tcl_path.exists():
                file_info = {
                    'type': 'tcl',
                    'path': str(tcl_path),
                    'absolute_path': str(tcl_path.absolute()),
                    'relative_path': str(tcl_path.relative_to(self.base_path) if tcl_path.is_relative_to(self.base_path) else tcl_path),
                    'is_top': bd_config.get('is_top', False),
                    'wrapper_name': bd_config.get('wrapper_name'),
                    'auto_wrapper': bd_config.get('auto_wrapper', True)
                }
                files.append(file_info)

        return files

    def _expand_pattern(self, pattern: str, exclude_patterns: List[str] = None) -> List[Path]:
        """
        扩展通配符模式为文件列表

        Args:
            pattern: 通配符模式，支持**递归
            exclude_patterns: 排除模式列表

        Returns:
            匹配的文件路径列表
        """
        if exclude_patterns is None:
            exclude_patterns = []

        # 将模式转换为绝对路径
        if not Path(pattern).is_absolute():
            pattern = str(self.base_path / pattern)

        # 使用glob.glob支持递归通配符
        try:
            matched_files = glob.glob(pattern, recursive=True)
        except (OSError, ValueError):
            # 如果glob失败，尝试简单的路径检查
            path = Path(pattern)
            matched_files = [str(path)] if path.exists() else []

        # 转换为Path对象并过滤排除模式
        paths = []
        for file_path in matched_files:
            path = Path(file_path)

            # 跳过目录
            if not path.is_file():
                continue

            # 检查是否匹配排除模式
            if self._matches_exclude_patterns(path, exclude_patterns):
                continue

            paths.append(path)

        return paths

    def _matches_exclude_patterns(self, path: Path, exclude_patterns: List[str]) -> bool:
        """检查路径是否匹配任何排除模式"""
        for pattern in exclude_patterns:
            # 将模式转换为绝对路径
            if not Path(pattern).is_absolute():
                pattern = str(self.base_path / pattern)

            # 使用fnmatch进行模式匹配
            if fnmatch.fnmatch(str(path), pattern):
                return True

            # 也检查相对于基础路径
            try:
                rel_path = path.relative_to(self.base_path)
                if fnmatch.fnmatch(str(rel_path), pattern):
                    return True
            except ValueError:
                pass

        return False

    def _is_pattern(self, path_str: str) -> bool:
        """检查路径字符串是否包含通配符"""
        pattern_chars = ['*', '?', '[', ']']
        return any(char in path_str for char in pattern_chars) or '**' in path_str

    def _detect_language(self, file_path: Path) -> str:
        """检测文件的语言类型"""
        suffix = file_path.suffix.lower()

        # 检查扩展名映射
        language = self.EXTENSION_TO_LANGUAGE.get(suffix)
        if language:
            return language

        # 尝试通过内容检测
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)  # 读取前1KB

                # 简单的内容检测
                if 'module' in content and 'endmodule' in content:
                    return 'verilog'
                elif 'entity' in content and 'architecture' in content:
                    return 'vhdl'
                elif 'class' in content or 'interface' in content:
                    return 'systemverilog'
        except (IOError, UnicodeDecodeError):
            pass

        return 'unknown'

    def analyze_dependencies(self, hdl_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        分析HDL文件的依赖关系

        Args:
            hdl_files: HDL文件信息列表

        Returns:
            按依赖关系排序的文件列表
        """
        # 简单的依赖分析：基于模块/实体引用
        # 实际实现可能需要更复杂的解析

        # 首先收集所有模块/实体名称
        module_map = {}  # 模块名 -> 文件

        for file_info in hdl_files:
            file_path = Path(file_info['path'])
            modules = self._extract_modules(file_path, file_info['language'])
            for module in modules:
                module_map[module] = file_info

        # 简单的依赖排序：基于引用关系
        # 这里实现一个简单的拓扑排序
        sorted_files = []
        visited = set()

        def visit(file_info):
            if file_info['path'] in visited:
                return

            visited.add(file_info['path'])

            # 获取文件引用的模块
            file_path = Path(file_info['path'])
            references = self._extract_references(file_path, file_info['language'])

            # 先处理依赖的文件
            for ref in references:
                if ref in module_map:
                    dep_file = module_map[ref]
                    if dep_file['path'] != file_info['path']:
                        visit(dep_file)

            sorted_files.append(file_info)

        # 访问所有文件
        for file_info in hdl_files:
            if file_info['path'] not in visited:
                visit(file_info)

        return sorted_files

    def _extract_modules(self, file_path: Path, language: str) -> List[str]:
        """从文件中提取模块/实体名称"""
        modules = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if language in ['verilog', 'systemverilog']:
                # 查找Verilog模块定义
                pattern = r'^\s*module\s+(\w+)'
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                modules.extend(matches)

            elif language == 'vhdl':
                # 查找VHDL实体定义
                pattern = r'^\s*entity\s+(\w+)\s+is'
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                modules.extend(matches)

        except (IOError, UnicodeDecodeError):
            pass

        return modules

    def _extract_references(self, file_path: Path, language: str) -> List[str]:
        """从文件中提取引用的模块/实体"""
        references = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if language in ['verilog', 'systemverilog']:
                # 查找模块实例化
                pattern = r'^\s*(\w+)\s+\w+\s*\(|^\s*(\w+)\s+#'
                lines = content.split('\n')
                for line in lines:
                    # 跳过module定义行
                    if 'module' in line and 'endmodule' not in line:
                        continue
                    matches = re.findall(pattern, line)
                    for match in matches:
                        ref = match[0] or match[1]
                        if ref and ref not in ['assign', 'always', 'initial', 'if', 'else']:
                            references.append(ref)

            elif language == 'vhdl':
                # 查找实体实例化或use语句
                pattern = r'^\s*component\s+(\w+)|^\s*entity\s+work\.(\w+)|^\s*use\s+work\.(\w+)'
                lines = content.split('\n')
                for line in lines:
                    # 跳过entity定义行
                    if 'entity' in line and 'is' in line and 'end' not in line:
                        continue
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    for match in matches:
                        ref = match[0] or match[1] or match[2]
                        if ref:
                            references.append(ref)

        except (IOError, UnicodeDecodeError):
            pass

        return references

    def generate_vivado_file_commands(self, scanned_files: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[str]]:
        """
        生成Vivado TCL文件添加命令

        Args:
            scanned_files: 扫描的文件结果

        Returns:
            包含各种文件添加命令的字典
        """
        commands = {
            'hdl_commands': [],
            'constraint_commands': [],
            'ip_commands': [],
            'bd_commands': []
        }

        # HDL文件命令
        hdl_files = scanned_files.get('hdl', [])
        for file_info in hdl_files:
            cmd = f'add_files {{{file_info["path"]}}}'
            # 如果指定了语言，添加-language参数
            if file_info.get('language') != 'auto':
                cmd += f' -language {file_info["language"]}'
            commands['hdl_commands'].append(cmd)

        # 约束文件命令
        constraint_files = scanned_files.get('constraints', [])
        for file_info in constraint_files:
            cmd = f'add_files -fileset constrs_1 {{{file_info["path"]}}}'
            commands['constraint_commands'].append(cmd)

        # IP核文件命令
        ip_files = scanned_files.get('ip_cores', [])
        for file_info in ip_files:
            file_path = Path(file_info['path'])
            file_type = file_info.get('type', 'unknown')
            is_directory = file_info.get('is_directory', False)

            if file_type == 'xci':
                # Xilinx IP核文件（.xci），使用read_ip命令
                cmd = f'read_ip {{{file_info["path"]}}}'
            elif file_type == 'xco':
                # 旧版IP核文件（.xco），需要升级
                cmd = f'add_files {{{file_info["path"]}}}'
                cmd += '\n' + f'upgrade_ip [get_ips {{{file_path.stem}}}]'
            elif file_type == 'ip_dir' or is_directory:
                # IP核目录，使用add_files -norecurse
                cmd = f'add_files -norecurse {{{file_info["path"]}}}'
            elif file_path.suffix.lower() == '.xci':
                # 通过后缀检测XCI文件
                cmd = f'read_ip {{{file_info["path"]}}}'
            elif file_path.suffix.lower() == '.xco':
                # 通过后缀检测XCO文件
                cmd = f'add_files {{{file_info["path"]}}}'
                cmd += '\n' + f'upgrade_ip [get_ips {{{file_path.stem}}}]'
            elif file_path.name == 'component.xml':
                # component.xml文件
                cmd = f'add_files -norecurse {{{file_info["path"]}}}'
            else:
                # 其他IP核文件，使用add_files
                cmd = f'add_files {{{file_info["path"]}}}'

            commands['ip_commands'].append(cmd)

        # Block Design文件命令
        bd_files = scanned_files.get('block_designs', [])
        for file_info in bd_files:
            if file_info['type'] == 'bd':
                cmd = f'add_files {{{file_info["path"]}}}'
                commands['bd_commands'].append(cmd)

        return commands