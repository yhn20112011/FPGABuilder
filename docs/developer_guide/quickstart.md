# 快速入门：手动介入开发工作

本文档提供快速指南，帮助开发者理解如何手动介入FPGABuilder的开发工作，特别是工具链与开发项目的解耦设计。

## 核心概念理解

### 1. 工具链解耦是什么？

传统FPGA开发流程通常将项目与特定工具链（如Vivado、Quartus）紧密耦合：
```
传统方式：
项目文件 → Vivado TCL脚本 → Vivado工具链
```

FPGABuilder的解耦设计：
```
FPGABuilder方式：
项目配置 → 插件管理器 → 厂商插件 → 具体工具链
            ↑
        动态选择
```

### 2. 解耦带来的优势

- **灵活性**：同一项目可在不同厂商间切换
- **可维护性**：工具链更新不影响项目
- **可测试性**：插件可独立测试
- **可扩展性**：轻松添加新厂商支持

## 五分钟上手

### 步骤1：探索项目结构

```bash
# 查看核心架构
ls src/core/
# config.py      - 配置管理
# project.py     - 项目管理
# plugin_base.py - 插件基类
# plugin_manager.py - 插件管理
# cli.py         - 命令行接口

# 查看现有插件
ls src/plugins/
# vivado/    - Xilinx Vivado插件
# quartus/   - Intel Quartus插件
# hls/       - HLS工具插件
# documentation/ - 文档生成插件
```

### 步骤2：理解配置文件

创建一个简单的配置文件 `test_config.yaml`：

```yaml
project:
  name: "test_project"
  version: "1.0.0"

fpga:
  vendor: "xilinx"     # 关键：这里只指定厂商，不绑定具体工具
  part: "xc7z045ffg676-2"

source:
  hdl:
    - path: "src/hdl/test.v"
      language: "verilog"
```

### 步骤3：手动加载配置

```python
# test_config.py
from src.core.config import ConfigManager

# 创建配置管理器
config_mgr = ConfigManager()

# 加载配置
config = config_mgr.load_config("test_config.yaml")

# 获取厂商信息
vendor = config_mgr.get("fpga.vendor")  # 返回 "xilinx"
print(f"项目使用厂商: {vendor}")
```

### 步骤4：动态选择插件

```python
# test_plugin.py
from src.core.plugin_manager import PluginManager

# 创建插件管理器
pm = PluginManager()
pm.discover_plugins()

# 根据配置选择插件
vendor = "xilinx"
plugin = pm.get_vendor_plugin(vendor)

if plugin:
    print(f"找到插件: {plugin.name}")
    print(f"插件类型: {plugin.plugin_type}")
    print(f"支持器件: {plugin.supported_parts}")
```

## 实际开发场景

### 场景1：添加新的构建选项

假设您想在构建流程中添加自定义的预处理步骤：

```python
# 创建自定义工具插件
from src.core.plugin_base import ToolPlugin, register_plugin

@register_plugin
class CustomPreprocessor(ToolPlugin):
    @property
    def name(self):
        return "custom_preprocessor"

    def execute(self, config):
        # 从配置获取源文件
        source_files = config.get("source.hdl", [])

        # 执行自定义预处理
        for file_info in source_files:
            file_path = file_info["path"]
            self.preprocess_file(file_path)

        return BuildResult(success=True, artifacts={}, logs={})
```

### 场景2：扩展配置选项

```python
# 在配置管理器中添加新选项
def extend_config_schema():
    config_mgr = ConfigManager()

    # 获取现有模式
    schema = config_mgr.config_schema

    # 添加自定义构建选项
    schema["properties"]["build"]["properties"]["custom_options"] = {
        "type": "object",
        "properties": {
            "optimization_level": {"type": "integer", "minimum": 0, "maximum": 3},
            "enable_debug": {"type": "boolean"},
            "custom_flags": {"type": "array", "items": {"type": "string"}}
        }
    }

    return schema
```

### 场景3：创建项目模板

```python
# 创建自定义项目模板
def create_custom_template(project_name, vendor, part):
    config_mgr = ConfigManager()

    # 基础配置
    config = config_mgr.create_default_config(project_name, vendor, part)

    # 添加自定义设置
    config["build"]["custom_options"] = {
        "optimization_level": 2,
        "enable_debug": True
    }

    # 添加预定义源文件结构
    config["source"]["hdl"] = [
        {"path": "src/hdl/top.v", "language": "verilog"},
        {"path": "src/hdl/utils/*.v", "language": "verilog"}
    ]

    return config
```

## 调试技巧

### 1. 查看插件加载过程

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.core.plugin_manager import PluginManager
pm = PluginManager()

# 查看发现的插件
print("发现插件:")
for plugin_info in pm.get_all_plugins():
    print(f"  - {plugin_info['name']} ({plugin_info['type']})")
```

### 2. 测试构建流程

```python
def test_build_flow_step_by_step():
    # 1. 加载配置
    config = load_config()

    # 2. 选择插件
    vendor = config["fpga"]["vendor"]
    plugin = get_plugin(vendor)

    # 3. 执行每个步骤
    steps = ["synthesize", "implement", "generate_bitstream"]

    for step in steps:
        print(f"执行步骤: {step}")
        method = getattr(plugin, step)
        result = method(config)

        if not result.success:
            print(f"步骤失败: {result.errors}")
            break
```

### 3. 验证配置

```python
def validate_config_interactive(config_path):
    config_mgr = ConfigManager()

    try:
        config = config_mgr.load_config(config_path)
        print("✅ 配置验证通过")

        # 显示关键信息
        print(f"项目名称: {config_mgr.get('project.name')}")
        print(f"FPGA厂商: {config_mgr.get('fpga.vendor')}")
        print(f"器件型号: {config_mgr.get('fpga.part')}")

        # 检查插件可用性
        vendor = config_mgr.get('fpga.vendor')
        pm = PluginManager()
        pm.discover_plugins()

        if pm.get_vendor_plugin(vendor):
            print(f"✅ 找到 {vendor} 插件")
        else:
            print(f"⚠️  未找到 {vendor} 插件")

    except Exception as e:
        print(f"❌ 配置错误: {e}")
```

## 常见任务

### 任务1：为现有项目添加FPGABuilder支持

1. **分析现有项目结构**
   ```bash
   # 查看现有构建脚本
   ls -la *.tcl *.mk Makefile

   # 识别关键配置
   # - FPGA器件型号
   # - 源文件列表
   # - 约束文件
   # - 构建选项
   ```

2. **创建配置文件**
   ```yaml
   # 将现有配置转换为YAML
   project:
     name: "existing_project"
     version: "1.0.0"

   fpga:
     vendor: "xilinx"
     part: "xc7z045ffg676-2"  # 从现有项目获取

   source:
     hdl:
       - path: "rtl/**/*.v"    # 现有源文件位置
         language: "verilog"
     constraints:
       - path: "constraints/*.xdc"
   ```

3. **创建转换脚本**
   ```python
   # convert_project.py
   def convert_vivado_project(vivado_dir):
       # 解析Vivado项目文件
       # 生成fpga_project.yaml
       # 转换TCL脚本为配置选项
       pass
   ```

### 任务2：创建自定义报告生成器

```python
class CustomReportPlugin(ToolPlugin):
    def execute(self, config):
        # 收集构建结果
        build_dir = config.get("build.output_dir", "build")

        # 分析报告文件
        reports = self.collect_reports(build_dir)

        # 生成自定义报告
        report_data = self.generate_report(reports)

        # 输出报告
        self.save_report(report_data, "custom_report.html")

        return BuildResult(
            success=True,
            artifacts={"report": "custom_report.html"},
            logs={"report_generation": "报告生成完成"}
        )
```

### 任务3：集成外部工具

```python
class ExternalToolPlugin(ToolPlugin):
    def execute(self, config):
        # 调用外部工具
        import subprocess

        tool_config = config.get("tools.external_tool", {})
        command = tool_config.get("command", "external_tool")
        args = tool_config.get("args", [])

        # 执行外部命令
        result = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True
        )

        # 处理结果
        if result.returncode == 0:
            return BuildResult(
                success=True,
                logs={"external_tool": result.stdout}
            )
        else:
            return BuildResult(
                success=False,
                errors=[f"外部工具失败: {result.stderr}"]
            )
```

## 下一步行动建议

1. **实验性修改**：在独立分支中尝试修改
2. **添加测试**：为新功能编写单元测试
3. **文档更新**：记录您的修改和添加的功能
4. **代码审查**：提交前进行自我代码审查

## 获取帮助

- 查看核心模块的源代码注释
- 运行现有测试了解预期行为
- 参考现有插件实现作为示例
- 使用调试模式运行命令：`FPGABuilder --verbose <command>`

记住FPGABuilder的核心设计原则：**配置与实现分离，插件化架构，统一接口**。遵循这些原则，您就能有效地扩展和定制工具链。