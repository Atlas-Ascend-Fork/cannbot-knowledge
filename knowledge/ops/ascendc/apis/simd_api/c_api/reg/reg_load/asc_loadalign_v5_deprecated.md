---
type: API
title: asc_loadalign (废弃)
description: 该接口已废弃，请使用asc_loadalign_postupdate实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口使用repeat
  stride模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_v5_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_loadalign (废弃)

该接口已废弃，请使用asc_loadalign_postupdate实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口使用repeat stride模式。
函数原型：void asc_loadalign(vector_int8_t& dst, __ubuf__ int8_t* src, uint16_t block_stride, uint16_t repeat_stride, vector_bool mask)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`same_topic`）：废弃 repeat-stride asc_loadalign 正文明确迁移到 asc_loadalign_postupdate；替代接口完成对齐搬入后自动更新源地址。
<!-- cannbot:related:end -->
