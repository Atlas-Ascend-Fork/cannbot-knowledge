---
type: API
title: AscSetCmpMask
description: 为asc_select操作设置作用于选择的Mask掩码。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_cmp_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetCmpMask

为asc_select操作设置作用于选择的Mask掩码。
函数原型：void asc_set_cmp_mask(__ubuf__ void* sel_mask)
参数：sel_mask（输入）：用于选择的Mask掩码的起始地址。
约束：需和asc_select操作配合使用。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSelect](asc_select.md)（`related`）：需和asc_select操作配合使用。；执行矢量选择操作，给定两个源操作数src0和src1，根据条件选择元素，得到目的操作数dst。此接口配合asc_set_cmp_mask(sel_mask)设置，规则为：当sel_mask的比特位是1时，从src0选取；当比特位是0时，从src1选择。。AscSetCmpMask 提供 AscSelect 消费的选择掩码，AscSelect 明确给出每个 mask bit 到 src0/src1 的选择规则，构成配置到执行的直接调用链。
<!-- cannbot:related:end -->
