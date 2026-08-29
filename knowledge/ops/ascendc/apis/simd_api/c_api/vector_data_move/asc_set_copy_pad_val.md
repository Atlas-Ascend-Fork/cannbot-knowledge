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

- [AscCopyGm2UbAlign](asc_copy_gm2ub_align/asc_copy_gm2ub_align.md)（`related`）：Global Memory到Unified Buffer对齐数据搬运接口集合，支持按指定对齐要求将数据从GM搬运到UB。；和asc_copy_gm2ub_align或asc_copy_ub2gm_align接口配合使用，设置连续搬运数据块左右两侧需要填补的数据值。；padding 值设置接口明确服务于对齐搬运，补齐 GM 到 UB 搬运中边界填充的参数合同。
- [AscCopyGm2UbAlign](asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_3510.md)（`related`）：“若搬运数据长度非32字节对齐，搬运数据会补齐至32字节对齐”产生填充区，“设置连续搬运数据块左右两侧需要填补的数据值”定义该填充区的值，二者是配套调用。
- [asc_set_gm2ub_pad（废弃）](asc_set_gm2ub_pad_deprecated.md)（`same_topic`）：“此接口已废弃，源数据从GM非对齐搬运到UB设置填补数据值请使用asc_set_copy_pad_val进行设置。”明确旧接口的替代目标；“和asc_copy_gm2ub_align或asc_copy_ub2gm_align接口配合使用，设置连续搬运数据块左右两侧需要填补的数据值。”给出新接口承接的搬运调用范围。
<!-- cannbot:related:end -->
