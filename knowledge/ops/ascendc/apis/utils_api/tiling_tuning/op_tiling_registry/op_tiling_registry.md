---
type: API
title: OpTilingRegistry
description: OpTilingRegistry注册接口索引。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/OpTilingRegistry/OpTilingRegistry.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# OpTilingRegistry

OpTilingRegistry 用于注册和管理算子的 Tiling 函数，提供构造析构、Tiling 函数获取（GetTilingFunc）和 Tiling 库动态加载（LoadTilingLibrary）接口。通过该注册机制，算子的 Tiling 策略可以在运行时动态绑定，支持 Tiling 库的独立编译与加载。

<!-- cannbot:related:start -->
## 相关

- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：焦点处理OpTilingRegistry 的加载、取函数与 Tiling 调测入口；TilingDebug正文说明“通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测”。候选把 Registry 类落到可执行的动态库加载、ContextBuilder 构造与 GetTilingFunc 调测流程。
- [GetTilingFunc](get_tiling_func.md)（`same_topic`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；OpTilingRegistry正文界定“OpTilingRegistry注册接口索引”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
- [构造和析构函数](constructor_and_destructor.md)（`same_topic`）：OpTilingRegistry 总览把构造析构、LoadTilingLibrary 和 GetTilingFunc 组织为完整注册流程。
<!-- cannbot:related:end -->
