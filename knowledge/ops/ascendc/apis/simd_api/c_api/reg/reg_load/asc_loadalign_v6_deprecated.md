---
type: API
title: asc_loadalign (废弃)
description: reg数据搬运接口，适用于从UB搬入MaskReg。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_v6_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_loadalign (废弃)

reg数据搬运接口，适用于从UB搬入MaskReg。
函数原型：void asc_loadalign(vector_bool& dst, __ubuf__ uint32_t* src)
约束：offset在缺省时默认偏移值offset=0。；用户可以通过自增基地址或者偏移的方式传入offset参数。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
