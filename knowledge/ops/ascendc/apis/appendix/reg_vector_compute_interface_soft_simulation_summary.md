---
type: API
title: Reg矢量计算接口软仿情况汇总
description: 本节汇总介绍了Reg矢量计算接口软仿数据类型的情况，本节内容仅针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_soft_simulation_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [agnostic]
---


# Reg矢量计算接口软仿情况汇总

本节汇总介绍了Reg矢量计算接口软仿数据类型的情况，本节内容仅针对如下型号生效： Ascend 950PR/Ascend 950DT Reg数据搬入和Reg数据搬出目录下提供了UB与RegTensor、UB与MaskReg之间的数据搬运接口。 UB与RegTensor之间的数据搬运根据操作数的数据类型位宽来搬运，与数据类型本身无关，表1和表2列出的软仿支持的数据类型包括以下情况： - 底层硬件不支持该数据类型，通过其他位宽相同的数据类型支持的搬运指令实现。 - 底层硬件不支持该数据类型，通过多种接口组合软仿实现。 - 底层硬件不支持该数据类型，通过双搬入 双搬出模式软仿实现RegTraitNumTwo的数据类型。

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算编程（C++ Tensor编程）](../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口软仿情况汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Reg矢量计算](../simd_api/basic_api/reg_vector_compute/reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口软仿情况汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [SIMT接口软仿情况汇总](simt_interface_soft_simulation_summary.md)（`same_topic`）：Reg矢量计算接口软仿情况汇总 与《SIMT接口软仿情况汇总》的衔接是：两张汇总采用同一‘单指令或编译器/上层拼接软仿’判定口径，SIMT汇总可用于区分 Reg 搬入搬出双操作数软仿与另一执行模型的软仿边界。
<!-- cannbot:related:end -->
