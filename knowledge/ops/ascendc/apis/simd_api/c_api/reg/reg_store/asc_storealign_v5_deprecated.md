---
type: API
title: asc_storealign (废弃)
description: 该接口已废弃，请使用asc_storealign_postupdate实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器连续对齐搬出到UB的场景，接口使用repeat
  stride模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_v5_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_storealign (废弃)

该接口已废弃，请使用asc_storealign_postupdate实现此功能。 reg计算数据搬运接口，适用于从矢量数据寄存器连续对齐搬出到UB的场景，接口使用repeat stride模式。
函数原型：void asc_storealign(__ubuf__ int8_t* dst_align32b, vector_int8_t src, uint16_t block_stride, uint16_t repeat_stride, vector_bool mask)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscStorealign](asc_storealign.md)（`related`）：若无需 postupdate 的地址更新语义，可改用通用 AscStoreAlign 完成连续对齐搬出。
- [AscStoreAlignPostupdate](asc_storealign_postupdate.md)（`same_topic`）：废弃说明明确要求用 asc_storealign_postupdate 替代 v5 的 repeat-stride 搬出功能。
<!-- cannbot:related:end -->
