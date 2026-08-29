---
type: API
title: Matmul Tiling类使用说明
description: Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/Matmul_Tiling_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Matmul Tiling类使用说明

Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。 Matmul Tiling API分为Matmul单核Tiling接口、多核Tiling接口和BatchMatmul Tiling接口，分别用于Matmul单核计算、多核计算和BatchMatmul计算场景。获取Tiling参数的流程如下： 1. 创建一个单核Tiling对象，或多核Tiling对象，或BatchMatmul Tiling对象。

<!-- cannbot:related:start -->
## 相关

- [Matmul算子优化Tiling策略](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md)（`explains`）：优化基本块，选择最优的baseM、baseN、baseK参数，其中baseM、baseN、baseK为Matmul Tiling中的参数。；Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。。调优案例以 baseM/baseN/baseK 改善搬运效率，API 使用页给出获得 TCubeTiling 参数的入口，连接了性能选择与可执行配置步骤。
- [Matmul高阶API开启Tiling全量常量化](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_constant.md)（`explains`）：使用MatmulApiStaticTiling参数替代TCubeTiling变量参数；调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数；连接常量化替代方案与常规动态 Tiling 基线。
- [GetTiling](get_tiling.md)（`related`）：“返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。”；“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。”。使用说明给出创建 Tiling 对象并获取参数的完整调用上下文，焦点返回码决定结果能否继续传入 kernel。
- [SetALayout](set_a_layout.md)（`related`）：“用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。”与“设置A矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A矩阵的Layout轴信息。”提供双方正文证据。通用流程要求先提供矩阵元数据，SetALayout 补充三类 Batch Layout 在 IterateBatch 前必须设置的 B/S/N/G/D 轴信息，形成特殊布局的调用前置条件。
<!-- cannbot:related:end -->
