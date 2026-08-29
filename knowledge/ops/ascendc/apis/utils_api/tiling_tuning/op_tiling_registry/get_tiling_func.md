---
type: API
title: GetTilingFunc
description: 根据算子类型OpType获取对应的Tiling函数。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/OpTilingRegistry/GetTilingFunc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# GetTilingFunc

根据算子类型 OpType 获取对应的 Tiling 函数。函数签名为 TilingFunc GetTilingFunc(const char* opType) const。
参数 opType 为算子类型字符串，需与原型定义时的算子类型保持一致。
返回值为 TilingFunc 函数指针（定义为 uint32_t(*)(gert::TilingContext*)），获取成功返回对应函数指针，失败返回空指针。
典型用法：先通过 OpTilingRegistry.LoadTilingLibrary 加载算子 so 库，再调用 GetTilingFunc("AddCustom") 获取 Tiling 函数并执行。
无特殊约束。

<!-- cannbot:related:start -->
## 相关

- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：通过OpTilingRegistry的LoadTilingLibrary接口加载Tiling动态库；使用GetTilingFunc接口获取Tiling函数指针。；典型用法：先通过 OpTilingRegistry.LoadTilingLibrary 加载算子 so 库，再调用 GetTilingFunc("AddCustom") 获取 Tiling 函数并执行。。候选 API 精确实现指南在加载动态库后的函数解析与调用步骤。
- [LoadTilingLibrary](load_tiling_library.md)（`related`）：根据输入的路径，加载对应的Tiling动态库。开发者基于工程化算子开发开发方式完成算子实现后，可通过算子包编译或算子动态库编译获取对应的Tiling动态库文件。；典型用法：先通过 OpTilingRegistry.LoadTilingLibrary 加载算子 so 库，再调用 GetTilingFunc("AddCustom") 获取 Tiling 函数并执行。。加载接口把编译产物装入进程，GetTilingFunc 随后按算子名取得并执行其中的 Tiling 函数。
<!-- cannbot:related:end -->
