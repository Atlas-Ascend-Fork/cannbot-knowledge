---
type: API
title: ReduceSum
description: 对多维向量按指定维度进行数据累加，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceSum_interface/ReduceSum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceSum

对多维向量按指定维度进行数据累加。定义指定计算维度为R轴，非指定维度为A轴。支持指定第一维或最后一维进行reduce。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceSumMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 ReduceSum AR 多行归约逐行错](../../../../../runbooks/precision/ascend950_reduce_sum_ar_multibundle_use_per_row.md)（`exemplifies`）：对多维向量按指定维度进行数据累加。定义指定计算维度为R轴，非指定维度为A轴。支持指定第一维或最后一维进行reduce。模板参数T支持half/float，pattern指定reduce模式。；`ReduceSum<float, Pattern::Reduce::AR>` 在 `srcShape={aBundle, rBundle}`（`aBundle>1`）且 `srcInnerPad=true` 时，3510 上的归约实现在多行间做了错误的分割/重排——总体量近似保留但逐行结果错位。。API 卡定义 AR/RA 多维规约合同，runbook 给出 950 上 AR 多行调用的精度失败签名与逐行规约修法。
- [GetReduceSumMaxMinTmpSize](get_reduce_sum_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取ReduceSum接口所需的最大和最小临时空间大小；临时空间大小通过GetReduceSumMaxMinTmpSize获取。。左卡按 ReduceSum 的 shape、dtype 与复用配置返回缓冲范围，右卡明确使用该结果为 sharedTmpBuffer 定容；两端衔接 Host 空间规划与 AR/RA 归约执行。
<!-- cannbot:related:end -->
