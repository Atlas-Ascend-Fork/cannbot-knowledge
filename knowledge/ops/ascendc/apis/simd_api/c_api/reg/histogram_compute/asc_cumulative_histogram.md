---
type: API
title: AscCumulativeHistogram
description: 对直方图数据进行累计统计，支持低位和高位两种模式，统计结果在目的寄存器原始数据基础上累加。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/histogram_compute/asc_cumulative_histogram.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscCumulativeHistogram

该接口用于对直方图数据进行累计统计。

如下图所示，在低位模式（BIN0）下，目的寄存器dst会统计源寄存器src中落在低位区间[0-127]的数据分布情况；在高位模式（BIN1）下，目的寄存器dst则会统计src中落在高位区间[128-255]的数据分布情况。dst中的第n个元素表示src中从0到n的所有数值在对应区间中出现的总频率。最终，统计结果会在目的寄存器原始数据的基础上进行累加。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。

支持数据类型：uint16_t、uint8_t。

约束：- 当mask位数为0时，对应位置的src源操作数的数值被忽略，dst对应位置数值为忽略该位置src后计算得到的值。
- dst的数据类型为uint16_t，最大值为65535，使用时需注意累加溢出问题。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscFrequencyHistogram](asc_frequency_histogram.md)（`related`）：“AscCumulativeHistogram”定义：对直方图数据进行累计统计，支持低位和高位两种模式，统计结果在目的寄存器原始数据基础上累加。；“AscFrequencyHistogram”定义：对输入数据进行频率统计生成直方图，支持低位和高位两种模式，结果在dst原有数据基础上累加。。实质衔接：Histograms/AscCumulativeHistogram 都在原 dst 上累加累计统计；FrequencyHistogram 改为频率统计，接口总览明确两种模式选择。
- [直方图计算](histogram_compute.md)（`related`）：“AscCumulativeHistogram”定义：对直方图数据进行累计统计，支持低位和高位两种模式，统计结果在目的寄存器原始数据基础上累加。；“直方图计算”定义：寄存器侧直方图计算类接口汇总，提供累积直方图与频率直方图两种计算能力。。实质衔接：Histograms/AscCumulativeHistogram 都在原 dst 上累加累计统计；FrequencyHistogram 改为频率统计，接口总览明确两种模式选择。
- [Histograms](../../../basic_api/reg_vector_compute/histogram_compute/histograms.md)（`same_topic`）：“AscCumulativeHistogram”定义：对直方图数据进行累计统计，支持低位和高位两种模式，统计结果在目的寄存器原始数据基础上累加。；“Histograms”定义：对直方图数据进行统计，在目的寄存器原始数据上累加源寄存器数据的频率统计或累计统计结果。。实质衔接：Histograms/AscCumulativeHistogram 都在原 dst 上累加累计统计；FrequencyHistogram 改为频率统计，接口总览明确两种模式选择。
<!-- cannbot:related:end -->
