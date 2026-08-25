---
type: API
title: asc_reduce_min
description: 对Warp内所有活跃线程输入val求最小值。Warp内所有活跃线程返回相同的结果。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_reduce_functions/asc_reduce_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_reduce_min

对Warp内所有活跃线程输入val求最小值。Warp内所有活跃线程返回相同的结果。

函数原型：inline int32_t asc_reduce_min(int32_t val)；inline uint32_t asc_reduce_min(uint32_t val)；inline float asc_reduce_min(float val) 等4种重载

参数：val（输入）：源操作数。

返回值：Warp内所有活跃线程输入val的最小值。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。
