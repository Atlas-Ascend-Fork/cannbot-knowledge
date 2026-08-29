---
type: API
title: Ballot
description: 判断thread_block_tile组内每个线程的输入是否非零，返回32位无符号整数表示各线程对应bit位。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/ballot.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Ballot

判断thread_block_tile组内每个线程的输入是否非零。
函数原型：unsigned int ballot(int predicate) const
返回值：32-bit的无符号整数：若thread_block_tile组内线程输入的predicate不为0，则返回值中与线程rank对应的bit位为1，否则为0。
约束：仅支持thread_block_tile的模板参数Size小于等于32的场景，即仅支持单Warp内线程子组。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
