---
type: API
title: aclrtAllocatorRegister
description: "将自定义 Allocator 及回调绑定到 Stream，仅用于单算子模型执行和动态 shape 推理；不同流共用同一 Allocator 时不能并发。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.callback
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-08_custom_memory_allocator.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- a3
- a2
- '310p'
- '910'
---
# aclrtAllocatorRegister

## 功能说明

注册用户自定义 Allocator 及回调函数到指定 Stream。

## 函数原型

```c
aclError aclrtAllocatorRegister(aclrtStream stream, aclrtAllocatorDesc allocatorDesc)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 需注册的 Stream，不能为 NULL |
| allocatorDesc | 输入 | Allocator 描述符指针 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 当前仅支持单算子模型执行和动态 shape 模型推理场景
- 同一 Stream 多次注册以最后一次为准
- 不同 Stream 使用同一 Allocator 时不能并发

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`3_memory_advanced/allocator/0_custom_allocator/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/allocator/0_custom_allocator/main.cpp#L100)
