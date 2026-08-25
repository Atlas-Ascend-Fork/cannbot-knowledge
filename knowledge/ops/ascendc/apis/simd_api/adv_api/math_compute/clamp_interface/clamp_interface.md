---
type: API
title: Clamp接口
description: 提供Clamp数值截断接口及其变体ClampMax、ClampMin，以及GetClampMaxMinTmpSize等Tiling临时空间大小查询接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/Clamp_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Clamp接口

提供数值截断（Clamp）操作的 Kernel 侧接口及变体，用于将张量元素限制在指定范围内。
包含 Clamp 双向截断、ClampMax 上界截断、ClampMin 下界截断三种计算接口，以及 GetClampMaxMinTmpSize 和 GetClampTmpBufferFactorSize 用于查询 Tiling 临时空间大小与因子。
