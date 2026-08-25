---
type: API
title: AscLoad
description: 从UB非32字节对齐的源地址搬运VL大小的数据到矢量数据寄存器。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_load.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoad

reg计算数据搬运接口，支持从UB非32字节对齐的源地址src搬运至矢量数据寄存器，搬运量为VL。 连续搬运时，用户需手动更新src地址。
函数原型：void asc_load(vector_int8_t& dst, __ubuf__ int8_t* src)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCopy](asc_copy.md)（`related`）：AscCopy 与《AscLoad》的实质衔接是：寄存器 AscCopy 在 RegTensor/MaskReg 间搬运；reg load 总览、AscLoad 和矢量 AscCopy 明确其数据域与替代路径。
- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`related`）：《AscLoadalignPostupdate》处理“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”。《AscLoad》明确提供“从UB非32字节对齐的源地址搬运VL大小的数据到矢量数据寄存器。”，其参数、调用或验证步骤直接接入LoadAlign 的地址 post-update、预取/非对齐加载和地址寄存器更新。
- [Load](../../../basic_api/reg_vector_compute/reg_data_load/load.md)（`same_topic`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《AscLoad》明确“从UB非32字节对齐的源地址搬运VL大小的数据到矢量数据寄存器。”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [Reg矢量计算](../../../basic_api/reg_vector_compute/reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《AscLoad》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
<!-- cannbot:related:end -->
