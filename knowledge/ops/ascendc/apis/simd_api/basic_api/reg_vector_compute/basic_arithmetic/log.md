---
type: API
title: Log
description: 根据mask逐元素对源操作数求自然对数（以e为底），将结果写入目的操作数。功能与Ln接口等价，命名遵循C/C++标准库log()约定。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Log.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Log

根据mask逐元素对源操作数求自然对数（以e为底），将结果写入目的操作数。功能与Ln接口等价，命名遵循C/C++标准库log()约定。

头文件路径："basic_api/reg_compute/kernel_reg_compute_vec_unary_intf.h"。 该接口根据mask逐元素对源操作数求自然对数，将结果写入目的操作数。计算公式如下：

本接口组包含 Ln, MaskMergeMode, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscLog](../../../c_api/vector_compute/asc_log.md)（`related`）：Reg Log 在 MaskReg 控制下对寄存器逐元素求自然对数，和 AscLog 的 UB 指针 count 模式形成按数据驻留位置的接口选择。
- [Log](../../../adv_api/math_compute/log_interface/log.md)（`related`）：两者计算同一自然对数，但分别面向 LocalTensor 高阶接口和 RegTensor VF 接口；Reg 版为无需高阶临时空间的不同实现路径。
- [Log接口](../../../adv_api/math_compute/log_interface/log_interface.md)（`related`）：高阶 Log 作用于 LocalTensor 并管理临时空间，Reg Log 直接作用寄存器并用 mask；同为自然对数时可按编程层级和融合需求选择。
- [Ln](ln.md)（`same_topic`）：Ln 与《Log》的实质衔接是：Ln 与 Log 都在 RegTensor 上按 mask 求自然对数；Log 采用标准库命名，是正文明确的等价入口，而 Log10/Log2 底数不同。
- [Log2](log2.md)（`same_topic`）：《Log2》说明根据mask对源操作数逐元素求以2为底的对数，将结果写入目的操作数。；《Log》说明根据mask逐元素对源操作数求自然对数（以e为底），将结果写入目的操作数。功能与Ln接口等价，命名遵循C/C++标准库log()约定。。二者在Reg Log2与Ln、Log/Log10共享对数语义但底数不同，选择时必须区分结果定义上存在可执行的直接衔接。
<!-- cannbot:related:end -->
