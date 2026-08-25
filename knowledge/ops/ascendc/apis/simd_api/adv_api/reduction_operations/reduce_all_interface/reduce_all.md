---
type: API
title: ReduceAll
description: 对一个多维向量在指定的维度求逻辑与。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2,
  3\)的二维矩阵进行运算，指定在第一维求逻辑与，输出结果为\[1, 0, 0\]；指定在第二维求逻辑与，输出结果为\[0, 0\]。 图1 ReduceAll按第一个维度计算示例
  ! 图2 ReduceAll按最后一个维度计算示例 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceAll_interface/ReduceAll.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceAll

对多维向量按指定维度进行逻辑与归约。定义指定计算维度为R轴，非指定维度为A轴。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceAllMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [ReduceAny](../reduce_any_interface/reduce_any.md)（`related`）：ReduceAny 与 ReduceAll 仅逻辑谓词不同，是判断“全部为真”还是“至少一个为真”的直接接口选型。
- [GetReduceAllMaxMinTmpSize](get_reduce_all_max_min_tmp_size.md)（`same_topic`）：焦点处理ReduceAll 临时空间上下界与 ReduceAll 执行接口；ReduceAll正文说明“对一个多维向量在指定的维度求逻辑与。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2, 3\)的二维矩阵进行运算，指定在第一维求逻辑与，输出结果为\[1, 0, 0\]；指定在第二维求逻辑与，输出结果为\[0, 0”。候选消费该查询结果或定义同一 ReduceAll workspace 契约。
- [ReduceAll接口](reduce_all_interface.md)（`same_topic`）：ReduceAll说明对一个多维向量在指定的维度求逻辑与。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2, 3\)的二维矩阵进行运算，指定在第一维求逻辑与，输出结果为\[1, 0, 0\]；指定在第二维求逻辑与，输出结果为\[0, 0\]。 图1 ReduceAll按第一个维度计算示例 ! 图2 ReduceAll按最后一个维度计算示例 !。
<!-- cannbot:related:end -->
