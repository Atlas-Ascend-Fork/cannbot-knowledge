---
type: API
title: AscLoadalignDownsamplePostupdate
description: 从UB对齐搬入2倍VL数据并实现2倍下采样，调用后自动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_downsample_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignDownsamplePostupdate

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现2倍下采样搬入模式并启用Post Update，接口调用后自动更新源操作数地址。
函数原型：void asc_loadalign_downsample_postupdate(vector_int8_t& dst, __ubuf__ int8_t*& src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignDownsample](asc_loadalign_downsample.md)（`same_topic`）：对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现2倍下采样搬入模式：加载2倍VL的数据，数据每隔一个保留，支持数据类型为b8/b16。；对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现2倍下采样搬入模式并启用Post Update，接口调用后自动更新源操作数地址。。两端共享 UB 对齐搬入和二倍下采样语义，PostUpdate 变体额外按 offset 更新源地址；联合阅读可在手工地址推进与自动推进之间选择。
<!-- cannbot:related:end -->
