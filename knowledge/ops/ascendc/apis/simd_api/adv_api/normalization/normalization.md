---
type: API
title: 归一化操作
description: 归一化操作接口导航页，涵盖LayerNorm、RmsNorm、BatchNorm、GroupNorm等归一化计算接口及Tiling参数获取接口。
tags: [task.lookup, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/normalization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 归一化操作

Ascend C SIMD 高阶 API 归一化计算导航页，提供各类归一化算子的 Kernel 侧计算与 Tiling 接口。
涵盖 LayerNorm（含 Grad/GradBeta）、RmsNorm、BatchNorm、DeepNorm、GroupNorm、Normalize 及 Welford 统计（WelfordUpdate/WelfordFinalize）等接口。
每个算子均提供对应的 Tiling 接口用于获取切分参数与临时空间大小，支持前向计算与反向梯度计算。
