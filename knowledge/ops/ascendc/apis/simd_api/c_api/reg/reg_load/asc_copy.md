---
type: API
title: AscCopy
description: 完成矢量寄存器之间、掩码寄存器之间以及矢量寄存器到掩码寄存器的数据搬运。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_copy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscCopy

完成数据在寄存器间的搬运，支持以下三种模式： 具体搬运原理请参考关键特性说明。
函数原型：void asc_copy(vector_int8_t& dst, vector_int8_t src, vector_bool mask)
约束：针对矢量数据寄存器复制到矢量数据寄存器：dst中未被mask筛选的位置保持原值。；针对掩码寄存器复制到掩码寄存器：带mask的接口dst中未被mask筛选的位置填0。；针对矢量寄存器复制到掩码寄存器：part的值必须在编译期确定，可传入整数字面量或constexpr整数常量，不支持传入运行时变量。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [模板内 float→float Cast 使 fp32 分支全错](../../../../../runbooks/precision/templated_float_input_must_bypass_same_type_cast.md)（`exemplifies`）：模板内 float→float Cast 使 fp32 分支全错 与《AscCopy》的实质衔接是：float 到 float 不应进入窄化 Cast，应该保持原值或 Copy；同步、BF16 分阶段、native 类型、VL、舍入与 RmsNorm 案例分别说明真正需要 Cast 时的类型、时序和验证契约。
- [AscCopy](../../vector_compute/asc_copy.md)（`related`）：AscCopy 与《AscCopy》的实质衔接是：寄存器 AscCopy 在 RegTensor/MaskReg 间搬运；reg load 总览、AscLoad 和矢量 AscCopy 明确其数据域与替代路径。
- [AscLoad](asc_load.md)（`related`）：AscCopy 与《AscLoad》的实质衔接是：寄存器 AscCopy 在 RegTensor/MaskReg 间搬运；reg load 总览、AscLoad 和矢量 AscCopy 明确其数据域与替代路径。
- [AscLoadalign](asc_loadalign.md)（`related`）：AscCopy 与《AscLoadalign》的实质衔接是：寄存器 AscCopy 在 RegTensor/MaskReg 间搬运；reg load 总览、AscLoad 和矢量 AscCopy 明确其数据域与替代路径。
- [Copy](../../../basic_api/memory_vector_compute/data_move/copy_ub_to_ub_continuous.md)（`related`）：Copy 与《AscCopy》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
- [Reg矢量计算](../reg.md)（`related`）：AscCopy 与《Reg矢量计算》的实质衔接是：寄存器 AscCopy 在 RegTensor/MaskReg 间搬运；reg load 总览、AscLoad 和矢量 AscCopy 明确其数据域与替代路径。
- [reg数据搬入](reg_load.md)（`related`）：AscCopy 与《reg数据搬入》的实质衔接是：寄存器 AscCopy 在 RegTensor/MaskReg 间搬运；reg load 总览、AscLoad 和矢量 AscCopy 明确其数据域与替代路径。
- [Copy](../../../basic_api/memory_vector_compute/data_move/copy_ub_to_ub_mask_highdim_split.md)（`same_topic`）：Copy 与《AscCopy》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
<!-- cannbot:related:end -->
