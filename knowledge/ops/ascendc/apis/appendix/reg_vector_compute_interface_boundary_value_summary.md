---
type: API
title: Reg矢量计算接口边界值汇总
description: 本节汇总介绍了Reg矢量计算接口在边界值输入下的两类输出结果，以下内容针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_boundary_value_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算接口边界值汇总

本节汇总介绍了Reg矢量计算接口在边界值输入下的两类输出结果，以下内容针对如下型号生效：

涵盖以下类别：概述、基础算术、复合计算、比较与选择、类型转换、归约计算、索引操作。

适用：Ascend 950PR/Ascend 950DT：、INF/NAN模式（非饱和模式）。

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算编程（C++ Tensor编程）](../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口边界值汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Memory矢量计算接口边界值汇总](memory_vector_compute_interface_boundary_value_summary.md)（`related`）：Memory矢量计算接口边界值汇总：两张附录分别刻画 Memory 与 Reg 矢量路径在边界值/精度条件下的结果，联合使用可在选定计算接口层前区分异常值行为，而非把目录成员全连接。 目标卡《Reg矢量计算接口边界值汇总》补充：本节汇总介绍了Reg矢量计算接口在边界值输入下的两类输出结果，以下内容针对如下型号生效：
- [Reg矢量计算](../simd_api/basic_api/reg_vector_compute/reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口边界值汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
<!-- cannbot:related:end -->
