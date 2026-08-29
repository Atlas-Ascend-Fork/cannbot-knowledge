---
type: API
title: AscSetMaskCount
description: 设置Mask模式为Counter模式。该模式下，不需要开发者去感知迭代次数、处理非对齐的尾块等操作，可直接传入数据计算数量，实际迭代次数由Vector计算单元自动推断。在前n个数据计算类的接口内部会自动设置该模式，不需要自行设置。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_mask_count.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetMaskCount

设置Mask模式为Counter模式。该模式下，不需要开发者去感知迭代次数、处理非对齐的尾块等操作，可直接传入数据计算数量，实际迭代次数由Vector计算单元自动推断。在前n个数据计算类的接口内部会自动设置该模式，不需要自行设置。
函数原型：void asc_set_mask_count()
约束：该API需和asc_set_vector_mask配合使用。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetVectorMask](asc_set_vector_mask.md)（`related`）：约束：该API需和asc_set_vector_mask配合使用。；该API用于设置Mask，使用前需要先调用asc_set_mask_count和asc_set_mask_norm设置Mask模式。。焦点接口先选择 Counter 模式，候选接口随后用 mask0 传入总参与元素数，构成必须按顺序调用的 Mask 配置链。
<!-- cannbot:related:end -->
