# FPGABuilder 文档索引

本文档提供FPGABuilder所有文档的索引和概述。

## 用户文档

### 入门指南
- [README.md](README.md) - 项目概述、安装和快速开始
- [用户指南](docs/user_guide/index.md) - 详细的使用说明和配置指南

### 命令行参考
- [命令行参考](README.md#命令行参考) - 所有命令和选项的详细说明
- [配置示例](README.md#配置文件示例) - 配置文件示例和说明

## 开发文档

### 架构设计
- [开发概述](DEVELOPER_OVERVIEW.md) - 核心设计思想和快速理解代码结构
- [开发指南总览](docs/developer_guide/index.md) - 完整的开发指南
- [架构设计详解](docs/developer_guide/architecture.md) - 深入理解系统架构
- [快速入门](docs/developer_guide/quickstart.md) - 快速上手手动开发

### 核心概念
- **工具链解耦**：项目配置与具体工具链实现分离
- **插件化架构**：通过插件扩展所有功能
- **配置驱动**：使用YAML配置文件定义项目

### 关键设计
1. **配置与实现分离**：项目配置描述"做什么"，插件实现"怎么做"
2. **统一接口设计**：所有插件实现相同的抽象接口
3. **动态插件发现**：运行时自动发现和加载插件
4. **构建流程抽象**：统一的构建流程接口

## 代码结构

### 核心模块
```
src/core/
├── config.py            # 配置管理 - 加载/验证/保存配置
├── project.py           # 项目管理 - 项目生命周期管理
├── plugin_base.py       # 插件基类 - 定义插件接口和类型
├── plugin_manager.py    # 插件管理 - 插件发现/注册/调度
└── cli.py               # 命令行接口 - 基于Click的命令处理
```

### 插件系统
```
src/plugins/
├── vivado/              # Xilinx Vivado插件
├── quartus/             # Intel Quartus插件
├── hls/                 # HLS工具插件
└── documentation/       # 文档生成插件
```

## 如何开始

### 作为用户
1. 阅读 [README.md](README.md) 了解基本概念
2. 查看 [用户指南](docs/user_guide/index.md) 学习详细用法
3. 尝试创建示例项目：`FPGABuilder init test_project --vendor xilinx`

### 作为开发者
1. 阅读 [开发概述](DEVELOPER_OVERVIEW.md) 理解核心设计
2. 查看 [快速入门](docs/developer_guide/quickstart.md) 学习手动开发
3. 探索 [架构设计](docs/developer_guide/architecture.md) 深入理解系统
4. 运行示例代码和测试

### 作为贡献者
1. 阅读 [贡献指南](CONTRIBUTING.md) 了解开发流程
2. 查看现有插件实现作为参考
3. 运行测试确保修改不破坏现有功能

## 工具链解耦设计

### 传统方式 vs FPGABuilder方式

**传统FPGA开发**：
```
项目文件 → 特定工具链脚本 → 厂商工具
```

**FPGABuilder方式**：
```
项目配置 → 插件管理器 → 厂商插件 → 具体工具链
```

### 解耦带来的优势

1. **可移植性**：同一项目可在不同厂商工具链间切换
   ```yaml
   # 只需修改这一行即可切换厂商
   fpga:
     vendor: "xilinx"  # 改为 "altera"、"lattice"等
   ```

2. **可维护性**：工具链更新只需修改插件，不影响项目配置

3. **可扩展性**：新增厂商只需实现标准插件接口
   ```python
   class NewVendorPlugin(FPGAVendorPlugin):
       # 实现标准接口即可
       pass
   ```

4. **可测试性**：插件可独立单元测试，不依赖具体项目

## 实用工具和脚本

### 配置验证脚本
```bash
# 验证配置文件
python scripts/validate_config.py fpga_project.yaml
```

### 插件调试工具
```python
# 交互式插件调试
from src.core.plugin_manager import PluginManager
pm = PluginManager()
pm.discover_plugins()

# 查看所有可用插件
for plugin_info in pm.get_all_plugins():
    print(f"{plugin_info['name']}: {plugin_info['type']}")
```

### 构建流程调试
```bash
# 详细输出模式
FPGABuilder --verbose build

# 逐步执行构建
FPGABuilder synth --dry-run
FPGABuilder impl --dry-run
```

## 常见任务指南

### 任务1：添加新配置选项
1. 修改 `src/core/config.py` 中的配置模式
2. 更新默认配置生成逻辑
3. 添加配置验证规则
4. 更新相关文档

### 任务2：创建新插件
1. 创建插件目录：`src/plugins/my_plugin/`
2. 实现插件基类接口
3. 注册插件到系统
4. 添加测试和文档

### 任务3：扩展构建流程
1. 创建新的工具插件
2. 在构建流程中注册插件
3. 配置插件执行顺序
4. 测试完整构建流程

### 任务4：集成外部工具
1. 创建工具插件封装外部工具
2. 配置工具参数和选项
3. 处理工具输出和错误
4. 集成到现有构建流程

## 学习路径

### 初学者
1. 📖 阅读 [README.md](README.md)
2. 🚀 尝试 [快速开始](README.md#快速开始)
3. ⚙️ 学习 [配置系统](docs/user_guide/index.md#配置文件详解)

### 中级用户
1. 🔌 了解 [插件系统](README.md#插件系统)
2. 🛠️ 学习 [命令行参考](README.md#命令行参考)
3. 📊 探索 [高级功能](docs/user_guide/index.md#高级功能)

### 开发者
1. 🏗️ 理解 [架构设计](docs/developer_guide/architecture.md)
2. 🔧 学习 [手动开发](docs/developer_guide/quickstart.md)
3. 🧪 查看 [代码结构](DEVELOPER_OVERVIEW.md#快速理解代码结构)

### 贡献者
1. 📝 阅读 [贡献指南](CONTRIBUTING.md)
2. 🔍 探索 [现有代码](src/core/)
3. 🧩 参考 [插件示例](src/plugins/vivado/)

## 获取帮助

- **文档问题**：查看相关文档页面
- **使用问题**：阅读用户指南和示例
- **开发问题**：参考开发指南和架构文档
- **代码问题**：查看源代码注释和测试

## 文档更新

本文档会随着项目发展而更新。如果您发现文档缺失或错误，欢迎：

1. 提交Issue报告问题
2. 提交Pull Request修复问题
3. 在讨论区提出建议

## 版本信息

- **文档版本**：1.0.0
- **最后更新**：2026-02-12
- **对应代码版本**：0.1.0

---

**记住**：FPGABuilder的核心价值在于**工具链与开发项目的解耦**。理解这一点是有效使用和扩展FPGABuilder的关键。