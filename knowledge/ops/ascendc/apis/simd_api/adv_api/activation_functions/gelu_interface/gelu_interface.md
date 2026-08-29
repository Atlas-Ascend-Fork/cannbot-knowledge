---
type: API
title: Gelu接口
description: 提供Gelu激活函数接口及变体，包含Gelu、FasterGelu、FasterGeluV2及GetGeluMaxMinTmpSize等Tiling查询接口。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Gelu_interface/Gelu_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Gelu接口

提供 Gaussian Error Linear Unit 激活函数的 Kernel 侧计算接口及变体。
包含 Gelu、FasterGelu、FasterGeluV2 三种实现，以及 GetGeluMaxMinTmpSize 用于查询 Tiling 临时空间上下界。
FasterGelu 系列通过近似算法降低计算开销，适用于对精度要求可放松的场景。
