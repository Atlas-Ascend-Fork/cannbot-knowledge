---
type: API
title: Cosh
description: 按元素做双曲余弦函数计算
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Cosh_interface/Cosh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Cosh

按元素做双曲余弦函数计算。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetCoshMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetCoshMaxMinTmpSize](get_cosh_max_min_tmp_size.md)（`related`）：Cosh 卡明确“临时空间大小通过GetCoshMaxMinTmpSize获取。”；Host Tiling 卡说明“host侧Tiling接口，用于获取Cosh接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”，二者形成 Cosh 临时空间的 Host 计算到 Kernel 使用链，但主 API 的双曲余弦计算与 helper 的容量规划并非同一主题。
- [GetCoshTmpBufferFactorSize](get_cosh_tmp_buffer_factor_size.md)（`same_topic`）：“获取Cosh接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuffer表示额外临时空间大小（字节）。”与“提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetCoshMaxMinTmpSize获取。”提供双方正文证据。factor 接口把固定可用缓冲换算为单次 Cosh 元素数，Cosh 卡给出显式 sharedTmpBuffer 与 calCount 重载；两端可共同确定分块大小和传入的计算元素数。
<!-- cannbot:related:end -->
