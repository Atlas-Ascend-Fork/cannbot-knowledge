---
type: API
title: SoftMax接口
description: 提供SoftMax及其变体接口，包含SoftMax、SimpleSoftMax、SoftmaxFlash、SoftmaxGrad等以及Tiling使用说明。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftMax_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SoftMax接口

提供 SoftMax 及其变体的 Kernel 侧计算与 Tiling 接口，覆盖标准 SoftMax、SimpleSoftMax、SoftmaxFlash（V2/V3）、SoftmaxGrad、SoftmaxGradFront、AdjustSoftMaxRes 等场景。
Tiling 侧接口为各变体提供独立的临时空间查询与切分参数获取方法，并包含 IsBasicBlockInSoftMax 用于判断输入是否满足 BasicBlock 对齐条件。
SoftmaxFlash 系列针对 Flash Attention 场景优化，支持前向与反向梯度计算。
