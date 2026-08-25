---
type: API
title: C-API-Reg矢量计算接口理论性能汇总
description: 本节汇总介绍了C-API Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/c_api_reg_vector_compute_theoretical_perf_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# C-API-Reg矢量计算接口理论性能汇总

本节汇总介绍了C-API Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效：

本接口属于 Reg 矢量计算接口，操作 RegTensor 寄存器数据。


临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算编程（C++ Tensor编程）](../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《C-API-Reg矢量计算接口理论性能汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Reg矢量计算编程（C指针编程）](../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/reg_vector_computation.md)（`explains`）：C 指针 Reg 编程指南说明如何组织 VF、mask 和同步，才能把单接口理论周期转化为可测 kernel。
- [API流水类型汇总（附录）](api_pipeline_type_summary.md)（`related`）：C-API Reg 理论性能表需要结合 PIPE_V 流水及 LocalMemBar 依赖规则解释可达到的吞吐。
- [Reg矢量计算接口指令单双发汇总](reg_vector_compute_interface_instruction_single_dual_issue_summary.md)（`related`）：单双发能力解释理论性能表中部分 Reg 指令为何受发射带宽限制。
- [Reg矢量计算接口理论性能汇总](reg_vector_compute_interface_theoretical_perf_summary.md)（`related`）：两份表分别覆盖 C-API Reg 与 C++ Reg 接口的理论周期，可用于同一寄存器算法在语言接口间做吞吐选型。
- [Reg矢量计算](../simd_api/basic_api/reg_vector_compute/reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《C-API-Reg矢量计算接口理论性能汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
<!-- cannbot:related:end -->
