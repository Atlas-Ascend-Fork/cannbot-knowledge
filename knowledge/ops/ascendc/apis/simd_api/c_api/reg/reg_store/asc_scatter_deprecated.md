---
type: API
title: asc_scatter
description: 该接口已废弃。请使用asc_scatter实现此功能。 该指令会根据索引值index将源操作数src中的元素分散到目的操作数dst中。分散过程如下图所示：
  !scatter功能说明
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_scatter_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_scatter

该接口已废弃。请使用asc_scatter实现此功能。 该指令会根据索引值index将源操作数src中的元素分散到目的操作数dst中。分散过程
函数原型：void asc_scatter(vector_int8_t& src, __ubuf__ int8_t* dst, vector_uint16_t index, vector_bool mask)
约束：dst首地址必须32B对齐。；当dst为int8_t或者uint8_t数据类型时，源操作数中仅偶数位元素有效。即src中的偶数位置[0, 2, 4, ..., 252, 254]的数据会被分散存储到目的操作数中。；index中的值必须唯一。若存在重复的index值，系统仅保留其中一个对应的数据，其余将被忽略。无法确定具体保留哪一个，因此必须确保index值不重复。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [FP16 scatter 归约逐次回写放大相消误差](../../../../../runbooks/precision/low_precision_scatter_reduction_needs_fp32_accumulator.md)（`exemplifies`）：asc_scatter 与《FP16 scatter 归约逐次回写放大相消误差》的实质衔接是：废弃 asc_scatter 的现行 C/基础/Reg Scatter 是迁移路径；三张故障卡直接约束 indices 形状、重复地址归约和写冲突。
- [Scatter 非散射维可缩小，更新量须按 indices 计算](../../../../../runbooks/precision/scatter_update_count_must_follow_indices_shape.md)（`exemplifies`）：asc_scatter 与《Scatter 非散射维可缩小，更新量须按 indices 计算》的实质衔接是：废弃 asc_scatter 的现行 C/基础/Reg Scatter 是迁移路径；三张故障卡直接约束 indices 形状、重复地址归约和写冲突。
- [重复目标随机写丢失 — 在 UB 内按序合并后 DMA 写回](../../../../../runbooks/precision/repeated_overwrite_updates_need_ordered_ub_merge.md)（`exemplifies`）：asc_scatter 与《重复目标随机写丢失 — 在 UB 内按序合并后 DMA 写回》的实质衔接是：废弃 asc_scatter 的现行 C/基础/Reg Scatter 是迁移路径；三张故障卡直接约束 indices 形状、重复地址归约和写冲突。
- [Scatter](../../../basic_api/memory_vector_compute/scatter_gather/scatter_isasi.md)（`related`）：asc_scatter 与《Scatter》的实质衔接是：废弃 asc_scatter 的现行 C/基础/Reg Scatter 是迁移路径；三张故障卡直接约束 indices 形状、重复地址归约和写冲突。
- [ScatterDiscrete](../../../basic_api/reg_vector_compute/reg_data_store/scatter_discrete.md)（`related`）：ScatterDiscrete 与《asc_scatter》的实质衔接是：ScatterDiscrete 与 Gather、C/基础 Scatter 形成索引读写对偶；两张故障卡直接约束重复索引归约和 updates 形状。
- [AscScatter](asc_scatter.md)（`same_topic`）：asc_scatter 与《AscScatter》的实质衔接是：废弃 asc_scatter 的现行 C/基础/Reg Scatter 是迁移路径；三张故障卡直接约束 indices 形状、重复地址归约和写冲突。
<!-- cannbot:related:end -->
