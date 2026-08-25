---
type: API
title: AscSetVectorMask
description: 为矢量计算接口设置参与计算的数据 Mask；调用前需通过 asc_set_mask_count 和 asc_set_mask_norm 选择 Mask 模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_vector_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# AscSetVectorMask

某些矢量计算接口需要提前设置Mask，提示哪些数据需要参与计算。 该API用于设置Mask，使用前需要先调用asc_set_mask_count和asc_set_mask_norm设置Mask模式。在不同的模式下Mask的含义如下：
函数原型：void asc_set_vector_mask(uint64_t mask1, uint64_t mask0)
参数：mask1（输入）：Normal模式：高位mask值。 Counter模式：需要置0，本入参不生效。；mask0（输入）：Normal模式：低位mask值。 Counter模式：整个矢量计算过程中，参与计算的元素个数。
约束：需先调用asc_set_mask_count或asc_set_mask_norm设置Mask模式。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
