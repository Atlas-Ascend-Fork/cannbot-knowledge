---
type: API
title: Reg矢量计算接口理论性能汇总
description: 本节汇总介绍了Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_theoretical_perf_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算接口理论性能汇总

本节汇总介绍了Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效：

本接口属于 Reg 矢量计算接口。

本节汇总介绍了Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效： Ascend 950PR/Ascend 950DT 本节汇总的理论性能均为单指令理论性能，实际性能还需考虑指令单双发情况，请参考Reg矢量计算接口指令单双发汇总。软仿实现的接口和数据类型不提供理论性能。

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算编程（C++ Tensor编程）](../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口理论性能汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [C-API-Reg矢量计算接口理论性能汇总](c_api_reg_vector_compute_theoretical_perf_summary.md)（`related`）：两份表分别覆盖 C-API Reg 与 C++ Reg 接口的理论周期，可用于同一寄存器算法在语言接口间做吞吐选型。
- [Reg矢量计算](../simd_api/basic_api/reg_vector_compute/reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口理论性能汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Reg矢量计算接口指令单双发汇总](reg_vector_compute_interface_instruction_single_dual_issue_summary.md)（`same_topic`）：Reg矢量计算接口指令单双发汇总：单双发汇总给出 Reg 指令吞吐的硬件读写上限；理论性能表用于核对期望 cycle，流水类型表解释能否并行，双发优化卡把这些约束转成可执行排布方法。 目标卡《Reg矢量计算接口理论性能汇总》补充：本节汇总介绍了Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效：
- [Vector指令理论性能汇总](vector_instruction_theoretical_perf_summary.md)（`same_topic`）：Vector 总表明确指出 950 上大量 Memory 矢量 API 由 Reg API 实现而不单列理论性能；Reg 总表给出这些底层单指令性能及单双发说明，是性能估算的直接下钻。
<!-- cannbot:related:end -->
