---
type: API
title: Digamma
description: 按元素计算x的gamma函数的对数导数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Digamma_interface/Digamma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Digamma

按元素计算x的gamma函数的对数导数（即digamma函数）。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetDigammaMaxMinTmpSize获取。

模板参数isReuseSource仅在float时生效，true表示允许复用srcTensor内存空间。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Lgammaf](../../../../simt_api/math_functions/float_math_functions/lgammaf.md)（`related`）：Lgammaf 与《Digamma》的实质衔接是：Lgammaf 与向量 Lgamma 是同一 log-gamma 任务，Tgamma 给出非对数对应量，Digamma 则给出其导数语义。
- [Tgammaf](../../../../simt_api/math_functions/float_math_functions/tgammaf.md)（`related`）：Digamma 是 log-gamma 的导数，适用于梯度/特殊函数链而非替代 Gamma 值。
- [Digamma接口](digamma_interface.md)（`same_topic`）：Digamma：Digamma 的计算重载直接依赖 host 临时空间上限/下限与 kernel 因子接口，接口页汇总同一组调用契约。 目标卡《Digamma接口》补充：按元素计算x的gamma函数的对数导数（Digamma函数），并提供临时空间大小获取接口。
- [GetDigammaMaxMinTmpSize](get_digamma_max_min_tmp_size.md)（`same_topic`）：Digamma说明按元素计算x的gamma函数的对数导数。
- [GetDigammaTmpBufferFactorSize](get_digamma_tmp_buffer_factor_size.md)（`same_topic`）：GetDigammaTmpBufferFactorSize：该因子接口与 Digamma计算及同名 MaxMinTmpSize共同闭合 host预算公式和 kernel sharedTmpBuffer；接口页给出两种重载与复用约束。 目标卡《Digamma》补充：按元素计算x的gamma函数的对数导数
<!-- cannbot:related:end -->
