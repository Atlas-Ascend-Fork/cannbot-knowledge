---
type: API
title: AscFrequencyHistogram
description: 对输入数据进行频率统计生成直方图，支持低位和高位两种模式，结果在dst原有数据基础上累加。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/histogram_compute/asc_frequency_histogram.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscFrequencyHistogram

对输入数据进行频率统计，生成直方图。统计结果在dst原有数据基础上累加。

工作原理
- 统计src中每个数值的出现频率。
- dst的第n个元素存储数值n在src中出现的次数。
- 结果累加到dst原有数据中，支持多次统计的累加计算。

分区间统计
由于src数据类型为uint8_t（取值范围0~255），而dst每个元素为uint16_t，且一个Vector Length可存储128个uint16_t数据，因此将统计范围分为两个区间
- 低位模式（BIN0）：统计src中数值在[0, 127]范围内的出现频率。
- 高位模式（BIN1）：统计src中数值在[128, 255]范围内的出现频率，统计时将数值减去128，映射到dst的索引位置。

统计方式如下图所示
- 低位模式（BIN0）：低位模式统计结果，dst[0]表示数值0的出现次数，dst[127]表示数值127的出现次数。
- 高位模式（BIN1）：高位模式统计结果，dst[0]表示数值128的出现次数，dst[127]表示数值255的出现次数。

参数：dst(输入/输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。

支持数据类型：uint16_t、uint8_t。

约束：- 该接口中mask用于筛选源操作数，不影响dst的写入行为，当mask位数为0时，源操作数src对应位置的数值将被忽略，dst对应位置数值为忽略该位置src后计算得到的值。
- dst的数据类型为uint16_t，最大值为65535，使用时需注意累加溢出问题。

仅 Ascend 950PR/Ascend 950DT 支持。
