---
type: API
title: 直方图计算
description: Reg矢量计算直方图接口索引页，包含Histograms。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/histogram_compute/histogram_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 直方图计算

提供 Histograms 接口，对直方图数据进行统计，在 dstReg 基础数据上累加 srcReg 的统计结果。支持频率统计和累计统计两种模式，通过 HistogramsBinType 选择低位区间 [0-127] 或高位区间 [128-255]。

频率统计中 dstReg 第 n 位表示 srcReg 中数值 n 的出现次数；累计统计中 dstReg 第 n 个元素表示 srcReg 中 0 到 n 所有数值的出现总频率。仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。

<!-- cannbot:related:start -->
## 相关

- [直方图计算](../../../c_api/reg/histogram_compute/histogram_compute.md)（`same_topic`）：直方图计算 与《直方图计算》的实质衔接是：Reg 与 C Reg 的直方图概述是同一频数/累积直方图能力在两层 API 的对应入口；接口成员关系由 part_of 处理。
<!-- cannbot:related:end -->
