---
type: API
title: GetReduceAllMaxMinTmpSize
description: 在host侧获取ReduceAll接口计算所需的最大和最小临时空间大小，用于选择合适的空间作为Tiling参数传递到kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceAll_interface/GetReduceAllMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetReduceAllMaxMinTmpSize

host侧Tiling接口，用于获取ReduceAll接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetReduceAllMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与ReduceAll接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [ReduceAll](reduce_all.md)（`same_topic`）：焦点处理ReduceAll 临时空间上下界与 ReduceAll 执行接口；ReduceAll正文说明“对一个多维向量在指定的维度求逻辑与。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2, 3\)的二维矩阵进行运算，指定在第一维求逻辑与，输出结果为\[1, 0, 0\]；指定在第二维求逻辑与，输出结果为\[0, 0”。候选消费该查询结果或定义同一 ReduceAll workspace 契约。
- [ReduceAll接口](reduce_all_interface.md)（`same_topic`）：焦点处理ReduceAll 临时空间上下界与 ReduceAll 执行接口；ReduceAll接口正文说明“对多维向量在指定维度求逻辑与，并提供临时空间大小获取接口”。候选消费该查询结果或定义同一 ReduceAll workspace 契约。
<!-- cannbot:related:end -->
