---
type: API
title: Memory矢量计算接口边界值汇总
description: 本节汇总介绍了Memory矢量计算接口在边界值输入下的两类输出结果，以下内容针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/memory_vector_compute_interface_boundary_value_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Memory矢量计算接口边界值汇总

本节汇总介绍了Memory矢量计算接口在边界值输入下的两类输出结果，以下内容针对如下型号生效：

涵盖以下类别：概述、Memory矢量计算接口输出inf/nan的场景总结、基础算术、复合计算、比较与选择、类型转换、归约计算、数据排布转换、数据填充、排序组合。

适用：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。

<!-- cannbot:related:start -->
## 相关

- [Memory矢量计算编程](../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/memory_vector_computation.md)（`explains`）：Memory矢量计算编程 与《Memory矢量计算接口边界值汇总》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [Memory矢量计算](../simd_api/basic_api/memory_vector_compute/memory_vector_compute.md)（`related`）：边界值汇总用于核对各 Memory Vector 指令在 NaN/Inf 等输入下的输出。
- [Reg矢量计算接口精度标准汇总](reg_vector_compute_interface_precision_standard_summary.md)（`related`）：Memory矢量计算接口边界值汇总：两张附录分别刻画 Memory 与 Reg 矢量路径在边界值/精度条件下的结果，联合使用可在选定计算接口层前区分异常值行为，而非把目录成员全连接。 目标卡《Reg矢量计算接口精度标准汇总》补充：本节汇总介绍了Reg矢量计算接口精度标准的情况，本节内容仅针对如下型号生效：
- [Reg矢量计算接口边界值汇总](reg_vector_compute_interface_boundary_value_summary.md)（`related`）：Memory矢量计算接口边界值汇总：两张附录分别刻画 Memory 与 Reg 矢量路径在边界值/精度条件下的结果，联合使用可在选定计算接口层前区分异常值行为，而非把目录成员全连接。 目标卡《Reg矢量计算接口边界值汇总》补充：本节汇总介绍了Reg矢量计算接口在边界值输入下的两类输出结果，以下内容针对如下型号生效：
<!-- cannbot:related:end -->
