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
