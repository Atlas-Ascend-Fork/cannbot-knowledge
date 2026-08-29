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

- [DeInterleave](de_interleave.md)（`related`）：将两个源操作数中的元素解交织存入两个结果操作数中，支持双输入和单输入两种模式。；将两个源操作数中的元素交织存入两个结果操作数中，要求元素个数为偶数。。DeInterleave 把交织输入拆成两路，Interleave 把两路重新交织；二者在成对数据重排流水中互为拆分与重组步骤，数据顺序合同直接衔接。
- [GroupedDynamicMxQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/grouped_dynamic_mx_quant_950.md)（`related`）：“｜ Scale layout ｜ `Duplicate`+`Interleave` ｜ calcBuf ｜ mxScaleQueue ｜ 两个 32-row scale 平面 ｜ 奇数平面补零；行尾按实际 `blockCount` ｜”；“将两个源操作数中的元素交织存入两个结果操作数中，要求元素个数为偶数。”。operator 用 Interleave 把成对 E8M0 scale 平面排成 mxscale 尾维 2，奇数平面补零正好满足接口偶数约束。
<!-- cannbot:related:end -->
