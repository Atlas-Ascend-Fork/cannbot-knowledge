---
type: API
title: Reg矢量计算接口指令单双发汇总
description: 本节汇总介绍了Reg矢量计算接口指令单双发的情况，指令单发指1个Cycle能够执行一条指令，指令双发指1个Cycle能够执行两条指令。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_instruction_single_dual_issue_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算接口指令单双发汇总

本节汇总介绍了Reg矢量计算接口指令单双发的情况，指令单发指1个Cycle能够执行一条指令，指令双发指1个Cycle能够执行两条指令。 针对寄存器：1个Cycle只能写两个Reg寄存器；针对UB：1个Cycle只能读两个VL（一个VL为256B），或者1个Cycle读一个VL和写一个VL。 本节内容不包含软仿类接口，仅针对如下型号生效： Ascend 950PR/Ascend 950DT 表 1 接口指令双发汇总

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算编程（C++ Tensor编程）](../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口指令单双发汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [指令双发优化](../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/dual_issue_optimization.md)（`explains`）：指令双发优化 与《Reg矢量计算接口指令单双发汇总》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [API流水类型汇总（附录）](api_pipeline_type_summary.md)（`related`）：流水归属决定 Reg 接口能否并发发射；单双发汇总把该流水信息落实为调度吞吐约束。
- [C-API-Reg矢量计算接口理论性能汇总](c_api_reg_vector_compute_theoretical_perf_summary.md)（`related`）：单双发能力解释理论性能表中部分 Reg 指令为何受发射带宽限制。
- [Reg矢量计算](../simd_api/basic_api/reg_vector_compute/reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口指令单双发汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [Reg矢量计算接口理论性能汇总](reg_vector_compute_interface_theoretical_perf_summary.md)（`same_topic`）：Reg矢量计算接口指令单双发汇总：单双发汇总给出 Reg 指令吞吐的硬件读写上限；理论性能表用于核对期望 cycle，流水类型表解释能否并行，双发优化卡把这些约束转成可执行排布方法。 目标卡《Reg矢量计算接口理论性能汇总》补充：本节汇总介绍了Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效：
<!-- cannbot:related:end -->
