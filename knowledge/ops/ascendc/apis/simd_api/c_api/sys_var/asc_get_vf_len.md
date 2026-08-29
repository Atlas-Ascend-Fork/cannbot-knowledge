---
type: API
title: AscGetVfLen
description: 获取Tensor位宽VL的大小。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_vf_len.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscGetVfLen

获取Tensor位宽VL（Vector Length）的大小。
函数原型：constexpr int64_t asc_get_vf_len()
返回值：位宽VL（Vector Length）的大小。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
