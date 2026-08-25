---
type: Guide
title: 基于全局掩码复用的计算性能优化
description: '>该性能优化建议适用于如下产品型号：'
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/vector_compute/mask_reuse_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# 基于全局掩码复用的计算性能优化

>该性能优化建议适用于如下产品型号：
>
>- Atlas A3 训练系列产品/Atlas A3 推理系列产品
>
>
>- Atlas A2 训练系列产品/Atlas A2 推理系列产品
>

【优先级】高

【描述】当**连续执行多个**向量计算操作（如多次Adds、Muls等）且这些操作共享**相同的掩码配置参数**（如掩码长度、掩码值和掩码模式一致）时，存在性能优化空间。此时，若每次调用计算接口时都启用内部掩码设置（即**isSetMask=true**），将被迫重复执行一整套掩码初始化流程：包括设置掩码模式SetMaskCount、设置掩码值（SetVectorMask）、重置掩码（ResetMask）以及重置掩码模式（SetMaskNorm）。这一系列操作在硬件层面需要耗费大量cycle，尤其在高频计算中，会拖慢整体执行效率。在计算规模较小时，由于实际计算耗时短，而掩码配置的固定开销占总耗时比例较高，优化策略能显著降低相对开销，实现高比例性能提升。

【优化方案】

在这些场景中，掩码配置保持不变的情况下，遵循“**一次性全局配置，后续复用**”的核心原则：在所有连续计算操作执行之前，通过调用**SetVectorMask**接口完成**全局掩码**的一次性、完整设置mask；随后，所有后续的向量计算接口调用均应将**isSetMask**参数设置为**false**，以明确指示接口跳过内部掩码设置流程，直接**复用已预置**的全局掩码状态。

**图1**  代码优化

理论分析：SetMaskCount、SetMask、ResetMask、SetMaskNorm四个接口，每个接口调用耗时1cycle，连续调用180次Adds计算接口，共节省4×180 = 720cycles。

<!-- cannbot:related:start -->
## 相关

- [AscSetMaskCount](../../../../apis/simd_api/c_api/vector_compute/asc_set_mask_count.md)（`explains`）：计数模式可把一次 mask 配置跨多指令复用。
- [MaskReg](../../../../apis/simd_api/basic_api/reg_vector_compute/register_data_types/mask_reg.md)（`explains`）：MaskReg 与《基于全局掩码复用的计算性能优化》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [Mask接口汇总（附录）](../../../../apis/appendix/mask_interface_summary.md)（`explains`）：Mask 支持矩阵界定哪些接口可复用全局 mask。
- [SetMaskNorm](../../../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/set_mask_norm.md)（`explains`）：SetMaskNorm 与《基于全局掩码复用的计算性能优化》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [VfFusionOptimization](vf_optimization/vf_fusion_optimization.md)（`related`）：VF fusion 可减少重复 mask 设置，但需保持 mask 生命周期。
- [arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用](../../../../runbooks/precision/arch35_select_vsel_cmpmask_spr_mask_reuse_count_over_64.md)（`related`）：该卡证明错误跨 repeat 复用 cmpmask 会污染后续元素，给出复用边界。
- [中级性能优化](../../typical_operator_cases/simd_operator_impl/add_vector_operator/intermediate_optimization.md)（`related`）：中级性能优化 与《基于全局掩码复用的计算性能优化》的实质衔接是：Add 中级优化围绕 mask 复用、双发、循环/融合与 Get/SetValue 访问开销实施。
- [指令双发优化](vf_optimization/dual_issue_optimization.md)（`related`）：指令双发优化 与《基于全局掩码复用的计算性能优化》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
<!-- cannbot:related:end -->
