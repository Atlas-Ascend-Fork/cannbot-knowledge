---
type: Guide
title: 较小矩阵长驻L1 Buffer，仅分次搬运较大矩阵
description: 【描述】在进行cube计算时，当L1无法全载左右矩阵时，可以让较小的矩阵长驻于L1上，只分次搬运较大的矩阵，减少搬运次数。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/matrix_compute/small_matrix_l1_buffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 较小矩阵长驻L1 Buffer，仅分次搬运较大矩阵

【优先级】高  __
【描述】在进行cube计算时，当L1无法全载左右矩阵时，可以让较小的矩阵长驻于L1上，只分次搬运较大的矩阵，减少搬运次数。
【反例】
假设L1的大小为512K，左矩阵和右矩阵的大小分别为992K、16K，数据类型为half，单次无法将左右矩阵全部载入L1中。开发者规划的切分策略为：不切K轴，将左矩阵平均分成两块A1、A2，shape大小均为[992, 256]；将右矩阵平均分成两块，shape大小均为[256, 16]。计算时的加载顺序如下：先加载A1矩阵至L1，将B1、B2依次加载并计算；然后再加载A2至L1，将B1、B2依次加载并计算。
【正例】
该示例中，将较小的右矩阵一次性搬入L1并长存于L1上，循环内不断搬运A矩阵，当循环次数为2时，共需要3次搬运。
