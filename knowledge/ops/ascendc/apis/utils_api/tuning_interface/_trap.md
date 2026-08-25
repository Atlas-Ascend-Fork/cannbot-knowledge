---
type: API
title: __trap
description: 在SIMT代码中调用此接口会中断算子的运行，适用于Kernel侧异常场景的调试。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/__trap.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __trap

在SIMT代码中调用此接口会中断算子的运行，适用于Kernel侧异常场景的调试。

函数原型：inline void __trap()

返回值：无

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "utils/debug/asc_assert.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。
