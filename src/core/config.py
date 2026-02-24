#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
import jsonschema
from dataclasses import dataclass, field
from pydantic import BaseModel, ValidationError


class ConfigError(Exception):
    """配置错误异常"""
    pass


class ConfigValidationError(ConfigError):
    """配置验证错误"""
    pass


@dataclass
class ConfigManager:
    """配置管理器"""

    config_path: Optional[Path] = None
    config_data: Dict[str, Any] = field(default_factory=dict)
    config_schema: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化配置管理器"""
        self._load_schema()
        if self.config_path and self.config_path.exists():
            self.load_config(self.config_path)

    def _load_schema(self):
        """加载配置模式"""
        # 这里可以加载内置的模式文件
        self.config_schema = self._get_default_schema()

    def _get_default_schema(self) -> Dict[str, Any]:
        """获取默认配置模式"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "project": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "description": {"type": "string"},
                        "author": {"type": "string"},
                        "license": {"type": "string"}
                    },
                    "required": ["name", "version"]
                },
                "fpga": {
                    "type": "object",
                    "properties": {
                        "vendor": {
                            "type": "string",
                            "enum": ["xilinx", "altera", "lattice", "microchip"]
                        },
                        "family": {"type": "string"},
                        "part": {"type": "string"},
                        "board": {"type": "string"},
                        "top_module": {"type": "string"},
                        "vivado_version": {
                            "type": "string",
                            "pattern": "^\\d{4}\\.\\d+$",
                            "description": "Vivado版本号，格式：YYYY.N"
                        },
                        "vivado_path": {
                            "type": "string",
                            "description": "Vivado安装路径"
                        },
                        "vivado_settings": {
                            "type": "object",
                            "properties": {
                                "default_lib": {"type": "string"},
                                "target_language": {
                                    "type": "string",
                                    "enum": ["verilog", "vhdl"]
                                },
                                "synthesis_flow": {
                                    "type": "string",
                                    "enum": ["out_of_context", "project"]
                                },
                                "implementation_flow": {
                                    "type": "string",
                                    "enum": ["project", "non_project"]
                                }
                            }
                        }
                    },
                    "required": ["vendor", "part"]
                },
                "source": {
                    "type": "object",
                    "properties": {
                        "hdl": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "pattern": {
                                        "type": "string",
                                        "description": "支持通配符的文件模式，如 **/*.v, **/*.vhd"
                                    },
                                    "language": {
                                        "type": "string",
                                        "enum": ["verilog", "vhdl", "systemverilog", "auto"]
                                    },
                                    "language_auto_detect": {
                                        "type": "boolean",
                                        "description": "是否自动检测文件语言",
                                        "default": True
                                    },
                                    "file_type": {
                                        "type": "string",
                                        "enum": ["source", "test", "constraint", "include"],
                                        "default": "source"
                                    },
                                    "include_dirs": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "recursive": {"type": "boolean"},
                                    "exclude": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["path"]
                            }
                        },
                        "constraints": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "type": {"type": "string"},
                                    "recursive": {"type": "boolean"},
                                    "exclude": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["path"]
                            }
                        },
                        "ip_cores": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "path": {"type": "string"},
                                    "type": {"type": "string"}
                                },
                                "required": ["name", "path"]
                            }
                        },
                        "ip_repo_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "IP核仓库路径列表，用于设置set_property IP_REPO_PATHS",
                            "default": ["ip_repo"]
                        },
                        "block_design": {
                            "type": "object",
                            "properties": {
                                "bd_file": {
                                    "type": "string",
                                    "description": "Block Design文件路径 (.bd)"
                                },
                                "tcl_script": {
                                    "type": "string",
                                    "description": "用于生成Block Design的TCL脚本路径"
                                },
                                "is_top": {
                                    "type": "boolean",
                                    "description": "是否为顶层设计",
                                    "default": False
                                },
                                "wrapper_name": {
                                    "type": "string",
                                    "description": "包装器模块名称"
                                },
                                "auto_wrapper": {
                                    "type": "boolean",
                                    "description": "是否自动生成包装器",
                                    "default": True
                                },
                                "generate_wrapper": {
                                    "type": "boolean",
                                    "description": "是否生成包装器",
                                    "default": True
                                },
                                "wrapper_language": {
                                    "type": "string",
                                    "enum": ["verilog", "vhdl"],
                                    "default": "verilog"
                                },
                                "wrapper_template": {
                                    "type": "string",
                                    "description": "包装器模板路径"
                                },
                                "wrapper_output_dir": {
                                    "type": "string",
                                    "description": "包装器输出目录",
                                    "default": "src/hdl/wrapper"
                                },
                                "wrapper_parameters": {
                                    "type": "object",
                                    "description": "包装器参数映射"
                                }
                            }
                        }
                    }
                },
                "dependencies": {
                    "type": "object",
                    "properties": {
                        "git_submodules": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "url": {"type": "string"},
                                    "branch": {"type": "string"}
                                },
                                "required": ["path", "url"]
                            }
                        },
                        "python_packages": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "build": {
                    "type": "object",
                    "properties": {
                        "synthesis": {
                            "type": "object",
                            "properties": {
                                "strategy": {"type": "string"},
                                "options": {"type": "object"}
                            }
                        },
                        "implementation": {
                            "type": "object",
                            "properties": {
                                "options": {"type": "object"}
                            }
                        },
                        "bitstream": {
                            "type": "object",
                            "properties": {
                                "options": {"type": "object"}
                            }
                        },
                        "hooks": {
                            "type": "object",
                            "properties": {
                                "pre_build": {
                                    "oneOf": [
                                        {"type": "string", "description": "构建前脚本路径或命令"},
                                        {"type": "array", "items": {"type": "string"}, "description": "构建前命令列表"}
                                    ],
                                    "description": "构建前脚本路径或命令（可多行）"
                                },
                                "pre_synth": {
                                    "oneOf": [
                                        {"type": "string", "description": "综合前脚本路径或命令"},
                                        {"type": "array", "items": {"type": "string"}, "description": "综合前命令列表"}
                                    ],
                                    "description": "综合前脚本路径或命令（可多行）"
                                },
                                "post_synth": {
                                    "oneOf": [
                                        {"type": "string", "description": "综合后脚本路径或命令"},
                                        {"type": "array", "items": {"type": "string"}, "description": "综合后命令列表"}
                                    ],
                                    "description": "综合后脚本路径或命令（可多行）"
                                },
                                "pre_impl": {
                                    "oneOf": [
                                        {"type": "string", "description": "实现前脚本路径或命令"},
                                        {"type": "array", "items": {"type": "string"}, "description": "实现前命令列表"}
                                    ],
                                    "description": "实现前脚本路径或命令（可多行）"
                                },
                                "post_impl": {
                                    "oneOf": [
                                        {"type": "string", "description": "实现后脚本路径或命令"},
                                        {"type": "array", "items": {"type": "string"}, "description": "实现后命令列表"}
                                    ],
                                    "description": "实现后脚本路径或命令（可多行）"
                                },
                                "post_bitstream": {
                                    "oneOf": [
                                        {"type": "string", "description": "比特流生成后脚本路径或命令"},
                                        {"type": "array", "items": {"type": "string"}, "description": "比特流生成后命令列表"}
                                    ],
                                    "description": "比特流生成后脚本路径或命令（可多行）"
                                },
                                "bin_merge_script": {
                                    "type": "string",
                                    "description": "二进制合并脚本路径"
                                },
                                "custom_scripts": {
                                    "type": "object",
                                    "description": "自定义脚本映射"
                                }
                            }
                        }
                    }
                },
                "documentation": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "format": {"type": "string"},
                        "output_dir": {"type": "string"},
                        "include_doxygen": {"type": "boolean"}
                    }
                }
            },
            "required": ["project", "fpga"]
        }

    def load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = Path(config_path)
        self.config_path = config_path

        if not config_path.exists():
            raise ConfigError(f"配置文件不存在: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix in ['.yaml', '.yml']:
                    self.config_data = yaml.safe_load(f)
                elif config_path.suffix == '.json':
                    self.config_data = json.load(f)
                else:
                    raise ConfigError(f"不支持的配置文件格式: {config_path.suffix}")

            # 验证配置
            self.validate_config()

            return self.config_data

        except yaml.YAMLError as e:
            raise ConfigError(f"YAML解析错误: {e}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"JSON解析错误: {e}")
        except Exception as e:
            raise ConfigError(f"加载配置文件失败: {e}")

    def save_config(self, config_data: Dict[str, Any],
                   config_path: Optional[Union[str, Path]] = None) -> None:
        """保存配置文件"""
        if config_path is None:
            if self.config_path is None:
                raise ConfigError("未指定配置文件路径")
            config_path = self.config_path
        else:
            config_path = Path(config_path)

        # 验证配置
        try:
            jsonschema.validate(config_data, self.config_schema)
        except jsonschema.ValidationError as e:
            raise ConfigValidationError(f"配置验证失败: {e}")

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix in ['.yaml', '.yml']:
                    yaml.dump(config_data, f, default_flow_style=False,
                             allow_unicode=True, sort_keys=False)
                elif config_path.suffix == '.json':
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    # 默认使用YAML格式
                    yaml.dump(config_data, f, default_flow_style=False,
                             allow_unicode=True, sort_keys=False)

            self.config_data = config_data
            self.config_path = config_path

        except Exception as e:
            raise ConfigError(f"保存配置文件失败: {e}")

    def validate_config(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """验证配置"""
        if config_data is None:
            config_data = self.config_data

        try:
            jsonschema.validate(config_data, self.config_schema)
            return True
        except jsonschema.ValidationError as e:
            raise ConfigValidationError(f"配置验证失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        data = self.config_data

        for i, k in enumerate(keys[:-1]):
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def merge(self, other_config: Dict[str, Any], overwrite: bool = True) -> None:
        """合并配置"""
        def merge_dicts(dict1, dict2, overwrite_flag):
            for key, value in dict2.items():
                if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                    merge_dicts(dict1[key], value, overwrite_flag)
                elif overwrite_flag or key not in dict1:
                    dict1[key] = value

        merge_dicts(self.config_data, other_config, overwrite)

    def create_default_config(self, project_name: str, vendor: str,
                             part: str, template: str = 'basic') -> Dict[str, Any]:
        """创建默认配置"""
        default_config = {
            'project': {
                'name': project_name,
                'version': '1.0.0',
                'description': f'{project_name} FPGA工程',
                'author': 'YiHok',
                'license': 'Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International'
            },
            'fpga': {
                'vendor': vendor,
                'part': part,
                'top_module': f'{project_name}_top'
            },
            'source': {
                'hdl': [],
                'constraints': [],
                'ip_cores': [],
                'ip_repo_paths': ['ip_repo']
            },
            'dependencies': {
                'git_submodules': []
            },
            'build': {
                'synthesis': {
                    'strategy': 'out_of_context',
                    'options': {}
                },
                'implementation': {
                    'options': {}
                }
            },
            'documentation': {
                'enabled': True,
                'format': 'mkdocs',
                'output_dir': 'docs',
                'include_doxygen': False
            }
        }

        # 根据模板添加特定配置
        if template == 'zynq':
            default_config['fpga']['family'] = 'zynq-7000'
            default_config['source']['hdl'].append({
                'path': 'src/hdl/**/*.v',
                'language': 'verilog'
            })
            default_config['source']['constraints'].append({
                'path': 'src/constraints/*.xdc'
            })
        elif template == 'versal':
            default_config['fpga']['family'] = 'versal'
            default_config['source']['hdl'].append({
                'path': 'src/hdl/**/*.v',
                'language': 'verilog'
            })
            default_config['source']['constraints'].append({
                'path': 'src/constraints/*.xdc'
            })

        return default_config

    def find_config_file(self, start_path: Union[str, Path]) -> Optional[Path]:
        """查找配置文件"""
        start_path = Path(start_path)

        # 在当前目录及父目录中查找配置文件
        for path in [start_path, *start_path.parents]:
            for config_name in ['fpga_project.yaml', 'fpga_project.yml',
                               'fpga_project.json', '.fpga_project.yaml']:
                config_file = path / config_name
                if config_file.exists():
                    return config_file

        return None

    def reload(self) -> None:
        """重新加载配置"""
        if self.config_path:
            self.load_config(self.config_path)


class ProjectConfig(BaseModel):
    """项目配置模型（使用Pydantic）"""

    class Config:
        extra = 'forbid'  # 禁止额外字段

    name: str
    version: str
    description: Optional[str] = ""
    author: Optional[str] = "YiHok"
    license: Optional[str] = "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International"


class FPGAConfig(BaseModel):
    """FPGA配置模型"""

    vendor: str
    part: str
    family: Optional[str] = ""
    board: Optional[str] = ""
    top_module: Optional[str] = ""


class SourceFileConfig(BaseModel):
    """源文件配置模型"""

    path: str
    language: Optional[str] = "verilog"
    include_dirs: Optional[list] = []


class BuildConfig(BaseModel):
    """构建配置模型"""

    synthesis: Optional[dict] = {}
    implementation: Optional[dict] = {}
    bitstream: Optional[dict] = {}