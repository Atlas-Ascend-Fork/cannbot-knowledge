---
type: API
title: AscSetCopyPadVal
description: 配合asc_copy_gm2ub_align或asc_copy_ub2gm_align接口，设置搬运数据块左右两侧需要填补的数据值。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_copy_pad_val.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSetCopyPadVal

和asc_copy_gm2ub_align或asc_copy_ub2gm_align接口配合使用，设置连续搬运数据块左右两侧需要填补的数据值。 对于Ascend 950PR/Ascend 950DT产品：
函数原型：void asc_set_copy_pad_val(int8_t pad_value)
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2UbAlign](asc_copy_gm2ub_align/asc_copy_gm2ub_align.md)（`related`）：AscSetCopyPadVal 负责“配合asc_copy_gm2ub_align或asc_copy_ub2gm_align接口，设置搬运数据块左右两侧需要填补的数据值”；AscCopyGm2UbAlign 负责“提供数据非对齐搬运功能，将数据从GM搬运到UB，支持8位/16位/32位数据类型，包含不同架构版本实现”。
- [AscCopyGm2UbAlign](asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_2201.md)（`related`）：AscSetCopyPadVal 负责“配合asc_copy_gm2ub_align或asc_copy_ub2gm_align接口，设置搬运数据块左右两侧需要填补的数据值”；AscCopyGm2UbAlign 负责“提供数据非对齐搬运功能，将数据从GM搬运到UB，支持8位/16位/32位数据类型搬运”。
- [SetPadValue](../../basic_api/memory_vector_compute/data_move_aux_config/set_pad_value_isasi.md)（`related`）：AscSetCopyPadVal说明配合asc_copy_gm2ub_align或asc_copy_ub2gm_align接口，设置搬运数据块左右两侧需要填补的数据值；对SetPadValue而言，SetPadValue 配置搬运补齐值；C API 的 copy-pad SPR 设置和 DataCopyPad 的左/右 padding 是其实际消费位置。
- [asc_copy_gm2ub](asc_copy_gm2ub/asc_copy_gm2ub_arch_2201.md)（`related`）：asc_copy_gm2ub 与《AscSetCopyPadVal》的实质衔接是：这些卡是 GM 到 UB 搬运的架构变体、对齐形态及 loop/pad 配置接口；调用前必须用匹配的 stride、loop size 与 padding 值构造同一数据搬运描述。
- [AscCopyUb2GmAlign](asc_copy_ub2gm_align/asc_copy_ub2gm_align_arch_2201.md)（`same_topic`）：AscCopyUb2GmAlign 与《AscSetCopyPadVal》的实质衔接是：UB→GM aligned 搬运与普通/2201 变体、反向 GM→UB、pad 和 loop 配置组成同一非对齐数据通路。
- [AscSetNdimPadValue](asc_set_ndim_pad_value.md)（`same_topic`）：AscSetCopyPadVal 的核心契约是“配合asc_copy_gm2ub_align或asc_copy_ub2gm_align接口，设置搬运数据块左右两侧需要填补的数据值”；AscSetNdimPadValue 补充“设置asc_ndim_copy_gm2ub接口Padding的填充固定值”。
- [asc_copy_ub2gm](asc_copy_ub2gm/asc_copy_ub2gm_arch_2201.md)（`same_topic`）：asc_copy_ub2gm 与《AscSetCopyPadVal》的实质衔接是：UB→GM 基础搬运与 aligned 变体、反向 GM→UB 组成数据通路；loop stride/size 与 pad 值必须在调用前按 2201 契约配置。
- [asc_set_gm2ub_pad（废弃）](asc_set_gm2ub_pad_deprecated.md)（`same_topic`）：AscSetCopyPadVal 的核心契约是“配合asc_copy_gm2ub_align或asc_copy_ub2gm_align接口，设置搬运数据块左右两侧需要填补的数据值”；asc_set_gm2ub_pad（废弃） 补充“此接口已废弃，源数据从GM非对齐搬运到UB设置填补数据值请使用asc_set_copy_pad_val进行设置。 将数据从Global Memory (GM) 非对齐搬运到 Unified Buffer (UB)时，通过调用该接口设置连续搬运数据块左右两侧需要填补的数据值”。
<!-- cannbot:related:end -->
