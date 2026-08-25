---
type: API
title: asc_all
description: 判断是否所有活跃线程的输入均不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均不为0，返回1，否则返回0。Warp内所有活跃线程返回相同的结果。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_vote_functions/asc_all.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_all

判断是否所有活跃线程的输入均不为0。

当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均不为0，返回1，否则返回0。Warp内所有活跃线程返回相同的结果。

函数原型：inline int32_t asc_all(int32_t predicate)

参数：predicate（输入）：操作数。

返回值：当Warp内所有活跃线程的输入均不为0，返回1，否则返回0。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。
