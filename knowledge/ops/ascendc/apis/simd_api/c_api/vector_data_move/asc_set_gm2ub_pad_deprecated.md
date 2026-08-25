---
type: API
title: asc_set_gm2ub_pad（废弃）
description: 此接口已废弃，源数据从GM非对齐搬运到UB设置填补数据值请使用asc_set_copy_pad_val进行设置。 将数据从Global Memory
  (GM) 非对齐搬运到 Unified Buffer (UB)时，通过调用该接口设置连续搬运数据块左右两侧需要填补的数据值。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_gm2ub_pad_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_set_gm2ub_pad（废弃）

此接口已废弃，源数据从GM非对齐搬运到UB设置填补数据值请使用asc_set_copy_pad_val进行设置。 将数据从Global Memory (GM) 非对齐搬运到 Unified Buffer (UB)时，通过调用该接口设置连续搬运数据块左右两侧需要填补的数据值。
函数原型：void asc_set_gm2ub_pad(uint32_t pad_val)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2UbAlign](asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_2201.md)（`related`）：AscCopyGm2UbAlign 与《asc_set_gm2ub_pad（废弃）》的实质衔接是：AscCopyGm2UbAlign 的 2201 入口与通用/3510 变体共享非对齐 GM→UB 契约；loop stride、loop size 和 pad 配置必须在调用前匹配，反向接口用于完整搬运闭环。
- [asc_copy_gm2ub](asc_copy_gm2ub/asc_copy_gm2ub_arch_2201.md)（`related`）：asc_copy_gm2ub 与《asc_set_gm2ub_pad（废弃）》的实质衔接是：这些卡是 GM 到 UB 搬运的架构变体、对齐形态及 loop/pad 配置接口；调用前必须用匹配的 stride、loop size 与 padding 值构造同一数据搬运描述。
- [AscSetCopyPadVal](asc_set_copy_pad_val.md)（`same_topic`）：AscSetCopyPadVal 的核心契约是“配合asc_copy_gm2ub_align或asc_copy_ub2gm_align接口，设置搬运数据块左右两侧需要填补的数据值”；asc_set_gm2ub_pad（废弃） 补充“此接口已废弃，源数据从GM非对齐搬运到UB设置填补数据值请使用asc_set_copy_pad_val进行设置。 将数据从Global Memory (GM) 非对齐搬运到 Unified Buffer (UB)时，通过调用该接口设置连续搬运数据块左右两侧需要填补的数据值”。
<!-- cannbot:related:end -->
