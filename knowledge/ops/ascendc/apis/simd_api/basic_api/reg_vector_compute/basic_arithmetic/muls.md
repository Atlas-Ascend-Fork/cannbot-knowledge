---
type: API
title: Muls
description: 根据mask对源操作数srcReg每个元素与标量scalarValue求积，将结果写入目的操作数dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Muls.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Muls

矢量内每个元素与标量求积。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_binary_scalar_intf.h"。

参数：T: 矢量目的操作数和源操作数的数据类型。支持的数据类型请参考数据类型。；U: 标量源操作数的数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；S: 目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；scalarValue(输入): 源操作数。 类型为标量。；mask(输入): 源操作数中元素有效性的指示，详细说明请参考MaskReg。

支持数据类型：int16_t、uint16_t、half、int32_t、uint32_t、float、complex32、int64_t、uint64_t、complex64。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMulScalar](../../../c_api/reg/arithmetic_compute/asc_mul_scalar.md)（`related`）：AscMulScalar 是 C Reg API 的对应标量乘接口，可用于从 C++ Reg::Muls 迁移。
- [AscMuls](../../../c_api/reg/arithmetic_compute/asc_muls_deprecated.md)（`related`）：废弃 C AscMuls 的目标能力由 Reg C++ Muls 表达：按 mask 将 RegTensor 与标量相乘，避免继续依赖废弃接口。
- [Mul](mul.md)（`related`）：Mul 的第二操作数是 RegTensor，而 Muls 的第二操作数是 scalar，应按参数形态选择。
- [Muls（灵活标量位置）](../../memory_vector_compute/basic_arithmetic/muls_flexible_scalar.md)（`related`）：Muls（灵活标量位置） 与《Muls》的实质衔接是：灵活标量 Muls 的 scalarTensorIndex、LocalTensor 单点标量和 cyclic-repeat 语义会直接影响广播乘法、量化 scale 与标量位置。
- [Muls](../../memory_vector_compute/basic_arithmetic/muls.md)（`same_topic`）：Muls 的核心契约是“双目矢量标量计算接口，将矢量tensor每个元素与标量求积”；Muls 补充“根据mask对源操作数srcReg每个元素与标量scalarValue求积，将结果写入目的操作数dstReg”。
<!-- cannbot:related:end -->
