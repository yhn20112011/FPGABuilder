# FPGABuilder 开发指南

## 概述

FPGABuilder是一个跨平台的FPGA自动构建工具链，旨在标准化和自动化FPGA开发流程。本开发指南旨在帮助开发者理解项目架构、设计思想，并指导如何手动介入开发工作。

### 核心设计理念

1. **配置驱动开发**：项目通过YAML配置文件定义，实现开发流程与具体工具链的解耦
2. **插件化架构**：所有功能通过插件实现，支持轻松扩展和定制
3. **统一接口**：为不同FPGA厂商提供一致的开发体验
4. **自动化与可重复性**：确保构建过程的一致性和可重复性

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    FPGABuilder CLI                          │
├─────────────────────────────────────────────────────────────┤
│                   核心框架 (Core Framework)                 │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │ 配置管理  │ │ 项目管理  │ │ 插件管理  │ │ CLI引擎  │  │
│  │ ConfigMgr │ │ ProjectMgr│ │ PluginMgr │ │           │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   插件系统 (Plugin System)                  │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │ Vivado    │ │ Quartus   │ │ HLS       │ │ 文档生成  │  │
│  │ 插件      │ │ 插件      │ │ 插件      │ │ 插件      │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    FPGA开发项目                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 fpga_project.yaml                    │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 源代码目录   约束文件    IP核    第三方库            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块说明

#### 1. 配置管理模块 (ConfigManager)
- **位置**: `src/core/config.py`
- **职责**: 加载、验证、保存项目配置
- **特性**:
  - 支持YAML和JSON格式
  - 使用JSON Schema进行配置验证
  - 提供配置模板生成功能
  - 支持配置合并和继承

#### 2. 项目管理模块 (ProjectManager)
- **位置**: `src/core/project.py`
- **职责**: 管理FPGA项目的生命周期
- **功能**:
  - 项目创建和初始化
  - 目录结构管理
  - Git子模块管理
  - 项目模板生成

#### 3. 插件管理模块 (PluginManager)
- **位置**: `src/core/plugin_manager.py`
- **职责**: 插件发现、注册和生命周期管理
- **功能**:
  - 动态加载插件
  - 插件依赖解析
  - 插件配置管理
  - 插件执行调度

#### 4. CLI引擎
- **位置**: `src/core/cli.py`
- **职责**: 提供命令行接口
- **特性**:
  - 基于Click框架
  - 支持丰富的命令和选项
  - 提供交互式配置界面

### 插件系统架构

#### 插件类型

FPGABuilder支持以下插件类型：

| 插件类型 | 描述 | 示例 |
|---------|------|------|
| `VENDOR` | FPGA厂商插件 | Vivado, Quartus插件 |
| `IP_CORE` | IP核插件 | AXI接口IP核生成器 |
| `HLS` | HLS插件 | Vitis HLS, Intel HLS |
| `DOCUMENTATION` | 文档插件 | MkDocs, Doxygen生成器 |
| `DEPLOYMENT` | 部署插件 | JTAG烧录, 远程部署 |
| `TOOL` | 工具插件 | 代码格式化, 静态分析 |

#### 插件基类层次结构

```
BasePlugin (抽象基类)
├── FPGAVendorPlugin (FPGA厂商插件基类)
├── IPCorePlugin (IP核插件基类)
├── HLSPlugin (HLS插件基类)
├── DocumentationPlugin (文档插件基类)
├── DeploymentPlugin (部署插件基类)
└── ToolPlugin (工具插件基类)
```

## 工具链与开发项目解耦设计

### 解耦机制

FPGABuilder通过以下机制实现工具链与开发项目的解耦：

#### 1. 配置与实现分离

```yaml
# fpga_project.yaml - 项目配置（与工具链无关）
project:
  name: "my_project"
  version: "1.0.0"

fpga:
  vendor: "xilinx"     # 指定厂商，不指定具体工具
  part: "xc7z045ffg676-2"

source:
  hdl:
    - path: "src/hdl/**/*.v"
      language: "verilog"
```

项目配置只描述"做什么"，不描述"怎么做"。具体实现由插件负责。

#### 2. 插件抽象层

每个FPGA厂商的工具链通过插件封装：

```python
class VivadoPlugin(FPGAVendorPlugin):
    """Vivado工具链插件"""

    @property
    def vendor(self) -> str:
        return "xilinx"

    def synthesize(self, config: Dict[str, Any]) -> BuildResult:
        # 具体的Vivado综合实现
        pass
```

#### 3. 动态插件发现

工具链在运行时动态发现和加载插件：

```python
# 插件管理器自动发现可用插件
plugin_manager = PluginManager()
plugin_manager.discover_plugins()

# 根据配置选择合适的插件
vendor = config.get('fpga.vendor')
plugin = plugin_manager.get_vendor_plugin(vendor)
```

#### 4. 统一构建接口

所有插件实现相同的接口：

```python
# 统一的构建流程接口
result = plugin.synthesize(config)
result = plugin.implement(config)
result = plugin.generate_bitstream(config)
```

### 解耦带来的优势

1. **可移植性**: 同一项目可在不同厂商工具链间切换
2. **可维护性**: 工具链更新不影响项目配置
3. **可扩展性**: 新增厂商只需实现插件接口
4. **可测试性**: 插件可独立测试，不依赖具体项目

## 手动介入开发工作流程

### 1. 环境准备

```bash
# 克隆代码库
git clone <repository_url>
cd FPGABuilder

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

### 2. 项目结构探索

```bash
# 查看核心模块
ls src/core/

# 查看插件目录
ls src/plugins/

# 查看现有项目示例
ls backup_existing_project/
```

### 3. 理解配置系统

#### 配置验证

```python
from src.core.config import ConfigManager

# 创建配置管理器
config_mgr = ConfigManager()

# 验证配置文件
config_mgr.load_config("fpga_project.yaml")

# 获取配置值
vendor = config_mgr.get("fpga.vendor")
part = config_mgr.get("fpga.part")
```

#### 配置扩展

```python
# 添加自定义配置字段
config_mgr.set("custom.build_options.optimization_level", 3)

# 保存配置
config_mgr.save_config()
```

### 4. 插件开发

#### 创建新插件

```python
from src.core.plugin_base import FPGAVendorPlugin, register_plugin, PluginType
from src.core.plugin_base import plugin_info

@plugin_info(name="my_vendor", plugin_type=PluginType.VENDOR, version="1.0.0")
@register_plugin
class MyVendorPlugin(FPGAVendorPlugin):
    """自定义FPGA厂商插件"""

    @property
    def name(self) -> str:
        return "my_vendor"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.VENDOR

    @property
    def vendor(self) -> str:
        return "my_vendor"

    def synthesize(self, config: Dict[str, Any]) -> BuildResult:
        # 实现综合逻辑
        pass

    # 实现其他抽象方法...
```

#### 插件注册

在 `src/plugins/` 目录下创建插件目录结构：

```
src/plugins/my_vendor/
├── __init__.py      # 插件入口点
├── plugin.py        # 插件实现
└── config_schema.py # 插件配置模式
```

### 5. 调试与测试

#### 单元测试

```python
# tests/test_my_plugin.py
import pytest
from src.plugins.my_vendor.plugin import MyVendorPlugin

def test_plugin_initialization():
    plugin = MyVendorPlugin()
    assert plugin.name == "my_vendor"
    assert plugin.vendor == "my_vendor"
```

#### 集成测试

```python
# tests/integration/test_build_flow.py
def test_complete_build_flow():
    # 加载配置
    config = load_test_config()

    # 创建插件实例
    plugin = MyVendorPlugin()
    plugin.initialize()

    # 执行构建流程
    synth_result = plugin.synthesize(config)
    assert synth_result.success

    # 验证输出
    assert "bitstream.bit" in synth_result.artifacts
```

### 6. 构建流程定制

#### 自定义构建步骤

```python
# 扩展构建流程
class CustomBuildPlugin(ToolPlugin):
    """自定义构建插件"""

    def execute(self, config: Dict[str, Any]) -> BuildResult:
        # 前置处理
        self.pre_process(config)

        # 调用标准构建流程
        vendor_plugin = get_vendor_plugin(config)
        result = vendor_plugin.synthesize(config)

        # 后置处理
        if result.success:
            self.post_process(config, result)

        return result
```

## 扩展开发指南

### 1. 添加新FPGA厂商支持

1. **创建插件目录**
   ```
   src/plugins/new_vendor/
   ```

2. **实现插件基类**
   ```python
   class NewVendorPlugin(FPGAVendorPlugin):
       # 实现所有抽象方法
       pass
   ```

3. **添加配置支持**
   - 在 `config.py` 的 `_get_default_schema()` 中添加厂商枚举
   - 更新配置验证规则

4. **提供工具链集成**
   - 实现厂商特定的TCL脚本生成
   - 集成厂商命令行工具

### 2. 添加新构建功能

1. **确定插件类型**
   - 选择适当的插件基类（ToolPlugin, DocumentationPlugin等）

2. **实现功能逻辑**
   - 遵循统一的接口规范
   - 提供详细的错误处理

3. **集成到构建流程**
   - 在 `cli.py` 中添加命令
   - 在构建流程中调用插件

### 3. 定制项目模板

1. **创建模板目录**
   ```
   src/templates/custom_template/
   ```

2. **定义模板文件**
   - 包含标准目录结构
   - 提供示例配置文件

3. **注册模板**
   - 在 `ProjectManager` 中添加模板支持
   - 更新 `create_default_config()` 方法

## 调试技巧

### 1. 插件调试

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 手动加载和测试插件
from src.core.plugin_manager import PluginManager
pm = PluginManager()
pm.discover_plugins()

# 测试特定插件
plugin = pm.get_plugin("vivado")
if plugin:
    plugin.initialize()
    # 执行测试...
```

### 2. 配置调试

```python
# 验证配置模式
from jsonschema import validate
try:
    validate(config_data, config_schema)
    print("配置验证通过")
except Exception as e:
    print(f"配置错误: {e}")
```

### 3. 构建流程调试

```python
# 逐步执行构建流程
def debug_build_flow(config):
    print("1. 加载配置...")
    print(f"   厂商: {config.get('fpga.vendor')}")
    print(f"   器件: {config.get('fpga.part')}")

    print("2. 初始化插件...")
    plugin = get_vendor_plugin(config)
    plugin.initialize()

    print("3. 执行综合...")
    synth_result = plugin.synthesize(config)
    print(f"   结果: {synth_result.success}")

    # 继续其他步骤...
```

## 最佳实践

### 1. 插件开发

- **保持插件轻量**: 每个插件只负责单一功能
- **遵循接口规范**: 严格实现基类定义的所有抽象方法
- **提供详细日志**: 便于问题诊断
- **包含单元测试**: 确保插件可靠性

### 2. 配置管理

- **使用配置验证**: 确保配置文件的正确性
- **提供默认值**: 减少用户配置负担
- **支持配置继承**: 便于创建配置模板
- **文档化配置选项**: 提供清晰的配置说明

### 3. 错误处理

- **优雅降级**: 当插件不可用时提供替代方案
- **详细错误信息**: 帮助用户快速定位问题
- **错误恢复**: 支持从失败点继续执行

### 4. 性能优化

- **缓存中间结果**: 减少重复计算
- **并行执行**: 利用多核CPU加速构建
- **增量构建**: 只重新构建发生变化的部分

## 故障排除

### 常见问题

1. **插件加载失败**
   - 检查插件目录结构
   - 验证插件类继承关系
   - 确认插件注册装饰器

2. **配置验证错误**
   - 检查配置模式定义
   - 验证配置数据类型
   - 查看JSON Schema文档

3. **构建过程失败**
   - 检查工具链安装
   - 验证环境变量设置
   - 查看构建日志

### 调试工具

```bash
# 启用调试模式
FPGABuilder --verbose build

# 生成详细日志
FPGABuilder build --log-level DEBUG

# 保存构建报告
FPGABuilder build --report-file build_report.json
```

## 贡献指南

### 1. 代码规范

- 遵循PEP 8编码规范
- 使用类型提示
- 添加文档字符串
- 编写单元测试

### 2. 提交流程

1. **创建功能分支**
   ```bash
   git checkout -b feature/new-plugin
   ```

2. **开发与测试**
   ```bash
   # 运行测试
   pytest tests/

   # 类型检查
   mypy src/

   # 代码格式检查
   black src/ tests/
   ```

3. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add new vendor plugin"
   git push origin feature/new-plugin
   ```

### 3. 文档更新

- 更新相关文档
- 提供使用示例
- 更新CHANGELOG.md

## 下一步

1. **探索现有代码**: 仔细阅读核心模块实现
2. **运行示例项目**: 理解实际工作流程
3. **修改和测试**: 尝试添加小功能
4. **贡献代码**: 提交改进和修复

通过本指南，您应该能够理解FPGABuilder的架构设计，掌握手动介入开发工作的方法，并充分利用工具链与开发项目解耦的优势进行定制开发。