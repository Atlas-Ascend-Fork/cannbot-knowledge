---
type: API
title: DeInterleave
description: 将两个源操作数中的元素解交织存入两个结果操作数中，支持双输入和单输入两种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_rearrange_ISASI/DeInterleave.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# DeInterleave

将两个源操作数中的元素解交织存入两个结果操作数中，支持双输入和单输入两种模式。

给定源操作数src0和src1，将src0和src1中的元素解交织存入结果操作数dst0和dst1中。解交织排列方式如下图所示，其中每个方格代表一个元素。

本接口属于 UB 矢量计算数据重排接口。

参数说明：T：操作数数据类型。；dst0/dst1：输出 目的操作数。类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。LocalTensor的起始地址需要32字节对齐。；src/src0/src1：输入 源操作数。类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。LocalTensor的起始地址需要32字节对齐。源操作数的数据类型需要与目的操作数保持一致。；count：输入 输入/输出数据元素个数，dst0/dst1/src0/src1长度大小为count。count必须为偶数。；srcCount：输入 输入数据元素个数，两个输出的大小都为输入的一半。srcCount必须为偶数。

约束：不支持源操作数与目的操作数地址重叠。

<!-- cannbot:related:start -->
## 相关

- [DeInterleave 两路写反——按偶索引到 dst0 修正](../../../../../runbooks/precision/deinterleave_dst0_is_even_lane_output.md)（`exemplifies`）：“在变量命名与 API 目标顺序之间建立一一对应：`qE` 必须放在 `dst0`，`qO` 必须放在 `dst1`。以下为轨迹逐字恢复的完整 `ProcessOneTile` before/after；唯一语义修复是 `DeInterleave` 两个目标的顺序。”与“将两个源操作数中的元素解交织存入两个结果操作数中，支持双输入和单输入两种模式。”提供双方正文证据。精度 runbook 通过调整 DeInterleave 的 dst0/dst1 顺序修复偶奇流接反，API 卡定义该接口可按单输入或双输入解交织到两路输出。
- [Interleave](interleave.md)（`related`）：将两个源操作数中的元素解交织存入两个结果操作数中，支持双输入和单输入两种模式。；将两个源操作数中的元素交织存入两个结果操作数中，要求元素个数为偶数。。DeInterleave 把交织输入拆成两路，Interleave 把两路重新交织；二者在成对数据重排流水中互为拆分与重组步骤，数据顺序合同直接衔接。
<!-- cannbot:related:end -->
