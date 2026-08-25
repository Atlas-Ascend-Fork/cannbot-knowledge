---
type: API
title: Reg矢量计算
description: Reg矢量计算API总览，涵盖数据类型、数据搬入/搬出、MaskReg计算、基础算术、逻辑、归约、同步控制等子模块。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_vector_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算

AscendC Reg 矢量计算 API 总览，基于寄存器侧 Tensor 执行 SIMD 计算。涵盖寄存器与辅助数据类型、VF 调用、数据搬入/搬出、MaskReg 计算，以及基础算术、逻辑、复合、比较与选择、类型转换、归约、数据填充、离散操作、数据重排、数据压缩、直方图、索引操作、同步控制、系统变量访问等子模块。相比 Memory 版本延迟更低，需配合 Load/Store 使用。

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算编程（C++ Tensor编程）](../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Reg矢量计算编程（C指针编程）](../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算 与《Reg矢量计算编程（C指针编程）》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [AscLoad](../../c_api/reg/reg_load/asc_load.md)（`same_topic`）：Reg矢量计算 与《AscLoad》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [AscStore](../../c_api/reg/reg_store/asc_store.md)（`same_topic`）：Reg矢量计算 与《AscStore》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [C-API-Reg矢量计算接口理论性能汇总](../../../appendix/c_api_reg_vector_compute_theoretical_perf_summary.md)（`same_topic`）：Reg矢量计算 与《C-API-Reg矢量计算接口理论性能汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Load](reg_data_load/load.md)（`same_topic`）：Reg矢量计算 与《Load》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Reg矢量计算接口MergeMode支持情况汇总](../../../appendix/reg_vector_compute_interface_mergemode_support_summary.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口MergeMode支持情况汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Reg矢量计算接口指令单双发汇总](../../../appendix/reg_vector_compute_interface_instruction_single_dual_issue_summary.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口指令单双发汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Reg矢量计算接口理论性能汇总](../../../appendix/reg_vector_compute_interface_theoretical_perf_summary.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口理论性能汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Reg矢量计算接口精度标准汇总](../../../appendix/reg_vector_compute_interface_precision_standard_summary.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口精度标准汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Reg矢量计算接口软仿情况汇总](../../../appendix/reg_vector_compute_interface_soft_simulation_summary.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口软仿情况汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Reg矢量计算接口边界值汇总](../../../appendix/reg_vector_compute_interface_boundary_value_summary.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口边界值汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Reg矢量计算概述](overview.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算概述》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Store](reg_data_store/store.md)（`same_topic`）：Reg矢量计算 与《Store》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
<!-- cannbot:related:end -->
