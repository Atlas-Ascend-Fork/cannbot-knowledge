---
type: API
title: OutputShapeDependOnCompute
description: 标识算子输出的shape依赖于计算得到，用于NonZero等计算完成后才能获取输出shape的算子，需在核函数中将实际输出shape写入出参。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/OutputShapeDependOnCompute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OutputShapeDependOnCompute

## 功能说明
标识算子输出的shape是否依赖于计算得到。某些算子，比如NonZero（统计tensor中非零值的个数），计算完成前无法得知算子输出的shape信息，算子计算完成后才能获取。该类算子在原型定义时，需要使用OutputShapeDependOnCompute接口进行标识，同时在算子核函数中将实际输出shape写入到出参中，便于框架侧基于该信息进行输出内存的管理。对应的kernel侧实现请参考输出shape依赖计算的算子kernel实现。
## 函数原型
## 参数说明
无
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
-   只能用于标识算子输出。
-   基于旧版本CANN包（不支持OutputShapeDependOnCompute特性）生成的自定义算子工程，无法兼容OutputShapeDependOnCompute接口。在使用非当前版本CANN包生成的自定义算子工程时，需特别注意兼容性问题。您可以通过查看自定义算子工程下cmake/util/ascendc_impl_build.py中有无output_shape_depend_on_compute字段来确认当前工程是否支持该特性，如果未找到该字段，则需要重新生成自定义算子工程以启用OutputShapeDependOnCompute特性。

<!-- cannbot:related:start -->
## 相关

- [输出shape依赖计算](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/kernel_output_shape_computation.md)（`explains`）：OutputShapeDependOnCompute 只完成原型标记，目标指南给出 kernel 写实际 shape、框架读取并管理输出内存的完整实现合同。
<!-- cannbot:related:end -->
