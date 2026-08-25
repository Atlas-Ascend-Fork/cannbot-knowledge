---
type: API
title: thread_block构造函数
description: thread_block不提供默认的构造函数，用户使用this_thread_block函数获取当前线程所属的thread_block对象。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/thread_block_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# thread_block构造函数

thread_block不提供默认的构造函数，用户使用this_thread_block函数获取当前线程所属的thread_block对象。
函数原型：thread_block this_thread_block()
返回值：返回当前线程所属的thread_block对象。
约束：线程块实际启动线程数不能超过MaxBlockSize。；scratch对应的block_tile_memory对象必须位于Global Memory或Unified Buffer，不能是在栈空间中创建的对象。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [DimThreads](dim_threads.md)（`related`）：thread_block构造函数 与《DimThreads》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [GroupDim](group_dim.md)（`related`）：thread_block构造函数 与《GroupDim》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [GroupIndex](group_index.md)（`related`）：thread_block构造函数 与《GroupIndex》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [NumThreads](num_threads.md)（`related`）：thread_block构造函数 与《NumThreads》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [ThreadBlock协作组size](size.md)（`related`）：thread_block构造函数 与《ThreadBlock协作组size》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [ThreadBlock协作组sync](sync.md)（`related`）：thread_block构造函数 与《ThreadBlock协作组sync》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [ThreadIndex](thread_index.md)（`related`）：thread_block构造函数 与《ThreadIndex》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [ThreadRank](thread_rank.md)（`related`）：thread_block构造函数 与《ThreadRank》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [ThreadBlock](thread_block.md)（`same_topic`）：thread_block构造函数 与《ThreadBlock》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [thread_block简介](thread_block_intro.md)（`same_topic`）：thread_block构造函数 与《thread_block简介》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
<!-- cannbot:related:end -->
