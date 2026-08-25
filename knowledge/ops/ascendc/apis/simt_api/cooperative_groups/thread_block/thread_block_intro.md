---
type: API
title: thread_block简介
description: thread_block是对线程块的抽象，它代表了核函数的启动配置（启动的线程块个数，每个线程块内的线程数量等）。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/thread_block_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# thread_block简介

thread_block是对线程块的抽象，它代表了核函数的启动配置（启动的线程块个数，每个线程块内的线程数量等）。通过thread_block可查询线程块维度、线程排名，并调用sync()在线程块范围内同步。

Public成员函数：sync、thread_rank、group_index、thread_index、dim_threads、num_threads、size、group_dim。头文件：simt_api/cooperative_groups.h。
