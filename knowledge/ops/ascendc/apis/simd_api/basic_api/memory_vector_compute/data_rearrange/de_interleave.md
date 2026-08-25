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

- [B16 交错 DINTLV 成对归零 — 转 fp32 后重排](../../../../../runbooks/precision/b16_interleave_compute_should_promote_to_b32_layout.md)（`exemplifies`）：DeInterleave：DeInterleave 的双输出偶/奇 lane 契约可由另一编程接口和逆操作 Interleave 对照，dst0 偶 lane runbook直接验证最易写反的输出约定，b16卡限定重排位宽风险。 目标卡《B16 交错 DINTLV 成对归零 — 转 fp32 后重排》补充：B16 直接解交错经 Cast 后 lane 对不齐；先转连续 fp32 UB 再走 DINTLV_B32。
- [DeInterleave 两路写反——按偶索引到 dst0 修正](../../../../../runbooks/precision/deinterleave_dst0_is_even_lane_output.md)（`exemplifies`）：DeInterleave：DeInterleave 的双输出偶/奇 lane 契约可由另一编程接口和逆操作 Interleave 对照，dst0 偶 lane runbook直接验证最易写反的输出约定，b16卡限定重排位宽风险。 目标卡《DeInterleave 两路写反——按偶索引到 dst0 修正》补充：Reg 交织拆分把 dst0/dst1 接反会让 interleaved 路线整行错；按 dst0=偶索引、dst1=奇索引接线。
- [AscDeintlv](../../../c_api/reg/data_rearrange/asc_deintlv.md)（`related`）：DeInterleave：DeInterleave 的双输出偶/奇 lane 契约可由另一编程接口和逆操作 Interleave 对照，dst0 偶 lane runbook直接验证最易写反的输出约定，b16卡限定重排位宽风险。 目标卡《AscDeintlv》补充：将src0和src1中的元素解交织存入dst0和dst1，提供矢量数据解交织和掩码解交织两种模式，仅在AIV上生效。
- [AscLoadalignDeintlvPostupdate](../../../c_api/reg/reg_load/asc_loadalign_deintlv_postupdate.md)（`related`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《DeInterleave》具体提供“将两个源操作数中的元素解交织存入两个结果操作数中，支持双输入和单输入两种模式。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [Interleave](interleave.md)（`related`）：Interleave 将两路数据交错合并，DeInterleave 按偶/奇 lane 还原两路，是可逆排布链的正反操作。
- [DeInterleave](../../reg_vector_compute/data_reorder/de_interleave.md)（`same_topic`）：DeInterleave：DeInterleave 的双输出偶/奇 lane 契约可由另一编程接口和逆操作 Interleave 对照，dst0 偶 lane runbook直接验证最易写反的输出约定，b16卡限定重排位宽风险。 目标卡《DeInterleave》补充：对寄存器源操作数srcReg0和srcReg1中的元素进行解交织，存入结果寄存器dstReg0和dstReg1中。
- [DeInterleave](../../reg_vector_compute/mask_reg_compute/de_interleave.md)（`same_topic`）：DeInterleave：DeInterleave 的双输出偶/奇 lane 契约可由另一编程接口和逆操作 Interleave 对照，dst0 偶 lane runbook直接验证最易写反的输出约定，b16卡限定重排位宽风险。 目标卡《DeInterleave》补充：将源操作数src0和src1中的元素解交织存入目的操作数dst0和dst1中。
<!-- cannbot:related:end -->
