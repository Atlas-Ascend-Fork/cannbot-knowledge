---
type: API
title: ThreadBlock
description: SIMT协作线程组thread_block接口集合，涵盖构造、同步、线程索引和维度查询等操作。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/thread_block.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlock

thread_block是对线程块的抽象，代表核函数的启动配置（线程块个数、每块线程数等）。提供sync同步线程块内所有线程。
查询接口含thread_rank（块内线程排名）、num_threads/size（块内线程数）、thread_index/group_index（线程与线程块索引）、dim_threads/group_dim（线程与线程块维度）。
