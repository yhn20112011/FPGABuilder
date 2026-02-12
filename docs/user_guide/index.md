# 用户指南

## 概述

FPGABuilder是一个跨平台的FPGA自动构建工具链，旨在简化和标准化FPGA开发流程。本指南将帮助您快速上手使用FPGABuilder。

## 安装

### Windows安装

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

### 开发模式安装

如果您想要修改FPGABuilder代码：

```bash
pip install -e .
```

## 快速开始

### 创建新项目

```bash
# 初始化一个新的FPGA工程
FPGABuilder init my_project --vendor xilinx --part xc7z045ffg676-2
```

### 配置项目

```bash
# 进入项目目录
cd my_project

# 交互式配置（类似Linux内核的menuconfig）
FPGABuilder config
```

或者直接编辑配置文件 `fpga_project.yaml`。

### 构建项目

```bash
# 完整构建流程
FPGABuilder build

# 仅执行综合
FPGABuilder synth

# 生成比特流
FPGABuilder bitstream
```

### 烧录设备

```bash
# 通过JTAG烧录
FPGABuilder program --cable xilinx_tcf --target hw_server:3121
```

## 项目结构

一个标准的FPGABuilder项目包含以下结构：

```
my_project/
├── fpga_project.yaml      # 项目配置文件
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

## 配置文件详解

### 基本配置

```yaml
project:
  name: "my_fpga_project"
  version: "1.0.0"
  description: "示例FPGA工程"
  author: "Your Name"
  license: "MIT"

fpga:
  vendor: "xilinx"
  family: "zynq-7000"
  part: "xc7z045ffg676-2"
  board: "zc706"
  top_module: "system_wrapper"
```

### 源代码配置

```yaml
source:
  hdl:
    - path: "src/hdl/**/*.v"
      language: "verilog"
    - path: "src/hdl/**/*.vhd"
      language: "vhdl"
    - path: "src/hdl/**/*.sv"
      language: "systemverilog"
  constraints:
    - path: "src/constraints/*.xdc"
      type: "xilinx"
  ip_cores:
    - name: "axi_uart"
      path: "src/ip/axi_uart.xci"
      type: "xilinx"
```

### 依赖配置

```yaml
dependencies:
  git_submodules:
    - path: "lib/common"
      url: "git@example.com:fpga/common.git"
      branch: "main"
    - path: "ip_repo/axi_cores"
      url: "git@example.com:fpga/axi-cores.git"
      branch: "v1.0"
  python_packages:
    - "numpy"
    - "matplotlib"
```

### 构建配置

```yaml
build:
  synthesis:
    strategy: "out_of_context"
    options:
      flatten_hierarchy: "rebuilt"
      fanout_limit: 10000
  implementation:
    options:
      opt_design: true
      place_design: true
      route_design: true
  bitstream:
    options:
      bin_file: true
      mask_file: true
```

### 文档配置

```yaml
documentation:
  enabled: true
  format: "mkdocs"
  output_dir: "docs"
  include_doxygen: true
  doxygen_config: "docs/doxygen.conf"
```

## 命令行参考

### 全局选项

```
FPGABuilder [全局选项] <命令> [命令选项]

全局选项:
  -c, --config FILE    指定配置文件（默认：fpga_project.yaml）
  -v, --verbose        详细输出模式
  -q, --quiet          静默模式
  --version            显示版本信息
  -h, --help           显示帮助信息
```

### 常用命令

| 命令 | 描述 | 示例 |
|------|------|------|
| `init` | 初始化新项目 | `FPGABuilder init my_project --vendor xilinx` |
| `create` | 创建项目结构 | `FPGABuilder create --template zynq` |
| `config` | 配置项目 | `FPGABuilder config` |
| `build` | 构建项目 | `FPGABuilder build` |
| `synth` | 仅综合 | `FPGABuilder synth` |
| `impl` | 仅实现 | `FPGABuilder impl` |
| `bitstream` | 生成比特流 | `FPGABuilder bitstream` |
| `program` | 烧录设备 | `FPGABuilder program --cable xilinx_tcf` |
| `ip` | 管理IP核 | `FPGABuilder ip create axi_uart` |
| `hls` | 管理HLS工程 | `FPGABuilder hls create --language cpp` |
| `docs` | 生成文档 | `FPGABuilder docs --format mkdocs` |
| `clean` | 清理构建文件 | `FPGABuilder clean --all` |
| `pack` | 打包发布 | `FPGABuilder pack --output release.zip` |

### 命令示例

```bash
# 查看所有可用命令
FPGABuilder --help

# 查看具体命令帮助
FPGABuilder init --help

# 使用指定配置文件
FPGABuilder -c custom_config.yaml build

# 详细输出模式
FPGABuilder --verbose build

# 创建IP核
FPGABuilder ip create axi_uart --type axi4lite --data-width 32

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

### 使用插件

```bash
# 列出可用插件
FPGABuilder plugins list

# 启用插件
FPGABuilder plugins enable vivado_advanced

# 禁用插件
FPGABuilder plugins disable vivado_advanced
```

## 高级功能

### 1. 增量构建

FPGABuilder支持增量构建，只重新构建发生变化的部分：

```bash
# 启用增量构建
FPGABuilder build --incremental

# 强制完整构建
FPGABuilder build --clean
```

### 2. 并行构建

利用多核CPU加速构建过程：

```bash
# 使用4个并行任务
FPGABuilder build --parallel 4

# 自动检测CPU核心数
FPGABuilder build --parallel auto
```

### 3. 构建缓存

FPGABuilder支持构建结果缓存，避免重复计算：

```bash
# 启用缓存
FPGABuilder build --cache

# 清理缓存
FPGABuilder cache clean
```

### 4. 远程构建

支持在远程服务器上执行构建：

```bash
# 在远程服务器上构建
FPGABuilder build --remote server.example.com

# 指定远程工作目录
FPGABuilder build --remote user@server:/home/user/build
```

## 故障排除

### 常见问题

#### 1. 插件加载失败

**症状**：
```
错误：无法加载插件 'vivado'
```

**解决方法**：
1. 检查插件是否安装：`FPGABuilder plugins list`
2. 检查插件依赖是否满足
3. 查看详细错误信息：`FPGABuilder --verbose plugins list`

#### 2. 配置验证失败

**症状**：
```
错误：配置验证失败
```

**解决方法**：
1. 验证配置文件语法：`FPGABuilder validate`
2. 检查必填字段是否完整
3. 查看具体错误信息

#### 3. 构建过程失败

**症状**：
```
错误：构建失败
```

**解决方法**：
1. 查看详细构建日志：`FPGABuilder --verbose build`
2. 检查工具链是否安装正确
3. 查看构建报告：`build/reports/build_summary.html`

### 调试技巧

```bash
# 启用调试模式
FPGABuilder --verbose build

# 生成详细日志
FPGABuilder build --log-level DEBUG

# 保存构建报告
FPGABuilder build --report-file build_report.json

# 仅验证配置不执行构建
FPGABuilder build --dry-run
```

## 最佳实践

### 1. 版本控制

- 将 `fpga_project.yaml` 添加到版本控制
- 使用git子模块管理第三方IP核
- 在配置中包含版本信息

### 2. 项目组织

- 按功能模块组织源代码
- 使用一致的命名规范
- 为每个模块提供测试

### 3. 构建配置

- 为不同构建目标创建配置变体
- 使用条件构建选项
- 记录构建配置变化

### 4. 文档维护

- 使用FPGABuilder自动生成文档
- 为项目提供使用说明
- 记录设计决策和架构

## 从传统项目迁移

如果您有一个传统的FPGA项目（使用Makefile、TCL脚本等），可以按以下步骤迁移：

1. **分析现有项目结构**
   ```bash
   # 识别关键组件
   # - 源代码文件
   # - 约束文件
   # - IP核文件
   # - 构建脚本
   ```

2. **创建FPGABuilder配置**
   ```bash
   # 生成基础配置
   FPGABuilder init existing_project --vendor xilinx --part <your_part>
   ```

3. **转换构建脚本**
   ```python
   # 将TCL脚本转换为配置选项
   # 将Makefile目标转换为构建步骤
   ```

4. **逐步迁移**
   - 先迁移基本构建流程
   - 再迁移高级功能
   - 最后优化和自动化

## 获取帮助

- 查看命令帮助：`FPGABuilder --help`
- 查阅在线文档
- 在GitHub Issues报告问题
- 参与社区讨论

## 更新日志

各版本更新内容请参阅[CHANGELOG.md](../CHANGELOG.md)。