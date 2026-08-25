---
type: API
title: ReduceMean
description: 对多维向量按指定维度求平均值，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceMean_interface/ReduceMean.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceMean

对多维向量按指定维度求平均值。定义指定计算维度为R轴，非指定维度为A轴。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceMeanMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Mean](../mean_interface/mean.md)（`related`）：ReduceMean 面向更一般的归约参数，而 Mean 固定沿末轴、最多二维；二者的差异直接用于接口选型。
- [GetReduceMeanMaxMinTmpSize](get_reduce_mean_max_min_tmp_size.md)（`same_topic`）：GetReduceMeanMaxMinTmpSize：该 host估算的shape/typeSize/isReuseSource必须与 ReduceMean kernel调用一致；ReduceMean接口页汇总同一 sharedTmpBuffer契约。 目标卡《ReduceMean》补充：对多维向量按指定维度求平均值，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
- [ReduceMean接口](reduce_mean_interface.md)（`same_topic`）：ReduceMean说明对多维向量按指定维度求平均值，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
<!-- cannbot:related:end -->
