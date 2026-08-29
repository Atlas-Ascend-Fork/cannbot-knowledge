---
type: API
title: ReduceMax
description: 对多维向量在指定维度求最大值，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceMax_interface/ReduceMax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceMax

对多维向量在指定维度求最大值。定义指定计算维度为R轴（Reduce轴），非指定维度为A轴（Normal轴）。支持指定第一维或最后一维进行reduce。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceMaxMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [indexer / 块量化 AscendC kernel 的非有限值 (NaN/Inf) 污染防护](../../../../../../../model/inference/runbooks/precision/precision_nonfinite_nan_inf_quant_indexer_kernel.md)（`exemplifies`）：动态 per-block 量化的每块 scale = 块内 `max(｜x｜)`。；对多维向量在指定维度求最大值。定义指定计算维度为R轴（Reduce轴），非指定维度为A轴（Normal轴）。支持指定第一维或最后一维进行reduce。模板参数T支持half/float，pattern指定reduce模式。；API 页补齐 runbook 中块 scale 规约所调用的 ReduceMax 维度与类型合同。
- [GetReduceMaxMaxMinTmpSize](get_reduce_max_max_min_tmp_size.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceMaxMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。；host侧Tiling接口，用于获取ReduceMax接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。ReduceMax 明确要求以 GetReduceMaxMaxMinTmpSize 决定临时空间，目标卡则定义该 Host 查询的上下界输出，二者构成 Host Tiling 到 Kernel 归约调用的资源配置链。
<!-- cannbot:related:end -->
