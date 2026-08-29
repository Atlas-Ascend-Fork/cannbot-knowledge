---
type: API
title: thread_block_tile简介
description: thread_block_tile是一个模板类，用于管理指定大小的线程子组。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/thread_block_tile_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# thread_block_tile简介

thread_block_tile是一个模板类，用于管理指定大小的线程子组。通过模板参数Size指定子组线程数量，支持sync同步、thread_rank查询线程排名、shfl/shfl_up/shfl_down/shfl_xor线程间数据交换、any/all/ballot谓词归约等操作。

接口支持范围：当Size<=32（单Warp内）时所有接口均支持；当Size>32（跨Warp）时ballot、shfl_up、shfl_down、shfl_xor不支持。

约束：SIMT架构不支持独立线程调度，一个Warp内的各协作组间应避免存在数据依赖，否则可能出现卡死的情况。
