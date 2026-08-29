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

- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`related`）：该接口已废弃，请使用asc_loadalign_postupdate实现此功能。 对齐数据搬运接口，从UB连续对齐搬入目的操作数，支持多种搬入模式，接口使用repeat stride模式。；将Unified Buffer（UB）中起始地址32字节对齐的数据搬入矢量数据寄存器或掩码寄存器，搬运过程中数据格式和内容保持不变。搬运完成后启用Post Update模式，自动更新源地址指针。本接口提供两种功能模式： 本接口仅在AIV上生效，非AIV调用直接返回。。废弃卡明确迁移到 asc_loadalign_postupdate，目标卡给出替代接口的对齐搬入与指针更新合同。
<!-- cannbot:related:end -->
