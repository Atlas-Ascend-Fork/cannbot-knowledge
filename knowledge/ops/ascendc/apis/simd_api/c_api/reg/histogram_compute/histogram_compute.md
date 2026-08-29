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
