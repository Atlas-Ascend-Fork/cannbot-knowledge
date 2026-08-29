---
type: API
title: 原子操作
description: SIMT API原子操作类接口汇总，提供add、sub、exch、max、min、inc、dec、cas等原子运算能力。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/atomic_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 原子操作

SIMT原子操作保证对同一地址的单次读-改-写过程具有原子性，避免多线程并发更新丢失。提供asc_atomic_add/sub/exch/max/min/inc/dec/cas/and/or/xor，适用于计数、状态抢占、直方图统计、归约等场景。
原子操作可作用于Global Memory（Grid内可访问）和Unified Buffer（线程块内可访问）。GM原子操作以128B地址范围为粒度，目标地址分散可提升吞吐；UB原子操作延迟较低但作用范围限于当前线程块。
原子操作保证单次更新不被打断，但不保证线程执行顺序，也不能替代同步屏障。浮点累加要求逐bit一致时应使用固定顺序归约。
