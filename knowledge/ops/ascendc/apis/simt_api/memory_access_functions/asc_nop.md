---
type: API
title: asc_nop（内存访问函数）
description: 本接口的功能为生成一条空操作指令，占用当前线程15个时钟周期，不执行任何实际计算与访存操作。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/asc_nop.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_nop

空操作函数。生成一条空操作指令，占用当前线程 15 个时钟周期，不执行任何实际计算与访存操作。主要用于避免多个线程读写同地址时可能发生的卡死问题。

函数原型：inline void asc_nop()

无参数，无返回值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [避免同地址访问](../../../guides/operator_practice/simd_operator_optimization/memory_access/avoid_same_address_access.md)（`explains`）：主要用于避免多个线程读写同地址时可能发生的卡死问题。；当同时访问Global Memory的数据，且地址处于连续的512字节范围内时，由于数据一致性的原因，多个请求会被串行处理，进而影响数据搬运效率。；目标页补充同地址请求的 512 字节归并和串行机制，可用于识别 asc_nop 所针对的访问形态。
<!-- cannbot:related:end -->
