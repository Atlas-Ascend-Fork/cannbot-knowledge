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

- [GetDigammaMaxMinTmpSize](get_digamma_max_min_tmp_size.md)（`related`）：“host侧Tiling接口，用于获取Digamma接口所需的最大和最小临时空间大小”；“临时空间大小通过GetDigammaMaxMinTmpSize获取”。前者生产临时空间上下界，Digamma 的 sharedTmpBuffer 重载直接消费该规划结果。
- [GetDigammaTmpBufferFactorSize](get_digamma_tmp_buffer_factor_size.md)（`related`）：“获取Digamma接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。”提供固定 buffer 的反向容量公式；“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。”说明 Digamma 的临时空间入口，联合阅读可从已有 UB 容量推导可处理元素数。
<!-- cannbot:related:end -->
