---
type: API
title: AscLoadalignUpsamplePostupdate
description: 从UB对齐搬入VL/2个数据并实现2倍上采样，调用后自动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_upsample_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignUpsamplePostupdate

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现2倍上采样搬入模式并启用Post Update，接口调用后自动更新源操作数地址。
函数原型：void asc_loadalign_upsample_postupdate(vector_int8_t& dst, __ubuf__ int8_t*& src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignUpsample](asc_loadalign_upsample.md)（`same_topic`）：对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现2倍上采样搬入模式：加载VL/2个数据，每个输入元素重复两次，支持数据类型为b8/b16。接口不传入偏移或传入int32_t/addr_reg偏移，由用户自行更新源操作数的地址。；对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现2倍上采样搬入模式并启用Post Update，接口调用后自动更新源操作数地址。。两者完成同一 UB 对齐搬入与二倍重复语义，差异集中在源地址由用户更新还是由 Post Update 自动更新。
<!-- cannbot:related:end -->
