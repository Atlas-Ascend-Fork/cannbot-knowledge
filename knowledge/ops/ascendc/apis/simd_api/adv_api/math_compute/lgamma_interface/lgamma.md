---
type: API
title: Lgamma
description: 按元素计算x的gamma函数的绝对值并求自然对数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Lgamma_interface/Lgamma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Lgamma

按元素计算x的gamma函数绝对值的自然对数（lgamma(x) = ln(|gamma(x)|)）。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetLgammaMaxMinTmpSize获取。

模板参数isReuseSource仅在float时生效，true表示允许复用srcTensor内存空间。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetLgammaTmpBufferFactorSize](get_lgamma_tmp_buffer_factor_size.md)（`related`）：factor 查询产生的临时空间容量用于决定 Lgamma kernel 单次可处理元素量，执行接口直接消费该 Tiling 决策。
- [Tgammaf](../../../../simt_api/math_functions/float_math_functions/tgammaf.md)（`related`）：高阶 LocalTensor Lgamma 与 SIMT lgammaf 同为 log-gamma，可按数据路径选择稳定替代。
- [GetLgammaMaxMinTmpSize](get_lgamma_max_min_tmp_size.md)（`same_topic`）：《Lgamma》处理“按元素计算x的gamma函数的绝对值并求自然对数”。《GetLgammaMaxMinTmpSize》明确“在host侧获取Lgamma接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”，可直接用于核对Lgamma Kernel、临时空间查询与标量 lgammaf 的同一计算合同。
- [Lgammaf](../../../../simt_api/math_functions/float_math_functions/lgammaf.md)（`same_topic`）：《Lgamma》处理“按元素计算x的gamma函数的绝对值并求自然对数”。《Lgammaf》明确“获取输入数据x伽马值的绝对值并求自然对数。”，可直接用于核对Lgamma Kernel、临时空间查询与标量 lgammaf 的同一计算合同。
- [Lgamma接口](lgamma_interface.md)（`same_topic`）：《Lgamma》处理“按元素计算x的gamma函数的绝对值并求自然对数”。《Lgamma接口》明确“按元素计算x的gamma函数绝对值的自然对数，并提供临时空间大小获取接口。”，可直接用于核对Lgamma Kernel、临时空间查询与标量 lgammaf 的同一计算合同。
<!-- cannbot:related:end -->
