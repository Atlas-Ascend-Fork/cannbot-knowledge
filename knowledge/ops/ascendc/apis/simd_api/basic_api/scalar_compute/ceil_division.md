---
type: API
title: CeilDivision
description: 计算两个整数num1和num2相除后向上取整结果。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/CeilDivision.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# CeilDivision

计算两个整数num1和num2相除后向上取整结果。

参数：num1: 参数1，被除数。；num2: 参数2，除数。

约束：- 当num2为0时，结果为0。
- 该接口仅支持在num1和num2为正数场景下使用。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [整数除法的快速算法](../../../../guides/operator_practice/simd_simt_hybrid_optimization/instruction_optimization/fast_integer_division.md)（`explains`）：CeilDivision 与《整数除法的快速算法》的实质衔接是：CeilDivision 与 CeilDiv 执行整数向上整除，快速除法与 SIMT divide 接口提供实现和舍入边界，标量计算页说明 device 使用域。
- [Fdividef](../../../simt_api/math_functions/float_math_functions/fdividef.md)（`related`）：CeilDivision 与《Fdividef》的实质衔接是：CeilDivision 与 CeilDiv 执行整数向上整除，快速除法与 SIMT divide 接口提供实现和舍入边界，标量计算页说明 device 使用域。
- [__fdividef](../../../simt_api/math_functions/float_math_functions/_fdividef.md)（`related`）：CeilDivision 与《__fdividef》的实质衔接是：CeilDivision 与 CeilDiv 执行整数向上整除，快速除法与 SIMT divide 接口提供实现和舍入边界，标量计算页说明 device 使用域。
- [CeilDiv](../../../utils_api/cpp_stdlib/math_functions/ceil_div.md)（`same_topic`）：CeilDivision 与 ceil_div 都对两个正整数执行向上整除，且除数为零时返回 0；后者额外允许 Host 调用并支持混合整型模板，核心结果合同相同。
- [标量计算](scalar_compute.md)（`same_topic`）：CeilDivision 与《标量计算》的实质衔接是：CeilDivision 与 CeilDiv 执行整数向上整除，快速除法与 SIMT divide 接口提供实现和舍入边界，标量计算页说明 device 使用域。
<!-- cannbot:related:end -->
