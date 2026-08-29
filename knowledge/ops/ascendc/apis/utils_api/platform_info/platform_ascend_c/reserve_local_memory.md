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

- [GetCoreMemSize](get_core_mem_size.md)（`related`）：“获取硬件平台存储空间的内存大小，例如L1、L0_A、L0_B、L2等，支持的存储空间类型定义如下：”明确给出左端事实；“该函数用于在Unified Buffer中预留指定大小的内存空间。调用该接口后，使用GetCoreMemSize可以获取实际可用的剩余Unified Buffer空间大小。”明确给出右端事实。ReserveLocalMemory 改变 UB 预留量，GetCoreMemSize 随后返回剩余可用空间；两者共同确定 Tiling 可使用的本地内存预算。
- [更多样例（数学计算）](../../../simd_api/adv_api/math_compute/more_examples.md)（`related`）：样例二：展示PlatformAscendC::ReserveLocalMemory与kernel侧API配合使用。；该函数用于在Unified Buffer中预留指定大小的内存空间。调用该接口后，使用GetCoreMemSize可以获取实际可用的剩余Unified Buffer空间大小。；接口页具体定义样例二用于计算可用 UB 的预留和查询合同。
<!-- cannbot:related:end -->
