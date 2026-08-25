---
type: API
title: MaskReg计算
description: MaskReg计算接口索引页，包含Move、Interleave、DeInterleave、Select、Pack、UnPack与MoveMask。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/MaskReg_compute/MaskReg_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MaskReg计算

MaskReg 专用计算接口集合，对掩码寄存器进行操作。Move 实现掩码数据搬运；Interleave/DeInterleave 实现交错与反交错；Select 按掩码选择；Pack/UnPack 实现打包与解包；MoveMask 移动掩码位。用于配合矢量计算的掩码控制，实现复杂的数据筛选与重排。

<!-- cannbot:related:start -->
## 相关

- [半精度索引错位—拆分双 int32 掩码](../../../../../runbooks/precision/b16_value_mask_must_split_for_two_int32_index_registers.md)（`exemplifies`）：本卡维护 valueMask、idxMaskLo、idxMaskHi；MaskReg 文档给出这些掩码转换与组合的接口范围。
- [MoveMask](move_mask.md)（`related`）：《MoveMask》明确“从SetVectorMask设置的掩码寄存器中读取Mask值，按模板参数T对应格式转换后写入MaskReg。”；它与《MaskReg计算》的“MaskReg计算接口索引页，包含Move、Interleave、DeInterleave、Select、Pack、UnPack与MoveMask。”在实际调用参数、数据流或结果校验上直接衔接。
- [MaskReg](../register_data_types/mask_reg.md)（`same_topic`）：MaskReg 与《MaskReg计算》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [Move](../reg_data_load/move.md)（`same_topic`）：Move 与《MaskReg计算》的实质衔接是：Move 的掩码写入语义由 C API 对应接口、MaskMergeMode 和 MaskReg 计算契约共同界定。
<!-- cannbot:related:end -->
