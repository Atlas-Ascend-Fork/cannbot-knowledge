---
type: API
title: ReserveLocalMemory
description: 该函数用于在Unified Buffer中预留指定大小的内存空间。调用该接口后，使用GetCoreMemSize可以获取实际可用的剩余Unified
  Buffer空间大小。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/ReserveLocalMemory.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# ReserveLocalMemory

## 功能说明
该函数用于在Unified Buffer中预留指定大小的内存空间。调用该接口后，使用GetCoreMemSize可以获取实际可用的剩余Unified Buffer空间大小。
## 函数原型
## 参数说明
## 返回值说明
无
## 约束说明
多次调用该函数时，仅保留最后一次调用的结果。

<!-- cannbot:related:start -->
## 相关

- [CheckLocalMemoryIA](../../../simd_api/basic_api/debug_interface/exception_detection/check_local_memory_ia_isasi.md)（`related`）：CheckLocalMemoryIA 与《ReserveLocalMemory》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [GetCoreMemSize](get_core_mem_size.md)（`related`）：GetCoreMemSize 与《ReserveLocalMemory》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
<!-- cannbot:related:end -->
