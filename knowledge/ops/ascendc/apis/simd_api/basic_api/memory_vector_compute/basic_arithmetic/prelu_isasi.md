---
type: API
title: Prelu
description: 双目矢量计算接口，src0非负时直接输出，否则输出src0与src1的乘积。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Prelu_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Prelu

单目矢量计算接口，按元素计算 PReLU 激活。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = max(0, src_i) + alpha * min(0, src_i)。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [AscPrelu](../../../c_api/reg/arithmetic_compute/asc_prelu.md)（`same_topic`）：《AscPrelu》说明实现PReLU激活函数，源操作数src0大于0时直接写入dst，否则将src0与src1相乘后写入dst。；《Prelu》说明双目矢量计算接口，src0非负时直接输出，否则输出src0与src1的乘积。。二者在AscPrelu和Reg/Memory Prelu共享逐元素双输入负半轴乘法，LeakyReLU则是标量斜率特例上存在可执行的直接衔接。
- [LeakyRelu](leaky_relu.md)（`same_topic`）：LeakyRelu 与《Prelu》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [Prelu](../../reg_vector_compute/basic_arithmetic/prelu.md)（`same_topic`）：《Prelu》明确“实现PReLU激活函数，源操作数srcReg0大于0的元素直接写入目的操作数，否则与srcReg1对应元素相乘后写入。”；它与《Prelu》的“双目矢量计算接口，src0非负时直接输出，否则输出src0与src1的乘积。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
