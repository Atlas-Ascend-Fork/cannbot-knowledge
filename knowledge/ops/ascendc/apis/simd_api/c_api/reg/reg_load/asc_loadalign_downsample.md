---
type: API
title: AscLoadalignDownsample
description: 从UB对齐搬入2倍VL数据并实现2倍下采样，每隔一个元素保留。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_downsample.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignDownsample

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现2倍下采样搬入模式：加载2倍VL的数据，数据每隔一个保留，支持数据类型为b8/b16。
函数原型：void asc_loadalign_downsample(vector_int8_t& dst, __ubuf__ int8_t* src)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
