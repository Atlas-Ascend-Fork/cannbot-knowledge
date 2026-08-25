---
type: API
title: 数据填充
description: Reg矢量计算数据填充接口索引页，包含Duplicate。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_padding/data_padding.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据填充

提供 Duplicate 接口，支持 Scalar 和 Tensor 两种模式将数据广播到寄存器。Scalar 模式将 scalarValue 广播到 dstReg（可选 mask 筛选位置）；Tensor 模式将 srcReg 最低位元素广播到 dstReg 被 mask 筛选的位置。

支持 MaskMergeMode 控制 mask 未筛选元素的写入行为（ZEROING 置零或保留原值）。仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。
