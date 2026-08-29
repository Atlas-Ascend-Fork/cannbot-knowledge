---
type: API
title: Tan
description: 按元素对输入数据做正切函数计算，输入值域需在限定范围内。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Tan_interface/Tan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Tan

按元素做正切函数计算，基于泰勒展开式实现（涉及伯努利数）。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetTanMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：输入数据限制在(-65504.0, 65504.0)范围内；不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetTanMaxMinTmpSize](get_tan_max_min_tmp_size.md)（`related`）：提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetTanMaxMinTmpSize获取。；host侧Tiling接口，用于获取Tan接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；Kernel 侧重载明确把临时空间容量交给 GetTanMaxMinTmpSize，Host 侧查询再把容量作为 Tiling 参数回传，闭合 Tan 的分块与 buffer 规划。
- [GetTanTmpBufferFactorSize](get_tan_tmp_buffer_factor_size.md)（`related`）：获取Tan接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetTanMaxMinTmpSize获取。；factor helper 从可用空间反推 Tan 单次规模，Tan 卡给出 buffer 与 calCount 重载，二者用于同一 kernel 的 Tiling 和调用组装。
<!-- cannbot:related:end -->
