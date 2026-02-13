# 用户指南

## 概述

FPGABuilder是一个跨平台的FPGA自动构建工具链，旨在简化和标准化FPGA开发流程。本指南将帮助您快速上手使用FPGABuilder。

## 安装

### 安装whl文件

pip install dist/FPGABuilder-0.1.0-py3-none-any.whl

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

## 从零开始创建Zynq项目

本节将指导您如何从零开始创建一个完整的Zynq项目，并生成比特流。基于我们的测试经验，我们将展示完整的流程和常见问题的解决方案。

### 步骤1：创建项目

使用 `init`命令创建新的Zynq项目，指定FPGA器件和模板：

```bash
# 创建名为my_zynq_project的Zynq项目
FPGABuilder init my_zynq_project --vendor xilinx --part xc7z045ffg676-2 --template zynq
```

该命令将：

1. 创建项目目录结构
2. 生成配置文件 `fpga_project.yaml`
3. 创建示例HDL文件 `src/hdl/my_zynq_project_top.v`
4. 创建示例约束文件 `src/constraints/clocks.xdc`
5. 提供后续步骤指导

### 步骤2：配置项目

检查生成的配置文件 `fpga_project.yaml`：

```yaml
project:
  name: my_zynq_project
  version: 1.0.0
  description: my_zynq_project FPGA工程
fpga:
  vendor: xilinx
  part: xc7z045ffg676-2
  family: zynq-7000
  top_module: my_zynq_project_wrapper
template: zynq
source:
  hdl:
    - path: src/hdl/**/*.v
      language: verilog
  constraints:
    - path: src/constraints/*.xdc
      type: xilinx
build:
  synthesis:
    strategy: Vivado Synthesis Defaults
  implementation:
    options: {}
  bitstream:
    options:
      bin_file: true
```

根据您的设计需求修改配置。

### 步骤3：编辑约束文件

**关键步骤**：Vivado要求所有逻辑端口都有引脚位置约束，否则会拒绝生成比特流（DRC错误 UCIO-1）。

打开 `src/constraints/clocks.xdc`，根据实际硬件修改引脚分配：

```tcl
# 时钟约束
create_clock -name clk -period 10.000 [get_ports clk]

# 电气标准
set_property IOSTANDARD LVCMOS33 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
# ... 为所有端口设置IOSTANDARD

# 引脚位置约束（示例：ZC706开发板）
set_property PACKAGE_PIN Y9 [get_ports clk]
set_property PACKAGE_PIN AB10 [get_ports rst_n]
# ... 为所有端口添加PACKAGE_PIN约束

# 对于测试目的，可以暂时降低DRC严重性（不推荐用于生产）：
# set_property SEVERITY {Warning} [get_drc_checks UCIO-1]
```

**重要**：必须为顶层模块的所有输入/输出端口添加完整的引脚约束。

### 步骤4：添加HDL源代码

编辑 `src/hdl/my_zynq_project_top.v` 或添加新的HDL文件。确保顶层模块名称与配置中的 `fpga.top_module` 一致。

### 步骤5：构建项目

运行完整构建流程：

```bash
# 进入项目目录
cd my_zynq_project

# 运行完整构建（综合→实现→比特流）
FPGABuilder build

# 或使用Vivado特定命令
FPGABuilder vivado build --steps all
```

构建过程：

1. **综合**：将HDL转换为门级网表
2. **实现**：布局布线，生成物理设计
3. **比特流生成**：生成配置文件（.bit）

### 步骤6：处理常见问题

#### 问题1：比特流生成失败，DRC错误 "Unconstrained Logical Port"

**现象**：

```
[ERROR] 比特流生成失败
ERROR: [DRC UCIO-1] Unconstrained Logical Port: X ports have no user assigned specific location constraint (LOC).
```

**解决方案**：

1. 检查约束文件是否包含所有端口的 `PACKAGE_PIN` 约束
2. 确保约束文件中的端口名称与HDL中的信号名称完全一致
3. 使用 `get_ports` 命令验证端口列表
4. 对于测试目的，可以临时降低DRC严重性（在约束文件中添加）：
   ```tcl
   set_property SEVERITY {Warning} [get_drc_checks UCIO-1]
   ```

#### 问题2：工程打开错误 "No open project"

**现象**：实现或比特流生成步骤失败，错误信息 "No open project"

**解决方案**：这是FPGABuilder插件问题，已修复。确保使用最新版本。

#### 问题3：约束文件未正确加载

**现象**：约束未被应用，时序约束失效

**解决方案**：

1. 检查约束文件路径配置
2. 使用 `FPGABuilder vivado import-files` 重新导入文件
3. 查看构建日志确认约束文件加载状态

### 步骤7：生成二进制文件（可选）

对于Zynq设备，可以生成boot.bin文件：

```bash
# 需要FSBL.elf文件和比特流文件
FPGABuilder vivado packbin --output boot.bin --fsbl fsbl.elf --bitstream my_zynq_project.bit
```

### 验证构建成功

构建成功后，检查输出文件：

- `build/bitstreams/my_zynq_project.bit` - 比特流文件
- `build/reports/` - 构建报告（时序、资源利用率等）
- `build/logs/` - 详细构建日志

### 最佳实践

1. **版本控制**：将配置文件、HDL源代码和约束文件加入版本控制
2. **约束管理**：为每个硬件板卡创建单独的约束文件
3. **模块化设计**：将设计分解为多个模块，便于复用和维护
4. **持续集成**：使用FPGABuilder自动化构建流程
5. **文档记录**：记录设计决策和约束配置

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
  # 钩子脚本配置（可选）
  hooks:
    # 构建前钩子：整个构建流程开始前执行
    pre_build: |
      echo "构建开始前检查环境"
      python scripts/check_dependencies.py
      echo "当前目录: $(pwd)"

    # 综合前钩子：综合步骤开始前执行
    pre_synth: "scripts/pre_synth.tcl"

    # 综合后钩子：综合完成后执行
    post_synth: "echo '综合完成'"

    # 实现前钩子：实现步骤开始前执行
    pre_impl: |
      echo "实现前命令1"
      echo "实现前命令2"

    # 实现后钩子：实现完成后执行
    post_impl: "scripts/post_impl.py"

    # 比特流后钩子：比特流生成后执行
    post_bitstream:
      - echo "比特流生成完成"
      - cp build/bitstreams/*.bit releases/
      - python scripts/notify.py --message "构建完成"

    # 二进制合并脚本（Zynq等SoC使用）
    bin_merge_script: "scripts/merge_bin.py"

    # 自定义脚本映射
    custom_scripts:
      custom1: "scripts/custom1.tcl"
      custom2: "scripts/custom2.py"
```

### 钩子脚本配置

钩子脚本允许在构建流程的不同阶段执行自定义命令，非常适合自动化任务如环境检查、文件复制、通知发送等。

#### 支持的钩子类型

| 钩子名称 | 执行时机 | 示例用途 |
|---------|---------|---------|
| `pre_build` | 整个构建流程开始前 | 环境检查、依赖下载、目录清理 |
| `pre_synth` | 综合步骤开始前 | 设置综合参数、运行预处理脚本 |
| `post_synth` | 综合完成后 | 生成综合报告、分析时序结果 |
| `pre_impl` | 实现步骤开始前 | 设置实现策略、加载额外约束 |
| `post_impl` | 实现完成后 | 生成实现报告、分析布局布线结果 |
| `post_bitstream` | 比特流生成后 | 复制比特流文件、发送构建通知 |
| `bin_merge_script` | 二进制文件合并 | 为Zynq等SoC生成boot.bin文件 |

#### 钩子格式

钩子支持三种配置格式：

1. **单行字符串**：
   ```yaml
   hooks:
     pre_synth: "scripts/pre_synth.tcl"
   ```

2. **多行字符串**：
   ```yaml
   hooks:
     pre_build: |
       echo "开始构建"
       python scripts/check_env.py
       echo "环境检查完成"
   ```

3. **命令数组**：
   ```yaml
   hooks:
     post_bitstream:
       - echo "比特流生成完成"
       - cp build/bitstreams/*.bit releases/
       - python scripts/notify.py
   ```

#### 执行规则

- **脚本文件检测**：如果钩子值是存在的文件路径，将作为脚本文件执行
  - `.py`文件使用Python执行
  - `.tcl`文件在Vivado环境中执行
  - `.sh`文件使用bash执行
- **直接命令**：如果钩子值不是文件路径，将作为shell命令直接执行
- **错误处理**：钩子执行失败时，会询问用户是否继续构建
- **平台兼容**：Windows/Linux/macOS均可使用

#### 实用示例

```yaml
build:
  hooks:
    # 构建前检查环境
    pre_build: |
      echo "=== 构建环境检查 ==="
      echo "Python版本: $(python --version)"
      echo "当前目录: $(pwd)"
      echo "时间: $(date)"

    # 比特流生成后复制文件
    post_bitstream:
      - echo "=== 复制比特流文件 ==="
      - mkdir -p releases
      - cp build/bitstreams/*.bit releases/
      - "if [ -f build/bitstreams/*.ltx ]; then cp build/bitstreams/*.ltx releases/; fi"
      - echo "文件已复制到 releases/ 目录"

    # 使用脚本文件
    pre_synth: "scripts/generate_constraints.py"
    post_impl: "scripts/analyze_timing.tcl"
```

### 开发工具路径配置

FPGABuilder支持通过配置文件指定开发工具的安装路径和版本，这在以下场景中特别有用：
- 系统安装了多个版本的开发工具
- 开发工具安装在非标准位置
- 需要确保特定版本的工具被使用

#### Vivado配置示例

```yaml
fpga:
  vendor: "xilinx"
  family: "zynq-7000"
  part: "xc7z045ffg676-2"
  top_module: "system_wrapper"
  # Vivado安装路径（可选）
  vivado_path: "C:/Xilinx/Vivado/2019.1"
  # Vivado版本号（可选，格式：YYYY.N）
  vivado_version: "2019.1"
  # Vivado设置（可选）
  vivado_settings:
    default_lib: "xil_defaultlib"
    target_language: "verilog"
    synthesis_flow: "project"
    implementation_flow: "project"
```

#### 配置说明

| 配置项 | 类型 | 描述 | 示例 |
|--------|------|------|------|
| `vivado_path` | 字符串 | Vivado安装路径。可以是：<br>1. `vivado.bat` (Windows) 或 `vivado` (Linux) 可执行文件路径<br>2. Vivado安装目录（自动查找可执行文件）<br>3. 如果未指定，FPGABuilder将自动检测系统安装 | `"C:/Xilinx/Vivado/2019.1"`<br>`"D:/Tools/Vivado/2023.2/bin/vivado.bat"` |
| `vivado_version` | 字符串 | Vivado版本号，格式：YYYY.N。<br>用于版本兼容性检查，确保使用正确的版本。<br>如果未指定，将从可执行文件或路径中自动检测 | `"2019.1"`<br>`"2023.2"`<br>`"2024.1"` |
| `vivado_settings` | 对象 | Vivado特定设置，包括：<br>- `default_lib`: 默认库名称<br>- `target_language`: 目标语言（verilog/vhdl）<br>- `synthesis_flow`: 综合流程（out_of_context/project）<br>- `implementation_flow`: 实现流程（project/non_project） | 见上方示例 |

#### 工作流程

1. **配置优先**：如果配置了 `vivado_path`，FPGABuilder将首先尝试使用该路径
2. **路径验证**：检查路径是否存在，查找Vivado可执行文件
3. **版本检查**：如果配置了 `vivado_version`，验证实际版本是否匹配
4. **自动回退**：如果配置路径无效，回退到自动检测

#### 跨平台注意事项

- **Windows**: Vivado可执行文件通常是 `vivado.bat`
- **Linux**: Vivado可执行文件通常是 `vivado`
- **路径格式**: 使用正斜杠 `/` 或双反斜杠 `\\` 作为路径分隔符
- **环境变量**: 支持在路径中使用环境变量（如 `%VIVADO_HOME%` 或 `$VIVADO_HOME`）

#### 版本兼容性

FPGABuilder支持Vivado 2018.0至2024.2版本：
- **2019.x**: 使用Vivado2019Adapter（新增）
- **2023.x**: 使用Vivado2023Adapter
- **2024.x**: 使用Vivado2024Adapter
- **其他版本（2018.0-2022.x）**: 使用默认适配器（无版本特定适配）

FPGABuilder为Vivado 2019.1提供了专门的适配器，确保版本兼容性。对于2018.0-2022.x的其他版本，使用默认适配器，基本功能可用，但某些版本特定命令可能受限。

#### 配置验证

使用以下命令验证配置：
```bash
# 验证配置文件语法
FPGABuilder validate

# 详细模式显示工具检测信息
FPGABuilder --verbose build --dry-run
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

| 命令          | 描述         | 示例                                            |
| ------------- | ------------ | ----------------------------------------------- |
| `init`      | 初始化新项目 | `FPGABuilder init my_project --vendor xilinx` |
| `create`    | 创建项目结构 | `FPGABuilder create --template zynq`          |
| `config`    | 配置项目     | `FPGABuilder config`                          |
| `build`     | 构建项目     | `FPGABuilder build`                           |
| `synth`     | 仅综合       | `FPGABuilder synth`                           |
| `impl`      | 仅实现       | `FPGABuilder impl`                            |
| `bitstream` | 生成比特流   | `FPGABuilder bitstream`                       |
| `program`   | 烧录设备     | `FPGABuilder program --cable xilinx_tcf`      |
| `ip`        | 管理IP核     | `FPGABuilder ip create axi_uart`              |
| `hls`       | 管理HLS工程  | `FPGABuilder hls create --language cpp`       |
| `docs`      | 生成文档     | `FPGABuilder docs --format mkdocs`            |
| `clean`     | 清理构建文件 | `FPGABuilder clean --all`                     |
| `pack`      | 打包发布     | `FPGABuilder pack --output release.zip`       |

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

#### 3. 工具检测失败

**症状**：
```
错误：未检测到Vivado安装
警告：Vivado版本不匹配: 配置版本=2023.2, 实际版本=2019.1
```

**解决方法**：
1. **检查开发工具安装**：
   - 确认Vivado已正确安装
   - 验证Vivado可执行文件路径在系统PATH中

2. **配置工具路径**（推荐）：
   - 在 `fpga_project.yaml` 中添加 `vivado_path` 和 `vivado_version` 配置
   - 示例：
     ```yaml
     fpga:
       vivado_path: "C:/Xilinx/Vivado/2023.2"
       vivado_version: "2023.2"
     ```

3. **版本兼容性检查**：
   - FPGABuilder支持Vivado 2018.0-2024.2版本
   - 如果使用2019.1等早期版本，某些高级功能可能受限
   - 建议升级到2023.2或更新版本以获得最佳体验

4. **环境变量设置**：
   - Windows: 设置 `VIVADO_HOME` 环境变量
   - Linux: 确保Vivado安装目录在PATH中

5. **详细检测**：
   ```bash
   # 显示工具检测详情
   FPGABuilder --verbose plugins list
   # 或
   FPGABuilder --verbose build --dry-run
   ```

#### 4. 构建过程失败

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

## Block Design支持

FPGABuilder支持Vivado Block Design (BD) 工作流。您可以使用以下配置来集成Block Design：

```yaml
source:
  block_design:
    tcl_script: "bd/system.tcl"   # 从Vivado导出的TCL脚本，用于恢复BD设计
    is_top: true                  # BD是否为顶层设计
    generate_wrapper: true        # 自动生成包装器 (make_wrapper)
    wrapper_language: "verilog"   # 包装器语言 (verilog/vhdl)
    # 可选：如果已有.bd文件，可以直接指定：
    # bd_file: "bd/system.bd"
```

**工作流程**：
1. FPGABuilder创建工程并导入源文件
2. 设置IP库路径 (ip_repo)
3. 执行 `source system.tcl` 恢复BD设计
4. 自动生成包装器：`make_wrapper -files [get_files [current_bd_design]] -top`
5. 设置顶层模块为生成的包装器
6. 继续构建流程（综合、实现、比特流生成）

**注意事项**：
- 确保TCL脚本包含完整的BD创建命令
- 如果使用`bd_file`而不是`tcl_script`，FPGABuilder会直接加载.bd文件
- `is_top: true` 将BD设置为顶层设计
- 包装器生成后，顶层模块会自动设置为包装器模块

## 更新日志

各版本更新内容请参阅[CHANGELOG.md](../CHANGELOG.md)。
