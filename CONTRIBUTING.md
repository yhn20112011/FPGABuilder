# 贡献指南

感谢您对FPGABuilder项目的关注！我们欢迎各种形式的贡献，包括但不限于：

- 报告bug
- 提出新功能建议
- 改进文档
- 提交代码补丁
- 开发插件

## 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/FPGABuilder.git
cd FPGABuilder
```

### 2. 创建虚拟环境

```bash
# 使用venv
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装开发依赖

```bash
pip install -e ".[dev]"
```

## 开发流程

### 1. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/issue-number
```

### 2. 编写代码

请遵循项目的代码风格：
- 使用Black进行代码格式化
- 使用Flake8进行代码检查
- 使用mypy进行类型检查
- 添加适当的注释和文档字符串

### 3. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_module.py

# 运行测试并生成覆盖率报告
pytest --cov=src tests/
```

### 4. 更新文档

如果您的更改涉及用户界面或API，请更新相关文档：
- 更新README.md中的示例
- 更新用户指南（docs/user_guide/）
- 更新API文档（如有需要）

### 5. 提交更改

```bash
# 添加更改
git add .

# 提交更改
git commit -m "描述您的更改"

# 推送分支
git push origin feature/your-feature-name
```

### 6. 创建Pull Request

1. 在GitHub上创建Pull Request
2. 填写PR模板
3. 等待代码审查

## 代码规范

### Python代码风格

- 遵循PEP 8规范
- 使用4个空格缩进
- 行长不超过88个字符（Black默认）
- 使用英文注释和文档字符串

### 文档字符串

使用Google风格的文档字符串：

```python
def function_name(arg1, arg2):
    """函数简短描述。

    函数的详细描述。

    Args:
        arg1: 第一个参数描述
        arg2: 第二个参数描述

    Returns:
        返回值描述

    Raises:
        ValueError: 当参数无效时
    """
    pass
```

### 类型提示

尽可能使用类型提示：

```python
from typing import List, Optional, Dict

def process_data(data: List[str]) -> Optional[Dict[str, int]]:
    """处理数据。"""
    pass
```

## 插件开发

### 插件结构

```
src/plugins/vendor_name/
├── __init__.py          # 插件主文件
├── tcl_templates/       # TCL模板文件
├── config_schema.yaml   # 配置模式
└── README.md           # 插件文档
```

### 插件接口

插件必须实现以下基类：

```python
from fpga_builder.core.plugin_base import FPGAVendorPlugin

class MyVendorPlugin(FPGAVendorPlugin):
    @property
    def name(self) -> str:
        return "my_vendor"

    @property
    def vendor(self) -> str:
        return "my_vendor"

    def create_project(self, config: Dict) -> bool:
        # 实现创建工程逻辑
        pass

    # 实现其他必需方法
```

### 注册插件

在插件的`__init__.py`中注册插件：

```python
from .my_vendor_plugin import MyVendorPlugin

__all__ = ["MyVendorPlugin"]
```

## 测试

### 单元测试

- 每个模块都应有对应的测试文件
- 测试文件命名：`test_模块名.py`
- 测试类命名：`Test类名`
- 测试方法命名：`test_方法名_场景`

### 集成测试

集成测试位于`tests/integration/`目录，测试整个工作流程。

### 模拟外部依赖

使用pytest fixture模拟外部工具（如Vivado、Quartus）：

```python
import pytest

@pytest.fixture
def mock_vivado(mocker):
    return mocker.patch("fpga_builder.plugins.vivado.VivadoPlugin")
```

## 文档

### 用户文档

用户文档使用MkDocs编写，位于`docs/`目录：

```bash
# 本地预览文档
mkdocs serve

# 构建文档
mkdocs build
```

### API文档

使用mkdocstrings自动生成API文档：

```python
::: fpga_builder.core.plugin_base
    options:
      show_source: true
```

## 发布流程

### 版本号

遵循语义化版本控制（SemVer）：
- MAJOR：不兼容的API修改
- MINOR：向下兼容的功能性新增
- PATCH：向下兼容的问题修正

### 发布步骤

1. 更新`src/core/__init__.py`中的版本号
2. 更新CHANGELOG.md
3. 创建发布标签
4. 构建发布包
5. 发布到PyPI

## 行为准则

请遵守项目的[行为准则](CODE_OF_CONDUCT.md)，保持尊重和专业的态度。

## 获取帮助

- 查看[文档](https://yourusername.github.io/FPGABuilder/)
- 在[GitHub Discussions](https://github.com/yourusername/FPGABuilder/discussions)提问
- 查看现有[Issues](https://github.com/yourusername/FPGABuilder/issues)

感谢您的贡献！