---
type: API
title: asc_ballot
description: 判断Warp中每个活跃线程的输入是否非零。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，返回一个32bit的无符号整数，若Warp内活跃线程输入的predicate不为0，则返回值中与线程Lane
  ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_vote_functions/asc_ballot.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_ballot

判断Warp中每个活跃线程的输入是否非零。

当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，返回一个32bit的无符号整数，若Warp内活跃线程输入的predicate不为0，则返回值中与线程Lane ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。

函数原型：inline uint32_t asc_ballot(int32_t predicate)

参数：predicate（输入）：操作数。

返回值：32bit的无符号整数：若Warp内活跃线程输入的predicate不为0，则返回值中与线程Lane ID对应的bit位为1，否则为0。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。
