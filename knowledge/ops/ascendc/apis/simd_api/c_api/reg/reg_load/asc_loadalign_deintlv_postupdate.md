---
type: API
title: AscLoadalignDeintlvPostupdate
description: 从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_deintlv_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignDeintlvPostupdate

asc_loadalign_deintlv_postupdate用于从UB中读取以32B对齐地址src为起始位置的连续2 x VL长度数据。数据按元素类型宽度进行解释，在Load过程中完成解交织后，分别写入两个目的向量寄存器dst0和dst1。 与asc_loadalign_deintlv不同，该接口在完成数据加载后，会对源地址参数src执行后更新操作： 其中，offset的单位为元素个数，实际地址偏移字节数为：offset * sizeof(data_type)。
函数原型：支持的数据类型请参见[数据类型](#data-type)章节。
返回值：无。
约束：src必须为32B对齐地址，且访问范围不能超过UB有效地址上界减去2 x VL，否则可能导致UB越界访问。；在循环中使用本接口时，offset的取值需要保证更新后的src仍满足32B对齐要求。；offset以元素为单位，实际地址步长需要结合源数据类型宽度进行换算。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [DeInterleave 两路写反——按偶索引到 dst0 修正](../../../../../runbooks/precision/deinterleave_dst0_is_even_lane_output.md)（`exemplifies`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《DeInterleave 两路写反——按偶索引到 dst0 修正》具体提供“Reg 交织拆分把 dst0/dst1 接反会让 interleaved 路线整行错；按 dst0=偶索引、dst1=奇索引接线。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [AscDeintlv](../data_rearrange/asc_deintlv.md)（`related`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《AscDeintlv》具体提供“将src0和src1中的元素解交织存入dst0和dst1，提供矢量数据解交织和掩码解交织两种模式，仅在AIV上生效。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [AscUpdateAddrReg](../reg_data_types/asc_update_addr_reg.md)（`related`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《AscUpdateAddrReg》具体提供“更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [DeInterleave](../../../basic_api/memory_vector_compute/data_rearrange/de_interleave.md)（`related`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《DeInterleave》具体提供“将两个源操作数中的元素解交织存入两个结果操作数中，支持双输入和单输入两种模式。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [DeInterleave](../../../basic_api/reg_vector_compute/data_reorder/de_interleave.md)（`related`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《DeInterleave》具体提供“对寄存器源操作数srcReg0和srcReg1中的元素进行解交织，存入结果寄存器dstReg0和dstReg1中。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [DeInterleave](../../../basic_api/reg_vector_compute/mask_reg_compute/de_interleave.md)（`related`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《DeInterleave》具体提供“将源操作数src0和src1中的元素解交织存入目的操作数dst0和dst1中。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [reg数据搬入](reg_load.md)（`related`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《reg数据搬入》具体提供“寄存器侧数据搬入类接口汇总，提供gather、load、loadalign等从UB到矢量数据寄存器的搬运能力。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [AscLoadalignDeintlv](asc_loadalign_deintlv.md)（`same_topic`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《AscLoadalignDeintlv》具体提供“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`same_topic`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscLoadalignDeintlvPostupdate》明确提供“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
<!-- cannbot:related:end -->
