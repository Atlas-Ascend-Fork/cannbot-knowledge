---
type: API
title: Interleave
description: 将两个源操作数中的元素交织存入两个结果操作数中，要求元素个数为偶数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_rearrange_ISASI/Interleave.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Interleave

将两个源操作数中的元素交织存入两个结果操作数中，要求元素个数为偶数。

给定源操作数src0和src1，将src0和src1中的元素交织存入结果操作数dst0和dst1中。交织排列方式如下图所示，其中每个方格代表一个元素。

本接口属于 UB 矢量计算数据重排接口。

参数说明：T：操作数数据类型。；dst0/dst1：输出 目的操作数。类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。LocalTensor的起始地址需要32字节对齐。；src0/src1：输入 源操作数。类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。LocalTensor的起始地址需要32字节对齐。源操作数的数据类型需要与目的操作数保持一致。；count：输入 输入/输出数据元素个数，dst0/dst1/src0/src1长度大小均为count。count必须为偶数。

约束：不支持源操作数与目的操作数地址重叠。

<!-- cannbot:related:start -->
## 相关

- [B16 交错 DINTLV 成对归零 — 转 fp32 后重排](../../../../../runbooks/precision/b16_interleave_compute_should_promote_to_b32_layout.md)（`exemplifies`）：该 runbook 证明 B16 直接交错/解交错会因 DINTLV lane 布局错配成对归零，并给出提升到连续 B32 后重排的已验证边界。
- [DeInterleave 两路写反——按偶索引到 dst0 修正](../../../../../runbooks/precision/deinterleave_dst0_is_even_lane_output.md)（`exemplifies`）：修复链在偶/奇两路 Reg 计算后用 LocalTensor Interleave 重组成输出；它是 DeInterleave 拆分路线的直接逆向布局步骤。
- [DeInterleave](de_interleave.md)（`related`）：Interleave 将两路数据交错合并，DeInterleave 按偶/奇 lane 还原两路，是可逆排布链的正反操作。
- [Interleave](../../reg_vector_compute/data_reorder/interleave.md)（`same_topic`）：Memory Tensor 版本完成同一交织任务，可按数据驻留选择。
<!-- cannbot:related:end -->
