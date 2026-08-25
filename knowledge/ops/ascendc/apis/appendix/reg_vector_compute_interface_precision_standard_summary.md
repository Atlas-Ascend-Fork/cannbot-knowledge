---
type: API
title: Reg矢量计算接口精度标准汇总
description: 本节汇总介绍了Reg矢量计算接口精度标准的情况，本节内容仅针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_precision_standard_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算接口精度标准汇总

本节汇总介绍了Reg矢量计算接口精度标准的情况，本节内容仅针对如下型号生效：

本接口属于 Reg 矢量计算接口，操作 RegTensor 寄存器数据。


临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [FP16 scatter 归约逐次回写放大相消误差](../../runbooks/precision/low_precision_scatter_reduction_needs_fp32_accumulator.md)（`exemplifies`）：FP16 scatter 归约逐次回写放大相消误差说明已验证边界仅为 FP16 scatter-add：逐步回写 half 会累积舍入误差，须用 FP32 中间缓冲；BF16、multiply、amin、amax 需分别验证。
- [Reg矢量计算编程（C++ Tensor编程）](../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口精度标准汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [核函数运行验证时算子存在精度问题](../../guides/programming_guide/appendix/faq/kernel_precision_issue.md)（`explains`）：核函数运行验证时算子存在精度问题说明在进行算子NPU域的运行验证时，实际数据和真值数据不一致，算子存在精度问题。
- [Memory矢量计算接口边界值汇总](memory_vector_compute_interface_boundary_value_summary.md)（`related`）：Memory矢量计算接口边界值汇总：两张附录分别刻画 Memory 与 Reg 矢量路径在边界值/精度条件下的结果，联合使用可在选定计算接口层前区分异常值行为，而非把目录成员全连接。 目标卡《Reg矢量计算接口精度标准汇总》补充：本节汇总介绍了Reg矢量计算接口精度标准的情况，本节内容仅针对如下型号生效：
- [SIMT接口精度标准汇总](simt_interface_precision_standard_summary.md)（`related`）：SIMT 与 Reg Vector 精度汇总分别给出函数/指令误差标准；混合 kernel 可据此把误差归到 SIMT 或 Reg 段。
- [Reg矢量计算](../simd_api/basic_api/reg_vector_compute/reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口精度标准汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
<!-- cannbot:related:end -->
