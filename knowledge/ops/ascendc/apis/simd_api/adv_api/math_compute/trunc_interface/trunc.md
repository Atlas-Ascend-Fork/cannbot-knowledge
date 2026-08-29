---
type: API
title: Trunc
description: 按元素做浮点数截断，即向零取整操作。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Trunc_interface/Trunc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Trunc

按元素做浮点数截断，即向零取整操作（Trunc(3.9)=3, Trunc(-3.9)=-3）。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetTruncMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetTruncMaxMinTmpSize](get_trunc_max_min_tmp_size.md)（`same_topic`）：“临时空间大小通过GetTruncMaxMinTmpSize获取”与“host侧Tiling接口，用于获取Trunc接口所需的最大和最小临时空间大小”明确了 Trunc 的 Host Tiling 到 Kernel 临时空间调用链。
- [GetTruncTmpBufferFactorSize](get_trunc_tmp_buffer_factor_size.md)（`same_topic`）：获取Trunc接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；按元素做浮点数截断，即向零取整操作（Trunc(3.9)=3, Trunc(-3.9)=-3）。模板参数T支持half/float。；factor 查询依据固定空间推导 Trunc 单次 calCount，计算卡以该 calCount 对 half 或 float 执行向零取整。
<!-- cannbot:related:end -->
