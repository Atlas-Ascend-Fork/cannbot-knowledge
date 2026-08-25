---
type: API
title: 基础算术
description: 寄存器侧基础算术类接口汇总，提供abs、add、sub、mul、div、exp、ln、sqrt、relu等逐元素矢量计算能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/arithmetic_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 基础算术

寄存器侧基础算术接口提供逐元素矢量运算。四则运算含asc_add/sub/mul/div及asc_add_scalar/mul_scalar/max_scalar/min_scalar标量变体，asc_addc/subc支持常量加减。
数学函数含asc_exp/ln/sqrt及asc_abs/neg。激活函数含asc_relu/leakyrelu/prelu。比较运算含asc_max/min及标量变体，asc_mull提供长乘。asc_muls已废弃，建议使用asc_mul_scalar替代。

<!-- cannbot:related:start -->
## 相关

- [AscMull](asc_mull.md)（`related`）：《AscMull》说明根据mask对源操作数src0、src1按元素相乘，将乘法结果的低位部分写入dst0，高位（溢出）部分写入dst1。；《基础算术》说明寄存器侧基础算术类接口汇总，提供abs、add、sub、mul、div、exp、ln、sqrt、relu等逐元素矢量计算能力。。二者在AscMull同时产生乘积高低位，只有同样保留溢出位的Mull接口可视为同一运算合同上存在可执行的直接衔接。
- [AscPrelu](asc_prelu.md)（`related`）：《AscPrelu》说明实现PReLU激活函数，源操作数src0大于0时直接写入dst，否则将src0与src1相乘后写入dst。；《基础算术》说明寄存器侧基础算术类接口汇总，提供abs、add、sub、mul、div、exp、ln、sqrt、relu等逐元素矢量计算能力。。二者在AscPrelu和Reg/Memory Prelu共享逐元素双输入负半轴乘法，LeakyReLU则是标量斜率特例上存在可执行的直接衔接。
- [AscSub](asc_sub.md)（`related`）：《AscSub》说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。；《基础算术》说明寄存器侧基础算术类接口汇总，提供abs、add、sub、mul、div、exp、ln、sqrt、relu等逐元素矢量计算能力。。二者在AscSub在Vector、Reg和Memory层实现同一减法，SubC/Relu融合及UB对齐故障给出结果变体和调用边界上存在可执行的直接衔接。
- [Reg矢量计算概述](../../../basic_api/reg_vector_compute/basic_arithmetic/overview.md)（`related`）：两卡覆盖同一 Reg 向量基础算术能力：本卡是 C++ Tensor/Reg 命名空间入口，目标卡汇总 C 指针 API 的 asc_abs/add/sub/mul/div/exp 等对应接口，适合按编程形态选型。
<!-- cannbot:related:end -->
