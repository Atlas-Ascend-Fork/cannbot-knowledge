---
type: API
title: CoalescedGroup
description: SIMT协作线程组coalesced_group接口集合，涵盖构造、同步、尺寸查询、shuffle和投票等操作。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/coalesced_group.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# CoalescedGroup

coalesced_group获取当前Warp中因条件分支而实际活跃的线程子集。SIMT架构以32线程为一组（Warp）执行，分支发散时Warp串行执行各分支，coalesced_group用于管理活跃线程。
提供sync同步、size/num_threads查询线程数、thread_rank/meta_group_rank/meta_group_size查询排名与分组信息。
shuffle操作含shfl/shfl_up/shfl_down实现线程间数据交换。投票操作含ballot（收集谓词位）、any（任一为真）、all（全部为真）。使用时需关注SIMT架构不支持独立线程调度。
