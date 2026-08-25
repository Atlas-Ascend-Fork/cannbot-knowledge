---
type: API
title: AscGetMaskSpr
description: 从特殊功能寄存器读取mask值，并按b16或b32数据类型格式化后返回
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_data_types/asc_get_mask_spr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscGetMaskSpr

从SPR（Special Purpose Register）中读取mask值，并按数据类型格式化后返回。
函数原型：vector_bool asc_get_mask_spr_b16()
返回值：vector_bool，掩码寄存器。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [ResetMask](../../../basic_api/memory_vector_compute/mask_operations/reset_mask.md)（`related`）：调试完 mask SPR 后需用 ResetMask 恢复默认状态，避免读取/实验后留下的 mask 配置影响后续指令。
- [SetMaskCount](../../../basic_api/memory_vector_compute/mask_operations/set_mask_count.md)（`related`）：SetMaskCount 切换计数 mask 状态后，AscGetMaskSpr 可读取寄存器内容用于调试 count 模式配置。
- [SetMaskNorm](../../../basic_api/memory_vector_compute/mask_operations/set_mask_norm.md)（`related`）：AscGetMaskSpr 读取当前 mask SPR，SetMaskNorm 是写入 normal mask 状态的直接来源，可用读取结果核验设置是否生效。
- [AscCreateMask](asc_create_mask.md)（`same_topic`）：AscCreateMask 与《AscGetMaskSpr》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
<!-- cannbot:related:end -->
