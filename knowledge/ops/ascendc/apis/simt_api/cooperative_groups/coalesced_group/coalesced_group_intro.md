---
type: API
title: coalesced_group简介
description: 在SIMT架构的硬件层面上，处理器以32个线程为一组（一个Warp）来执行线程。如果核函数代码中的条件分支导致Warp内的线程出现发散（Warp
  Divergence），那么Warp会串行执行每个分支，在执行某个分支时会屏蔽不在该指令路径上的线程。coalesced_group用于获取当前Warp中实际活跃的线程子集。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/coalesced_group_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# coalesced_group简介

在SIMT架构的硬件层面上，处理器以32个线程为一组（一个Warp）来执行线程。如果核函数代码中的条件分支导致Warp内的线程出现发散（Warp
在SIMT架构的硬件层面上，处理器以32个线程为一组（一个Warp）来执行线程。如果核函数代码中的条件分支导致Warp内的线程出现发散（Warp Divergence），那么Warp会串行执行每个分支，在执行某个分支时会屏蔽不在该指令路径上的线程。coalesced_group用于获取当前Warp中实际活跃的线程子集。

> 使用coalesced_group时需关注SIMT架构不支持独立线程调度。
