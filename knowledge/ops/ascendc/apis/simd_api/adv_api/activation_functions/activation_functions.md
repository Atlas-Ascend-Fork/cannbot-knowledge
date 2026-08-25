---
type: API
title: 激活函数
description: 汇总Ascend C SIMD高阶API中各类激活函数接口，包括SoftMax、LogSoftMax、Gelu、SwiGLU、Silu、Swish、GeGLU、ReGlu、Sigmoid等。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/activation_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 激活函数

Ascend C SIMD 高阶 API 激活函数导航页，提供神经网络常用激活算子的 Kernel 侧接口。
涵盖 SoftMax、LogSoftMax、Gelu、SwiGLU、Silu、Swish、GeGLU、ReGlu、Sigmoid 等接口，每个接口独立提供计算与 Tiling 查询方法。
各接口支持的数据类型与约束请参见对应子卡片。
