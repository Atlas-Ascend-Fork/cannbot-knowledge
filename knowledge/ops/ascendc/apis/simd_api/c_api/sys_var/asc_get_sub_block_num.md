---
type: API
title: AscGetSubBlockNum
description: 分离模式下获取一个AI Core上Cube或Vector核的数量。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_sub_block_num.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetSubBlockNum

分离模式下，获取一个AI Core上Cube Core（AIC）或者Vector Core（AIV）的数量。
函数原型：int64_t asc_get_sub_block_num()
返回值：不同Kernel类型下，在AIC和AIV上调用该接口的返回值如下：
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
