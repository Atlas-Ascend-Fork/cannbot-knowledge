---
type: API
title: Reg矢量计算接口MergeMode支持情况汇总
description: 不支持MergeMode模板参数的接口，下文不罗列。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_mergemode_support_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算接口MergeMode支持情况汇总

不支持MergeMode模板参数的接口，下文不罗列。

本接口属于 Reg 矢量计算接口，操作 RegTensor 寄存器数据。


临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 广播枚举与模板顺序不兼容](../../runbooks/compilation/reg_duplicate_highlow_precedes_merge_mode.md)（`exemplifies`）：MergeMode 支持汇总用于判断接口模板是否接收 MERGING/ZEROING；该 runbook 给出 Duplicate 中 HighLowPart 必须位于 MergeMode 之前的真实模板顺序错误。
- [Reg矢量计算编程（C++ Tensor编程）](../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口MergeMode支持情况汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [MaskMergeMode](../simd_api/basic_api/reg_vector_compute/aux_data_types/mask_merge_mode.md)（`related`）：MaskMergeMode 与《Reg矢量计算接口MergeMode支持情况汇总》的实质衔接是：MaskMergeMode 决定 inactive lane 合并行为；支持矩阵和两张编译故障卡直接约束枚举选择与模板实参顺序。
- [Reg矢量计算](../simd_api/basic_api/reg_vector_compute/reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算接口MergeMode支持情况汇总》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
<!-- cannbot:related:end -->
