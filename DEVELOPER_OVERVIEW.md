# FPGABuilder 开发概述

## 核心设计思想

### 1. 工具链解耦

**问题**：传统FPGA开发将项目与特定工具链（Vivado/Quartus）紧密耦合，导致：
- 项目难以在不同厂商间迁移
- 工具链升级影响项目稳定性
- 构建流程不可重复

**解决方案**：配置驱动 + 插件化架构
```
项目配置 → 插件管理器 → 厂商插件 → 具体工具链
    ↑                     ↑
  描述"做什么"         实现"怎么做"
```

### 2. 架构优势

- **可移植性**：同一YAML配置可适配不同厂商工具链
- **可维护性**：工具链更新只需修改插件，不影响项目配置
- **可扩展性**：新增厂商只需实现标准插件接口
- **可测试性**：插件可独立单元测试

## 快速理解代码结构

### 核心模块（src/core/）

```
src/core/
├── __init__.py          # 模块导出
├── config.py            # 配置管理 - 加载/验证/保存YAML配置
├── project.py           # 项目管理 - 项目生命周期管理
├── plugin_base.py       # 插件基类 - 定义插件接口和类型
├── plugin_manager.py    # 插件管理 - 插件发现/注册/调度
└── cli.py               # 命令行接口 - 基于Click的命令处理
```

### 插件系统（src/plugins/）

```
src/plugins/
├── vivado/              # Xilinx Vivado插件
├── quartus/             # Intel Quartus插件
├── hls/                 # HLS工具插件
└── documentation/       # 文档生成插件
```

## 如何手动介入开发

### 1. 修改配置系统

```python
# 添加新的配置选项
# 文件：src/core/config.py

# 在 _get_default_schema() 中添加新字段
schema["properties"]["build"]["properties"]["custom_option"] = {
    "type": "object",
    "properties": {
        "optimization_level": {"type": "integer"},
        "enable_feature": {"type": "boolean"}
    }
}

# 在 create_default_config() 中添加默认值
default_config["build"]["custom_option"] = {
    "optimization_level": 2,
    "enable_feature": True
}
```

### 2. 创建新插件

```python
# 文件：src/plugins/my_plugin/__init__.py

from src.core.plugin_base import ToolPlugin, register_plugin

@register_plugin
class MyCustomPlugin(ToolPlugin):
    @property
    def name(self):
        return "my_custom_plugin"

    def execute(self, config):
        # 实现自定义功能
        return BuildResult(success=True)
```

### 3. 扩展构建流程

```python
# 在现有构建流程中添加自定义步骤

# 1. 创建预处理插件
class PreprocessorPlugin(ToolPlugin):
    def execute(self, config):
        # 在综合前执行自定义处理
        pass

# 2. 创建后处理插件
class PostprocessorPlugin(ToolPlugin):
    def execute(self, config, build_result):
        # 在构建后执行自定义处理
        pass
```

## 关键设计模式

### 1. 策略模式（插件选择）

```python
# 根据配置动态选择插件
def get_vendor_plugin(vendor):
    plugins = {
        "xilinx": VivadoPlugin,
        "altera": QuartusPlugin,
        "lattice": LatticePlugin
    }
    return plugins.get(vendor)()
```

### 2. 模板方法模式（构建流程）

```python
# 定义构建算法骨架
class BuildPipeline:
    def build(self, config):
        self.pre_process(config)
        self.execute_build(config)
        self.post_process(config)

    # 子类可重写这些步骤
    def pre_process(self, config):
        pass

    def execute_build(self, config):
        pass

    def post_process(self, config):
        pass
```

### 3. 观察者模式（事件通知）

```python
# 构建事件通知系统
class BuildEventNotifier:
    def __init__(self):
        self.listeners = []

    def add_listener(self, listener):
        self.listeners.append(listener)

    def notify(self, event, data):
        for listener in self.listeners:
            listener.on_event(event, data)
```

## 调试和测试

### 1. 插件调试

```python
# 手动测试插件
from src.core.plugin_manager import PluginManager

pm = PluginManager()
pm.discover_plugins()

# 测试特定插件
plugin = pm.get_plugin("vivado")
if plugin:
    plugin.initialize()

    # 测试配置验证
    config = {"fpga": {"vendor": "xilinx", "part": "xc7z045ffg676-2"}}
    valid, errors = plugin.validate_config(config)
    print(f"配置验证: {valid}, 错误: {errors}")
```

### 2. 配置调试

```python
# 验证配置文件和模式
from src.core.config import ConfigManager

config_mgr = ConfigManager()

try:
    config = config_mgr.load_config("test_config.yaml")
    print("✅ 配置验证通过")

    # 检查关键字段
    required_fields = ["project.name", "fpga.vendor", "fpga.part"]
    for field in required_fields:
        value = config_mgr.get(field)
        print(f"  {field}: {value}")

except Exception as e:
    print(f"❌ 配置错误: {e}")
```

### 3. 构建流程调试

```bash
# 使用详细输出模式
FPGABuilder --verbose build

# 逐步执行构建步骤
FPGABuilder synth --dry-run
FPGABuilder impl --dry-run
FPGABuilder bitstream --dry-run
```

## 实用代码片段

### 1. 快速创建插件模板

```python
#!/usr/bin/env python3
"""
插件模板生成器
用法：python create_plugin_template.py MyPlugin
"""

import sys
import os

template = '''from src.core.plugin_base import {base_class}, register_plugin

@register_plugin
class {plugin_name}({base_class}):
    """{plugin_name}插件"""

    @property
    def name(self) -> str:
        return "{plugin_name_lower}"

    @property
    def plugin_type(self):
        return PluginType.{plugin_type}

    def execute(self, config):
        """执行插件功能"""
        # TODO: 实现插件逻辑
        return BuildResult(success=True)

    def initialize(self) -> bool:
        """初始化插件"""
        return True

    def cleanup(self) -> bool:
        """清理插件"""
        return True
'''

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python create_plugin_template.py <插件名>")
        sys.exit(1)

    plugin_name = sys.argv[1]
    plugin_name_lower = plugin_name.lower()

    print("选择插件类型:")
    print("1. VENDOR - FPGA厂商插件")
    print("2. TOOL - 工具插件")
    print("3. DOCUMENTATION - 文档插件")
    print("4. DEPLOYMENT - 部署插件")

    choice = input("输入选择 (1-4): ")

    type_map = {
        "1": ("FPGAVendorPlugin", "VENDOR"),
        "2": ("ToolPlugin", "TOOL"),
        "3": ("DocumentationPlugin", "DOCUMENTATION"),
        "4": ("DeploymentPlugin", "DEPLOYMENT")
    }

    if choice in type_map:
        base_class, plugin_type = type_map[choice]

        # 创建插件目录
        plugin_dir = f"src/plugins/{plugin_name_lower}"
        os.makedirs(plugin_dir, exist_ok=True)

        # 生成插件文件
        plugin_content = template.format(
            plugin_name=plugin_name,
            plugin_name_lower=plugin_name_lower,
            base_class=base_class,
            plugin_type=plugin_type
        )

        plugin_file = os.path.join(plugin_dir, "plugin.py")
        with open(plugin_file, "w", encoding="utf-8") as f:
            f.write(plugin_content)

        # 创建 __init__.py
        init_content = f'''"""
{plugin_name}插件包
"""

from .plugin import {plugin_name}

__all__ = ["{plugin_name}"]
'''

        init_file = os.path.join(plugin_dir, "__init__.py")
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(init_content)

        print(f"✅ 插件模板已创建: {plugin_dir}")
    else:
        print("❌ 无效选择")
```

### 2. 配置验证脚本

```python
#!/usr/bin/env python3
"""
配置验证脚本
用法：python validate_config.py <配置文件>
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import ConfigManager

def main(config_file):
    config_mgr = ConfigManager()

    try:
        config = config_mgr.load_config(config_file)
        print("✅ 配置验证通过")

        # 显示关键信息
        print("\n配置摘要:")
        print(f"  项目名称: {config_mgr.get('project.name')}")
        print(f"  项目版本: {config_mgr.get('project.version')}")
        print(f"  FPGA厂商: {config_mgr.get('fpga.vendor')}")
        print(f"  器件型号: {config_mgr.get('fpga.part')}")

        # 检查插件可用性
        vendor = config_mgr.get('fpga.vendor')
        if vendor:
            from src.core.plugin_manager import PluginManager
            pm = PluginManager()
            pm.discover_plugins()

            if pm.get_vendor_plugin(vendor):
                print(f"✅ 找到 {vendor} 插件支持")
            else:
                print(f"⚠️  未找到 {vendor} 插件支持")

        return 0

    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python validate_config.py <配置文件>")
        sys.exit(1)

    sys.exit(main(sys.argv[1]))
```

## 下一步行动

### 1. 探索现有代码
- 阅读 `src/core/config.py` 理解配置管理
- 查看 `src/core/plugin_base.py` 理解插件接口
- 分析 `src/plugins/vivado/` 学习插件实现

### 2. 运行示例
```bash
# 创建测试项目
FPGABuilder init test_project --vendor xilinx --part xc7z045ffg676-2

# 探索生成的文件结构
cd test_project
ls -la
cat fpga_project.yaml
```

### 3. 尝试修改
- 添加一个新的配置选项
- 创建一个简单的工具插件
- 修改构建流程顺序

### 4. 运行测试
```bash
# 运行现有测试
pytest tests/

# 为新功能添加测试
# 验证修改没有破坏现有功能
```

## 获取帮助

- 查看开发文档：`docs/developer_guide/`
- 阅读源代码注释
- 运行 `FPGABuilder --help` 查看命令帮助
- 参考现有插件实现作为示例

## 设计原则回顾

1. **配置与实现分离**：项目配置描述"做什么"，插件实现"怎么做"
2. **面向接口编程**：所有功能通过抽象接口访问
3. **开闭原则**：通过扩展（插件）而非修改来添加新功能
4. **依赖倒置**：高层模块不依赖低层模块，两者都依赖抽象

遵循这些原则，您就能有效地扩展和定制FPGABuilder。