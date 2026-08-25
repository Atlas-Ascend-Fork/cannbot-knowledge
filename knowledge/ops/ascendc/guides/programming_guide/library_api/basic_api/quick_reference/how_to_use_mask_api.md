---
type: Guide
title: 如何使用掩码操作API
description: Mask用于控制矢量计算中参与计算的元素个数，支持以下工作模式及配置方式：
tags: [task.lookup, topic.implementation.api_layer]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/library_api/basic_api/quick_reference/how_to_use_mask_api.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 如何使用掩码操作API

Mask用于控制矢量计算中参与计算的元素个数，支持以下工作模式及配置方式：
Mask工作模式
Mask配置方式
Mask操作的使用方式如下：
Mask操作的使用方式
典型场景的使用示例如下：
-   场景1：Normal模式 + 外部API配置 + 高维切分计算API
-   场景2：Counter模式 + 外部API配置 + 高维切分计算API
-   场景3：Counter模式 + 外部API配置 + 前n个数据计算接口配合使用

<!-- cannbot:related:start -->
## 相关

- [AscCreateMask](../../../../../apis/simd_api/c_api/reg/reg_data_types/asc_create_mask.md)（`explains`）：AscCreateMask 与《如何使用掩码操作API》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [AscSetVectorMask](../../../../../apis/simd_api/c_api/vector_compute/asc_set_vector_mask.md)（`explains`）：掩码快速参考给出 Counter/Normal 配置顺序和尾块示例。
- [AscUpdateMask](../../../../../apis/simd_api/c_api/reg/reg_data_types/asc_update_mask.md)（`explains`）：如何使用掩码操作API 与《AscUpdateMask》的实质衔接是：掩码指南直接覆盖 Move/Create/UpdateMask、Normal/Counter 设置和 Reset；两张故障卡约束模板类型与可修改参数。
- [Copy](../../../../../apis/simd_api/basic_api/memory_vector_compute/data_move/copy_ub_to_ub_mask_highdim_split.md)（`explains`）：Copy 与《如何使用掩码操作API》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [MoveMask](../../../../../apis/simd_api/basic_api/reg_vector_compute/mask_reg_compute/move_mask.md)（`explains`）：如何使用掩码操作API 与《MoveMask》的实质衔接是：掩码指南直接覆盖 Move/Create/UpdateMask、Normal/Counter 设置和 Reset；两张故障卡约束模板类型与可修改参数。
- [ResetMask](../../../../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/reset_mask.md)（`explains`）：如何使用掩码操作API 与《ResetMask》的实质衔接是：掩码指南直接覆盖 Move/Create/UpdateMask、Normal/Counter 设置和 Reset；两张故障卡约束模板类型与可修改参数。
- [SetMaskCount](../../../../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/set_mask_count.md)（`explains`）：如何使用掩码操作API 与《SetMaskCount》的实质衔接是：掩码指南直接覆盖 Move/Create/UpdateMask、Normal/Counter 设置和 Reset；两张故障卡约束模板类型与可修改参数。
- [SetMaskNorm](../../../../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/set_mask_norm.md)（`explains`）：SetMaskNorm 与《如何使用掩码操作API》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [SetVectorMask](../../../../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/set_vector_mask.md)（`explains`）：如何使用掩码操作API 与《SetVectorMask》的实质衔接是：掩码指南直接覆盖 Move/Create/UpdateMask、Normal/Counter 设置和 Reset；两张故障卡约束模板类型与可修改参数。
- [Reg CreateMask 缺类型参数导致编译失败](../../../../../runbooks/compilation/reg_createmask_requires_explicit_type.md)（`related`）：如何使用掩码操作API 与《Reg CreateMask 缺类型参数导致编译失败》的实质衔接是：掩码指南直接覆盖 Move/Create/UpdateMask、Normal/Counter 设置和 Reset；两张故障卡约束模板类型与可修改参数。
- [UpdateMask 引用参数拒绝 const — 改用可修改左值](../../../../../runbooks/compilation/updatemask_requires_mutable_uint32_lvalue.md)（`related`）：如何使用掩码操作API 与《UpdateMask 引用参数拒绝 const — 改用可修改左值》的实质衔接是：掩码指南直接覆盖 Move/Create/UpdateMask、Normal/Counter 设置和 Reset；两张故障卡约束模板类型与可修改参数。
<!-- cannbot:related:end -->
