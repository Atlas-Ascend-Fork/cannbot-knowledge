---
type: API
title: 原子操作简介
description: SIMT原子操作用于保证对同一地址的一次读-改-写过程具有原子性，可避免多个线程并发更新同一地址时出现更新丢失。原子操作常用于计数、状态抢占、直方图统计、归约计算和共享状态位更新等场景。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/atomic_operations_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 原子操作简介

SIMT原子操作用于保证对同一地址的一次读-改-写过程具有原子性，可避免多个线程并发更新同一地址时出现更新丢失。原子操作常用于计数、状态抢占、直方图统计、归约计算和共享状态位更新等场景。
SIMT原子操作用于保证对同一地址的一次读-改-写过程具有原子性，可避免多个线程并发更新同一地址时出现更新丢失。原子操作常用于计数、状态抢占、直方图统计、归约计算和共享状态位更新等场景。

原子操作保证单次内存更新不可被其他线程打断，但不保证多个线程到达该原子操作的先后顺序，也不能替代线程同步屏障功能。
