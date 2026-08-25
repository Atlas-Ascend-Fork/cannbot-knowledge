---
type: API
title: 直方图计算
description: 寄存器侧直方图计算类接口汇总，提供累积直方图与频率直方图两种计算能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/histogram_compute/histogram_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 直方图计算（C API）

直方图计算接口集合，用于对输入数据进行直方图统计。包含asc_cumulative_histogram（累计直方图计算，输出累计频数分布）和asc_frequency_histogram（频数直方图计算，输出各区间频数）。这些接口在Vector Core上执行，适用于图像处理中的直方图均衡化、数据分析中的数据分布统计等场景。使用时需配置区间边界和数据类型等参数，具体约束请参考各接口的详细文档。

<!-- cannbot:related:start -->
## 相关

- [AscCumulativeHistogram](asc_cumulative_histogram.md)（`related`）：“AscCumulativeHistogram”定义：对直方图数据进行累计统计，支持低位和高位两种模式，统计结果在目的寄存器原始数据基础上累加。；“直方图计算”定义：寄存器侧直方图计算类接口汇总，提供累积直方图与频率直方图两种计算能力。。实质衔接：Histograms/AscCumulativeHistogram 都在原 dst 上累加累计统计；FrequencyHistogram 改为频率统计，接口总览明确两种模式选择。
- [Histograms](../../../basic_api/reg_vector_compute/histogram_compute/histograms.md)（`related`）：Histograms说明对直方图数据进行统计，在目的寄存器原始数据上累加源寄存器数据的频率统计或累计统计结果。
- [直方图计算](../../../basic_api/reg_vector_compute/histogram_compute/histogram_compute.md)（`same_topic`）：直方图计算 与《直方图计算》的实质衔接是：Reg 与 C Reg 的直方图概述是同一频数/累积直方图能力在两层 API 的对应入口；接口成员关系由 part_of 处理。
<!-- cannbot:related:end -->
