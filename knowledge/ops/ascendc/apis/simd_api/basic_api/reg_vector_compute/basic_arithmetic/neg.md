---
type: API
title: Neg
description: 根据mask对源操作数srcReg逐元素取相反数，将结果写入目的操作数dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Neg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Neg

该接口用于根据mask对输入数据srcReg进行取相反数操作，将结果写入dstReg。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_unary_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；U: 源操作数和目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；mask(输入): 源操作数中元素有效性的指示，详细说明请参考MaskReg。

支持数据类型：int8_t、int16_t、half、int32_t、float、int64_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscNeg](../../../c_api/reg/arithmetic_compute/asc_neg.md)（`related`）：AscNeg 与《Neg》的实质衔接是：AscNeg 的 C++/Vector 入口执行算术取负，AscNot 是按位取反的近名反例，可防止把数值负号与 bitwise NOT 混用。
- [Neg](../../memory_vector_compute/basic_arithmetic/neg_isasi.md)（`related`）：“Neg”处理根据mask对源操作数srcReg逐元素取相反数，将结果写入目的操作数dstReg。；“Neg”明确单目矢量计算接口，对输入tensor按元素取相反数。。实质衔接：Reg C++ Neg 与 AscNeg 共享 mask/寄存器逐元素取反契约，Memory Neg 则给出 Tensor 路径的等价选择。
<!-- cannbot:related:end -->
