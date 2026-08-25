---
type: API
title: NumThreads
description: 获取coalesced_group组内线程总数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/num_threads.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# NumThreads

获取coalesced_group组内线程总数。
函数原型：unsigned long long num_threads() const
返回值：coalesced_group组内线程总数。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [CoalescedGroup](coalesced_group.md)（`related`）：NumThreads 与《CoalescedGroup》的实质衔接是：NumThreads 返回 group 当前线程数，coalesced/thread-block/tile 对应入口、size、ThreadRank、构造与简介共同界定不同协作组作用域。
- [coalesced_group构造函数](coalesced_group_constructor.md)（`related`）：NumThreads 与《coalesced_group构造函数》的实质衔接是：NumThreads 返回 group 当前线程数，coalesced/thread-block/tile 对应入口、size、ThreadRank、构造与简介共同界定不同协作组作用域。
- [coalesced_group简介](coalesced_group_intro.md)（`related`）：NumThreads 与《coalesced_group简介》的实质衔接是：NumThreads 返回 group 当前线程数，coalesced/thread-block/tile 对应入口、size、ThreadRank、构造与简介共同界定不同协作组作用域。
- [CoalescedGroup协作组size](size.md)（`same_topic`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《NumThreads》说明获取coalesced_group组内线程总数。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [NumThreads](../grid_group/num_threads.md)（`same_topic`）：NumThreads 与《NumThreads》的实质衔接是：NumThreads 返回 group 当前线程数，coalesced/thread-block/tile 对应入口、size、ThreadRank、构造与简介共同界定不同协作组作用域。
- [NumThreads](../thread_block/num_threads.md)（`same_topic`）：NumThreads 与《NumThreads》的实质衔接是：NumThreads 返回 group 当前线程数，coalesced/thread-block/tile 对应入口、size、ThreadRank、构造与简介共同界定不同协作组作用域。
- [NumThreads](../thread_block_tile/num_threads.md)（`same_topic`）：NumThreads 与《NumThreads》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [ThreadRank](thread_rank.md)（`same_topic`）：“ThreadRank”处理获取当前线程在coalesced_group组内的排名，排名从0开始。；“NumThreads”明确获取coalesced_group组内线程总数。。实质衔接：ThreadRank 的返回范围由 coalesced_group 活跃线程集合和 num_threads 决定，构造函数给出对象来源，指南解释发散后的分组语义。
<!-- cannbot:related:end -->
