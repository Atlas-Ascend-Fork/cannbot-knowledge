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

- [Cosh接口](cosh_interface.md)（`same_topic`）：焦点处理Cosh 高阶 API 的计算接口与临时空间计算；Cosh正文说明“按元素做双曲余弦函数计算”。候选分别承担 Cosh 实际计算、workspace 上下界和固定空间容量推算。
- [GetCoshMaxMinTmpSize](get_cosh_max_min_tmp_size.md)（`same_topic`）：GetCoshMaxMinTmpSize说明在host侧获取Cosh接口预留或申请临时空间的最大和最小值，用于Tiling参数传递；对Cosh而言，Cosh 的 Host Tiling 必须在最大/最小临时空间与 factor 参数之间选择，才能推算 Kernel 单次处理量。
- [GetCoshTmpBufferFactorSize](get_cosh_tmp_buffer_factor_size.md)（`same_topic`）：GetCoshTmpBufferFactorSize说明获取Cosh接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量；对Cosh而言，Cosh 的 Host Tiling 必须在最大/最小临时空间与 factor 参数之间选择，才能推算 Kernel 单次处理量。
<!-- cannbot:related:end -->
