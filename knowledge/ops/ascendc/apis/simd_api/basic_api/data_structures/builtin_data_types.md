---
type: API
title: 内置数据类型（数据结构）
description: Ascend C提供b8\~b64（8bit\~64bit）四种不同位宽的数据类型，不同位宽对应的数据类型如下表所示。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/builtin_data_types.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 内置数据类型（数据结构）

Ascend C 按位宽提供数据类型：b8 含 int8_t/uint8_t；b16 含 int16_t/uint16_t/half/bfloat16_t；b32 含 int32_t/uint32_t/float；b64 含 int64_t/uint64_t/double。特殊类型：int4b_t（4 位有符号整数）、fp8_e4m3fn_t（FP8 E4M3 格式）、hifloat8_t（HI FLOAT8 格式）。

float32 在当前 AI 处理器中尾数位为 10bits（非标准 IEEE 754 的 23bits）。half 为 IEEE 754 半精度（1 符号 + 5 指数 + 10 尾数）。bfloat16_t 为 BFLOAT16（1 符号 + 8 指数 + 7 尾数）。各数据类型间转换规则参考精度转换。

<!-- cannbot:related:start -->
## 相关

- [精度转换（数据结构）](precision_conversion.md)（`related`）：精度转换（数据结构） 与《内置数据类型（数据结构）》的实质衔接是：本卡给出跨类型舍入、饱和与尾数损失规则；SIMT、Memory/Reg Cast 总览和具体 f32→s64 失败分别把这些规则落实到模式选择、数据宽度与编译约束。
- [RegTensor](../reg_vector_compute/register_data_types/reg_tensor.md)（`same_topic`）：RegTensor 与《内置数据类型（数据结构）》的实质衔接是：RegTensor 是 256B VL 的 VF 内基本单元；MaskReg/AddrReg/非对齐状态、内置类型和跨 VF/错误类型案例直接限定 lane、寿命和模板参数。
<!-- cannbot:related:end -->
