---
type: API
title: 归约操作
description: 归约操作接口导航页，涵盖Sum、Mean、ReduceSum、ReduceMax、ReduceMin等沿指定维度的归约计算接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/reduction_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: [agnostic]
---

# 归约操作

Ascend C SIMD 高阶 API 归约计算导航页，提供沿指定维度对张量进行归约的 Kernel 侧接口。
涵盖基础归约（Sum、Mean）与通用归约（ReduceSum、ReduceMean、ReduceMax、ReduceMin、ReduceAny、ReduceAll、ReduceProd），以及 ReduceXorSum 按位异或求和接口。
各接口支持指定归约轴与数据类型，通常配合 Tiling 临时空间查询方法使用。
