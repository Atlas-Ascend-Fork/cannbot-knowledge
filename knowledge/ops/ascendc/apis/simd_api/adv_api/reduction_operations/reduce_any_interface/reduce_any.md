---
type: API
title: ReduceAny
description: 对一个多维向量在指定的维度求逻辑或。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2,
  3\)的二维矩阵进行运算，指定在第一维求逻辑或，输出结果为\[1, 0, 1\]；指定在第二维求逻辑或，输出结果为\[1, 1\]。 图1 ReduceAny按第一个维度计算示例
  ! 图2 ReduceAny按最后一个维度计算示例 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceAny_interface/ReduceAny.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceAny

对多维向量按指定维度进行逻辑或归约。定义指定计算维度为R轴，非指定维度为A轴。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceAnyMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [ReduceAll](../reduce_all_interface/reduce_all.md)（`related`）：ReduceAny 与 ReduceAll 仅逻辑谓词不同，是判断“全部为真”还是“至少一个为真”的直接接口选型。
- [GetReduceAnyMaxMinTmpSize](get_reduce_any_max_min_tmp_size.md)（`same_topic`）：ReduceAny 使用该接口规划逻辑 OR 归约的临时空间。
- [ReduceAny接口](reduce_any_interface.md)（`same_topic`）：ReduceAny说明对一个多维向量在指定的维度求逻辑或。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2, 3\)的二维矩阵进行运算，指定在第一维求逻辑或，输出结果为\[1, 0, 1\]；指定在第二维求逻辑或，输出结果为\[1, 1\]。 图1 ReduceAny按第一个维度计算示例 ! 图2 ReduceAny按最后一个维度计算示例 !。
<!-- cannbot:related:end -->
