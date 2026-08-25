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

- [AscReduceMax](../../../c_api/reg/reduce_compute/asc_reduce_max.md)（`same_topic`）：AscReduceMax 与《ReduceMax》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [GetReduceMaxMaxMinTmpSize](get_reduce_max_max_min_tmp_size.md)（`same_topic`）：GetReduceMaxMaxMinTmpSize：该 host 接口专门为 ReduceMax 计算选择 sharedTmpBuffer，ReduceMax 正文中的 isReuseSource/shape 必须与这里的估算入参保持一致。 目标卡《ReduceMax》补充：对多维向量在指定维度求最大值，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
- [ReduceMax](../../../basic_api/memory_vector_compute/reduction_compute/reduce_max.md)（`same_topic`）：高阶 ReduceMax 提供同一最大值归约并封装 shape/workspace。
- [ReduceMax接口](reduce_max_interface.md)（`same_topic`）：ReduceMax说明对多维向量在指定维度求最大值，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
<!-- cannbot:related:end -->
