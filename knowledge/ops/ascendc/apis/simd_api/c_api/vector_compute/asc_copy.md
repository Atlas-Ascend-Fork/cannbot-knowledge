---
type: API
title: AscCopy
description: 将数据从Unified Buffer搬运到Unified Buffer。支持高维切分。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_copy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscCopy

将数据从Unified Buffer搬运到Unified Buffer。支持高维切分。
函数原型：void asc_copy(__ubuf__ int16_t* dst, __ubuf__ int16_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [fp32 UB 非 VL 拷贝须用带掩码 Reg](../../../../runbooks/precision/non_vl_fp32_ub_copy_needs_masked_reg_load_store.md)（`exemplifies`）：AscCopy 与《fp32 UB 非 VL 拷贝须用带掩码 Reg》的实质衔接是：AscCopy 是 UB→UB 搬运；basic Copy、UB 搬运指南和 Reg Copy提供连续、高维/掩码入口，非整 VL 的 fp32 案例说明何时必须改用 masked Reg load/store。
- [模板内 float→float Cast 使 fp32 分支全错](../../../../runbooks/precision/templated_float_input_must_bypass_same_type_cast.md)（`exemplifies`）：模板内 float→float Cast 使 fp32 分支全错 与《AscCopy》的实质衔接是：float 到 float 不应进入窄化 Cast，应该保持原值或 Copy；同步、BF16 分阶段、native 类型、VL、舍入与 RmsNorm 案例分别说明真正需要 Cast 时的类型、时序和验证契约。
- [AscCopy](../reg/reg_load/asc_copy.md)（`related`）：AscCopy 与《AscCopy》的实质衔接是：寄存器 AscCopy 在 RegTensor/MaskReg 间搬运；reg load 总览、AscLoad 和矢量 AscCopy 明确其数据域与替代路径。
- [Copy](../../basic_api/memory_vector_compute/data_move/copy_ub_to_ub_continuous.md)（`same_topic`）：AscCopy 与《Copy》的实质衔接是：AscCopy 是 UB→UB 搬运；basic Copy、UB 搬运指南和 Reg Copy提供连续、高维/掩码入口，非整 VL 的 fp32 案例说明何时必须改用 masked Reg load/store。
- [Copy](../../basic_api/memory_vector_compute/data_move/copy_ub_to_ub_mask_highdim_split.md)（`same_topic`）：AscCopy 与《Copy》的实质衔接是：AscCopy 是 UB→UB 搬运；basic Copy、UB 搬运指南和 Reg Copy提供连续、高维/掩码入口，非整 VL 的 fp32 案例说明何时必须改用 masked Reg load/store。
- [UB与UB数据搬运](../../basic_api/data_move_guide/ub_ub_data_move.md)（`same_topic`）：AscCopy 与《UB与UB数据搬运》的实质衔接是：AscCopy 是 UB→UB 搬运；basic Copy、UB 搬运指南和 Reg Copy提供连续、高维/掩码入口，非整 VL 的 fp32 案例说明何时必须改用 masked Reg load/store。
<!-- cannbot:related:end -->
