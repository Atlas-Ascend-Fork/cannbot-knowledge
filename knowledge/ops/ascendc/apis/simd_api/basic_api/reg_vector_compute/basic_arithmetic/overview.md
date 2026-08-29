---
type: API
title: Reg矢量计算概述
description: 寄存器矢量基本算术运算接口概述，涵盖Abs、Exp、Add、Mul等单目、双目及标量双目运算。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Reg矢量计算概述

寄存器矢量基本算术运算接口概述，涵盖Abs、Exp、Add、Mul等单目、双目及标量双目运算。

头文件路径："basic_api/reg_compute/kernel_reg_compute_vec_unary_intf.h"。 - 对实数类型 对srcReg中的有效元素逐个取绝对值，并将结果写入dstReg对应位置，计算公式如下： - 对复数类型 对srcReg中有效元素逐个取模，并将结果写入dstReg对应位置，计算公式如下： 其中$srcReg_i = \alpha + \beta i$，α为复数的实部，β为复数的虚部。

本接口组包含 Abs, Exp, Ln, Log, Log2。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

约束：当目的操作数和源操作数数据类型不一致时，目的操作数和源操作数不可重叠。；整型数据的计算结果如果超出数据类型的表示范围会采取非饱和截断，比如int8_t类型，srcReg为-128，其绝对值128会被截断成-128。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
