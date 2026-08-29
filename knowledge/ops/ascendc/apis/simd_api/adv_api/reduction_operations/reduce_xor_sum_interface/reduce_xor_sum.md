---
type: API
title: ReduceXorSum
description: 对元素执行按位异或并归约求和；int16 结果溢出时饱和为 -32768 或 32767。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceXorSum_interface/ReduceXorSum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceXorSum

对多维向量按指定维度进行异或求和归约。定义指定计算维度为R轴，非指定维度为A轴。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceXorSumMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetReduceXorSumMaxMinTmpSize](get_reduce_xor_sum_max_min_tmp_size.md)（`related`）：焦点卡要求“isReuseSource与ReduceXorSum接口保持一致”，候选卡定义“对多维向量按指定维度进行异或求和归约。”；Host 侧临时空间计算的复用参数必须与 Kernel 侧 ReduceXorSum 调用一致。
<!-- cannbot:related:end -->
