---
type: API
title: AscReduceMax
description: 根据mask对源操作数进行归约最大值操作，将最大值及其索引写入目的操作数。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/asc_reduce_max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscReduceMax

根据mask对源操作数src进行归约最大值操作，将最大值写入目的操作数dst的第0个元素，将最大值在src中的索引原始位模式写入dst的第1个元素，并将dst中的其他元素置0。如果存在多个最大值，则写入最小的索引。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。

支持数据类型：float、half、int16_t、int32_t、uint16_t、uint32_t。

约束：- 未被mask选中的元素被视为对应数据类型的最小值，浮点数类型的最小值为-inf。如果src中的所有元素均未被mask选中，则将该最小值写入dst的第0个元素，并将其余元素置0。
- 比较时遵循。
- 如果输入数据中存在nan，则将nan写入dst的第0个元素，并将第一个nan的索引写入dst的第1个元素。

仅 Ascend 950PR/Ascend 950DT 支持。
