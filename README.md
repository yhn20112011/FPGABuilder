# FPGABuilder - FPGA自动构建工具链

FPGABuilder是一个跨平台的FPGA自动构建工具链，支持Windows环境，能够集成Xilinx、Altera等主流FPGA厂商的开发工具，提供工程创建、构建、综合、烧录等全流程自动化。

## 特性

- **多厂商支持**: 支持Xilinx Vivado、Intel Quartus等主流FPGA开发工具
- **自动化构建**: 一键完成从源代码到比特流的全流程构建
- **插件化架构**: 模块化设计，易于扩展新功能和新厂商支持
- **配置驱动**: 使用YAML配置文件定义工程，支持版本控制
- **文档集成**: 自动生成项目文档，支持MkDocs和Doxygen
- **交互式配置**: 提供类似Linux内核的menuconfig配置界面
- **项目管理**: 支持git子模块，自动管理第三方IP核和库
- **跨平台**: 优先支持Windows，设计考虑Linux/macOS兼容性

## 安装

### 快速安装（Windows）

1. 下载最新版本的FPGABuilder安装包
2. 运行安装程序，按照提示完成安装
3. 安装完成后，重启命令行终端
4. 验证安装：`FPGABuilder --version`

### 从源代码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/FPGABuilder.git
cd FPGABuilder

# 安装依赖
pip install -r requirements.txt

# 安装FPGABuilder
python setup.py install
```

## 构建与打包

FPGABuilder提供了完整的构建和打包工具，支持生成Wheel包、源代码分发包、独立可执行文件和Windows安装程序。

### 快速构建Wheel包

Wheel包是Python的标准分发格式，可以在不编译的情况下快速安装。

```bash
# 方法1：使用setup.py直接构建
python setup.py bdist_wheel

# 方法2：使用打包脚本（推荐）
python scripts/package.py --wheel

# 生成的Wheel文件位于 dist/ 目录
# 例如：dist/FPGABuilder-0.1.0-py3-none-any.whl
```

### 完整打包流程

使用打包脚本可以一次性生成所有分发格式：

```bash
# 清理所有构建文件
python scripts/package.py --clean

# 构建所有分发格式（sdist + wheel + exe + installer）
python scripts/package.py --all

# 或者分别构建
python scripts/package.py --sdist    # 源代码分发包
python scripts/package.py --wheel    # Wheel包
python scripts/package.py --exe      # 独立可执行文件
python scripts/package.py --installer  # Windows安装程序（仅Windows）
```

### 清理构建文件

构建过程中会产生临时文件，建议在提交代码前或重新构建前进行清理：

```bash
# 使用打包脚本清理
python scripts/package.py --clean

# 或者手动清理
rm -rf build/ dist/ *.egg-info/ __pycache__/
```

打包脚本的`clean()`方法会清理以下目录和文件：
- `build/` - 构建临时目录
- `dist/` - 分发文件目录
- `*.egg-info/` - Egg信息目录
- `__pycache__/` - Python缓存文件
- `.pytest_cache/` - 测试缓存
- `.mypy_cache/` - 类型检查缓存

### 打包脚本选项

```bash
python scripts/package.py --help

用法: package.py [-h] [--clean] [--sdist] [--wheel] [--exe] [--installer] [--all] [--output OUTPUT] [--version]

选项:
  -h, --help            显示帮助信息
  --clean               清理构建文件
  --sdist               构建源代码分发包
  --wheel               构建wheel包
  --exe                 构建独立可执行文件
  --installer           构建Windows安装程序
  --all                 打包所有格式
  --output OUTPUT, -o OUTPUT
                        输出目录 (默认: "dist")
  --version, -V         显示版本
```

### 构建环境要求

- **Python**: 3.8或更高版本
- **构建工具**: `pip install build` (用于`sdist`和`wheel`)
- **可选依赖**:
  - `pip install pyinstaller` (用于可执行文件)
  - Inno Setup (用于Windows安装程序)

### 开发构建工作流

1. **开发阶段**：
   ```bash
   # 安装开发依赖
   pip install -e .

   # 测试功能
   FPGABuilder --version
   ```

2. **构建测试**：
   ```bash
   # 清理并构建Wheel包
   python scripts/package.py --clean --wheel

   # 测试安装
   pip install dist/FPGABuilder-*.whl
   ```

3. **发布准备**：
   ```bash
   # 完整构建所有分发格式
   python scripts/package.py --clean --all

   # 验证包文件
   ls -la dist/
   ```

## 快速开始

### 创建新工程

```bash
# 初始化一个新的FPGA工程
FPGABuilder init my_project --vendor xilinx --part xc7z045ffg676-2
```

### 配置工程

```bash
# 进入工程目录
cd my_project

# 交互式配置
FPGABuilder config
```

### 构建工程

```bash
# 完整构建（综合+实现+生成比特流）
FPGABuilder build

# 仅综合
FPGABuilder synth

# 生成比特流
FPGABuilder bitstream
```

### 烧录设备

```bash
# 通过JTAG烧录
FPGABuilder program --cable xilinx_tcf --target hw_server:3121
```

## 工程结构

一个标准的FPGABuilder工程包含以下结构：

```
my_project/
├── fpga_project.yaml      # 工程配置文件
├── src/                   # 源代码目录
│   ├── hdl/              # HDL源代码
│   ├── constraints/      # 约束文件
│   └── ip/               # IP核文件
├── ip_repo/              # 第三方IP核仓库（git子模块）
├── lib/                  # 第三方库（git子模块）
├── docs/                 # 项目文档
├── build/                # 构建输出
│   ├── reports/          # 构建报告
│   ├── bitstreams/       # 比特流文件
│   └── logs/             # 构建日志
└── tests/                # 测试文件
```

## 配置文件示例

### fpga_project.yaml

```yaml
project:
  name: "my_fpga_project"
  version: "1.0.0"
  description: "示例FPGA工程"

fpga:
  vendor: "xilinx"
  family: "zynq-7000"
  part: "xc7z045ffg676-2"
  top_module: "system_wrapper"

source:
  hdl:
    - path: "src/hdl/**/*.v"
      language: "verilog"
    - path: "src/hdl/**/*.vhd"
      language: "vhdl"
  constraints:
    - path: "src/constraints/*.xdc"

dependencies:
  git_submodules:
    - path: "lib/common"
      url: "git@example.com:fpga/common.git"

build:
  synthesis:
    strategy: "out_of_context"
  implementation:
    opt_design: true
    place_design: true
    route_design: true
```

## 命令行参考

### 全局选项

```
FPGABuilder [全局选项] <命令> [命令选项]

全局选项:
  -c, --config FILE    指定配置文件
  -v, --verbose        详细输出
  --version            显示版本信息
  -h, --help           显示帮助信息
```

### 常用命令

| 命令 | 描述 |
|------|------|
| `init` | 初始化新工程 |
| `create` | 创建工程结构 |
| `config` | 配置工程（menuconfig界面） |
| `build` | 构建工程 |
| `synth` | 仅综合 |
| `impl` | 仅实现（布局布线） |
| `bitstream` | 生成比特流 |
| `program` | 烧录设备 |
| `ip` | 管理IP核 |
| `hls` | 管理HLS工程 |
| `docs` | 生成文档 |
| `clean` | 清理构建文件 |
| `pack` | 打包发布 |

### 示例

```bash
# 查看所有可用命令
FPGABuilder --help

# 查看具体命令帮助
FPGABuilder init --help

# 创建IP核
FPGABuilder ip create axi_uart --type axi4lite

# 生成文档
FPGABuilder docs --format mkdocs --output docs/

# 清理构建文件
FPGABuilder clean --all
```

## 插件系统

FPGABuilder支持插件扩展，可以添加：

1. **新FPGA厂商支持** - 添加新的FPGA工具链插件
2. **构建流程扩展** - 自定义构建步骤
3. **报告生成器** - 添加新的报告格式
4. **部署方式** - 支持新的烧录方式

### 开发插件

参考`src/plugins/vivado/`示例开发新插件。

## 文档

- [用户指南](docs/user_guide/) - 详细使用说明
- [开发者指南](docs/developer_guide/) - 插件开发和贡献指南
- [API参考](docs/api/) - 代码API文档

## 支持

- 问题反馈：[GitHub Issues](https://github.com/yourusername/FPGABuilder/issues)
- 功能请求：[GitHub Discussions](https://github.com/yourusername/FPGABuilder/discussions)
- 文档：[在线文档](https://yourusername.github.io/FPGABuilder/)

## 许可证

本项目采用MIT许可证。详见[LICENSE](LICENSE)文件。

## 开发指南

如果您想要理解FPGABuilder的架构设计，手动介入开发工作，或了解工具链与开发项目的解耦机制，请参阅：

- [开发指南总览](docs/developer_guide/index.md) - 完整的开发指南
- [快速入门](docs/developer_guide/quickstart.md) - 快速上手手动开发
- [架构设计详解](docs/developer_guide/architecture.md) - 深入理解系统架构

## 贡献

欢迎贡献代码、报告问题或提出改进建议。请参阅[贡献指南](CONTRIBUTING.md)。