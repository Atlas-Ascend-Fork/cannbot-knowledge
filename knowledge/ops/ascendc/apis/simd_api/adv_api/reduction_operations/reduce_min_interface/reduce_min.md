---
type: API
title: ReduceMin
description: 对一个多维向量在指定的维度求最小值。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2,
  3\)的二维矩阵进行运算，指定在第一维求最小值，输出结果为\[1, 2, 3\]；指定在第二维求最小值，输出结果为\[1, 4\]。 图1 ReduceMin按第一个维度计算示例
  ! 图2 ReduceMin按最后一个维度计算示例 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceMin_interface/ReduceMin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: ['950', a2, a3]
---


# ReduceMin

对多维向量在指定维度求最小值。定义指定计算维度为R轴，非指定维度为A轴。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceMinMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetReduceMinMaxMinTmpSize](get_reduce_min_max_min_tmp_size.md)（`related`）：“host侧Tiling接口，用于获取ReduceMin接口所需的最大和最小临时空间大小”给出焦点端事实；“临时空间大小通过GetReduceMinMaxMinTmpSize获取。”给出候选端事实。GetReduceMinMaxMinTmpSize 卡定义 Host 侧临时空间预算，ReduceMin 卡明确消费该预算，二者形成 Tiling 计算到 Kernel 调用的参数链。
<!-- cannbot:related:end -->
