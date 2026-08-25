---
type: API
title: ReduceProd
description: 对一个多维向量在指定的维度求积。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2,
  3\)的二维矩阵进行运算，指定在第一维求乘积，输出结果为\[4, 10, 18\]；指定在第二维求乘积，输出结果为\[6, 120\]。 图1 ReduceProd按第一个维度计算示例
  ! 图2 ReduceProd按最后一个维度计算示例 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceProd_interface/ReduceProd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceProd

对多维向量按指定维度进行连乘归约。定义指定计算维度为R轴，非指定维度为A轴。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceProdMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetReduceProdMaxMinTmpSize](get_reduce_prod_max_min_tmp_size.md)（`same_topic`）：GetReduceProdMaxMinTmpSize 与《ReduceProd》的实质衔接是：GetReduceProdMaxMinTmpSize 的 max/min 结果直接约束 ReduceProd 的 sharedTmpBuffer，isReuseSource 也必须与实际 ReduceProd 调用保持一致。
- [ReduceProd接口](reduce_prod_interface.md)（`same_topic`）：函数页给出 ReduceProd 的 shape、dtype 和调用参数，是总览页对应的实际乘积归约。
<!-- cannbot:related:end -->
