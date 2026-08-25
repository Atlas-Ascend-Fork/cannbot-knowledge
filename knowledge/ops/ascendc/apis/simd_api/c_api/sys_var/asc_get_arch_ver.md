---
type: API
title: AscGetArchVer
description: 获取当前AI处理器架构版本号。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_arch_ver.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetArchVer

获取当前AI处理器架构版本号。
函数原型：void asc_get_arch_ver(uint32_t& core_version)
约束：在调用asc_get_arch_ver接口前，需先定义core_version,调用asc_get_arch_ver接口后core_version会变成相对应架构版本号的值。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
