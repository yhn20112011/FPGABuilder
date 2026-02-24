# FPGABuilder 文档

欢迎使用FPGABuilder文档。本文档提供全面的使用指南、开发参考和架构说明。

## 用户文档

- [用户指南](user_guide/) - 安装、配置和使用FPGABuilder
- [命令行参考](../README.md#命令行参考) - 所有命令和选项的详细说明
- [配置示例](../README.md#配置文件示例) - 配置文件示例和说明

## 开发文档

### 入门指南
- [开发指南总览](developer_guide/index.md) - 完整的开发指南
- [快速入门](developer_guide/quickstart.md) - 快速上手手动开发
- [架构设计详解](developer_guide/architecture.md) - 深入理解系统架构

### 核心概念
- **配置驱动开发**：项目通过YAML配置文件定义，实现开发流程与具体工具链的解耦
- **插件化架构**：所有功能通过插件实现，支持轻松扩展和定制
- **统一接口**：为不同FPGA厂商提供一致的开发体验

### 工具链解耦设计

FPGABuilder的核心创新在于将工具链与开发项目完全解耦：

```
传统方式：
项目文件 → 特定工具链脚本 → 厂商工具

FPGABuilder方式：
项目配置 → 插件管理器 → 厂商插件 → 具体工具链
```

**解耦带来的优势**：
1. **可移植性**：同一项目可在不同厂商工具链间切换
2. **可维护性**：工具链更新不影响项目配置
3. **可扩展性**：新增厂商只需实现插件接口
4. **可测试性**：插件可独立测试，不依赖具体项目

## API参考

- [核心模块](../src/core/) - 配置管理、项目管理、插件管理等核心模块
- [插件系统](../src/plugins/) - 插件开发接口和示例
- [工具函数](../src/utils/) - 常用工具函数和辅助类

## 示例项目

- [示例项目](../examples/) - 各种使用场景的示例项目
- [现有项目转换](../backup_existing_project/) - 传统FPGA项目转换为FPGABuilder格式的示例

## 贡献指南

请参阅[贡献指南](../CONTRIBUTING.md)了解如何为项目做出贡献。

## 获取帮助

- [GitHub Issues](https://github.com/yhn20112011/FPGABuilder/issues) - 报告问题和缺陷
- [GitHub Discussions](https://github.com/yhn20112011/FPGABuilder/discussions) - 提问和讨论
- [在线文档](https://yhn20112011.github.io/FPGABuilder/) - 最新文档

## 许可证

本项目采用 Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)。详见[LICENSE](../LICENSE)文件。

未经本人书面授权任何人不得商用，本人保留一切权力。