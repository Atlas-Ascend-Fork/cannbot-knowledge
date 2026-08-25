---
type: API
title: AscXor
description: 根据mask对矢量数据寄存器或掩码寄存器src0和src1执行按位异或操作，结果写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/logic_compute/asc_xor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscXor

asc_xor支持两种接口
- 对矢量数据寄存器操作
    根据mask对矢量数据寄存器src0和src1进行按位异或（^）操作，将结果写入dst。未被mask筛选的位置被置为0。
- 对掩码寄存器操作
    根据mask对两个掩码寄存器src0和src1进行按位异或（^）操作，将结果写入dst。未被mask筛选的位置被置为0。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。；dst(输出): 目的操作数（掩码寄存器）。；src0(输入): 源操作数（掩码寄存器）。；src1(输入): 源操作数（掩码寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：dst中未被mask筛选的位置被置为0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Xor](../../../adv_api/math_compute/xor_interface/xor.md)（`same_topic`）：AscXor 与《Xor》的实质衔接是：高阶 Xor、基础 Reg Xor 和 AscXor 完成同一逐元素异或，差异在 LocalTensor/RegTensor/C Reg 入口和工作区管理。
- [Xor](../../../basic_api/reg_vector_compute/logical_compute/xor.md)（`same_topic`）：AscXor 与《Xor》的实质衔接是：高阶 Xor、基础 Reg Xor 和 AscXor 完成同一逐元素异或，差异在 LocalTensor/RegTensor/C Reg 入口和工作区管理。
- [Xor接口](../../../adv_api/math_compute/xor_interface/xor_interface.md)（`same_topic`）：AscXor 与《Xor接口》的实质衔接是：高阶 Xor、基础 Reg Xor 和 AscXor 完成同一逐元素异或，差异在 LocalTensor/RegTensor/C Reg 入口和工作区管理。
<!-- cannbot:related:end -->
