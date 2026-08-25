---
type: Guide
title: 外部样例链接汇总（附录）
description: 本文是参考内容，汇总指南中引用的外部代码样例和API参考链接，便于开发者快速查找和参考。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/appendix/external_sample_links.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 外部样例链接汇总

本文是参考内容，汇总指南中引用的外部代码样例和API参考链接，便于开发者快速查找和参考。

## 代码样例

### 基础算子实现

- AddCustom算子样例里的AddCustom样例。
  - 说明：展示基础的完整算子实现，包括TilingData定义、Tiling函数和Kernel代码。

### msOpGen工具生成自定义算子工程模板

- [msOpGen样例](https://gitcode.com/cann/asc-tools/tree/master/examples/03_msopgen)。
  - 说明：基于AddCustom算子演示如何使用msOpGen工具生成自定义算子工程模板，并通过ACLNN调用示例验证生成的自定义算子。

### TilingData传递属性

- LeakyReluCustom里的leaky_relu_custom样例。
  - 说明：通过TilingData传递属性信息。

### 模板编程算子实现

- Kernel模板编程样例。
  - 说明：展示使用Kernel模板参数实现编译期分支控制的示例。

### 编译与集成样例

- 静态库集成和使用样例。
  - 说明：展示如何将算子编译为静态库并集成到应用中。

- aclnn单算子调用样例。
  - 说明：展示如何通过aclnn API调用自定义算子。

## API参考

### Tiling API

- Tiling数据结构。
  - 说明：Tiling数据结构参考。

- GetLibApiWorkSpaceSize。
  - 说明：获取Ascend C API预留workspace大小的方法。

### 模板编程API

- 模板参数定义。
  - 说明：ASCENDC_TPL_ARGS_DECL、ASCENDC_TPL_ARGS_SEL等模板参数宏的定义。

### 原型注册API

- OpAICoreConfig注册接口。
  - 说明：OpAICoreConfig类用于多硬件平台差异化原型注册。

## 其他参考

- [图引擎开发指南](https://www.hiascend.com/document/redirect/CannCommunityGraphguide)。
  - 说明：Ascend Graph图开发的完整指南，适用于算子入图场景。
