---
type: API
title: Abs
description: 单目矢量计算接口，对输入tensor按元素取绝对值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Abs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Abs

单目矢量计算接口，按元素取绝对值。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = |src_i|。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Abs 原地取绝对值后量化丢符号致 int8 坍缩](../../../../../runbooks/precision/abs_inplace_overwrites_signed_source_before_quant.md)（`exemplifies`）：Abs 与《Abs 原地取绝对值后量化丢符号致 int8 坍缩》的衔接是：这些卡分别给出 Abs 在 Reg、C Reg、C Vector 路径上的同一绝对值语义；原地覆盖时符号位丢失案例是该操作的直接别名风险。
- [AscendC::Abs 规范化 NaN payload 致逐位验收误报](../../../../../runbooks/precision/ascendc_abs_nan_payload.md)（`exemplifies`）：Abs API 是实测规范化 FP16 NaN payload 的直接执行接口；非 NaN 逐位一致而 NaN 只需验证仍为 NaN 且清符号位。
- [Abs](../../reg_vector_compute/basic_arithmetic/abs.md)（`same_topic`）：Abs 与《Abs》的衔接是：这些卡分别给出 Abs 在 Reg、C Reg、C Vector 路径上的同一绝对值语义；原地覆盖时符号位丢失案例是该操作的直接别名风险。
- [AscAbs](../../../c_api/reg/arithmetic_compute/asc_abs.md)（`same_topic`）：Abs 与《AscAbs》的衔接是：这些卡分别给出 Abs 在 Reg、C Reg、C Vector 路径上的同一绝对值语义；原地覆盖时符号位丢失案例是该操作的直接别名风险。
- [AscAbs](../../../c_api/vector_compute/asc_abs.md)（`same_topic`）：Abs 与《AscAbs》的衔接是：这些卡分别给出 Abs 在 Reg、C Reg、C Vector 路径上的同一绝对值语义；原地覆盖时符号位丢失案例是该操作的直接别名风险。
<!-- cannbot:related:end -->
