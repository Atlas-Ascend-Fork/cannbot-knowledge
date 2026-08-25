---
type: API
title: AscLoadalignDeintlv
description: 从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_deintlv.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignDeintlv

asc_loadalign_deintlv用于从UB中读取以32B对齐地址为起始位置的连续2 x VL长度数据。数据按元素类型宽度进行解释，在Load过程中完成解交织后，分别写入两个目的矢量数据寄存器。 以float数据类型、Ascend 950PR/Ascend 950DT产品为例，若VL = 256B，则单次操作覆盖64个float元素。调用asc_loadalign_deintlv后，数据从UB到Reg的排布如下图所示。 > 提示：
函数原型：asc_loadalign_deintlv按源地址的寻址方式分为以下三类接口：[基址寻址接口](#base-addressing-api)、[标量偏移寻址接口](#base-scalar-offset-api)、[地址寄存器偏移寻址接口](#base-register-indexed-api)。支持的数据类型请参见[数据类型](#data-type)章节。
返回值：无。
约束：对于基址寻址接口，src必须为32B对齐地址，且访问范围不能超过UB有效地址上界减去2 x VL。；对于标量偏移寻址接口和地址寄存器偏移寻址接口，实际访问地址必须为32B对齐，且访问范围不能超过UB有效地址上界减去2 x VL。；使用地址寄存器偏移寻址接口时，需要先通过asc_update_addr_reg完成地址寄存器初始化。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignDeintlvPostupdate](asc_loadalign_deintlv_postupdate.md)（`same_topic`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《AscLoadalignDeintlv》具体提供“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
<!-- cannbot:related:end -->
