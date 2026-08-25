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
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceMin

对多维向量在指定维度求最小值。定义指定计算维度为R轴，非指定维度为A轴。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceMinMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [A5 循环内 ReduceMin 取索引致 vector core 异常](../../../../../runbooks/precision/a5_reducemin_vector_core.md)（`exemplifies`）：Runbook 给出 ReduceMin(calIndex=true) 在 3510 循环调用时的 error 264、调用次数相关性与 Scalar 替代验证，为 API 卡补充一个经过 A/B 验证的运行边界。
- [AscDatablockReduceMin](../../../c_api/vector_compute/asc_datablock_reduce_min.md)（`related`）：高阶 ReduceMin 封装 shape 与 workspace，适合整 tensor 归约；本接口适合显式 DataBlock 编程。
- [AscReduceMin](../../../c_api/reg/reduce_compute/asc_reduce_min.md)（`related`）：高阶 ReduceMin 封装 shape/workspace，适合整 tensor；Reg API 适合 VF 内显式寄存器归约。
- [AscReduceMinDatablock](../../../c_api/reg/reduce_compute/asc_reduce_min_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《ReduceMin》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [GetReduceMinMaxMinTmpSize](get_reduce_min_max_min_tmp_size.md)（`same_topic`）：GetReduceMinMaxMinTmpSize 与《ReduceMin》的衔接是：ReduceMinMax 临时空间查询为 ReduceMin/ReduceMax 归约接口计算最小与最大工作区，属于调用前必须完成的资源契约。
- [ReduceMin](../../../basic_api/memory_vector_compute/reduction_compute/reduce_min.md)（`same_topic`）：ReduceMin 与《ReduceMin》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [ReduceMin接口](reduce_min_interface.md)（`same_topic`）：函数页给出 ReduceMin 的参数、shape 和调用约束，是接口总览对应的实际高阶归约操作。
<!-- cannbot:related:end -->
