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

<!-- cannbot:related:start -->
## 相关

- [同一Warp内避免分支跳转](../../../../guides/operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md)（`explains`）：Ballot 与《同一Warp内避免分支跳转》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [ThreadBlockTile协作组any](any.md)（`related`）：Ballot 返回完整 lane 位图，Any 只返回布尔；需要后续 mask 时用 Ballot。
- [Warp Vote类函数](../../warp_functions/warp_vote_functions/warp_vote_functions.md)（`related`）：Warp Vote类函数 与《Ballot》的实质衔接是：该页自身仅列出 warp vote 成员，成员层级已由 part_of 表达；只保留直接使用 vote 做分支优化的指南及 cooperative-group Ballot 对照。
- [Ballot](../coalesced_group/ballot.md)（`same_topic`）：Ballot 与《Ballot》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [NumThreads](num_threads.md)（`same_topic`）：NumThreads 与《Ballot》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [ThreadBlockTile](thread_block_tile.md)（`same_topic`）：Ballot 与《ThreadBlockTile》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [ThreadBlockTile协作组all](all.md)（`same_topic`）：Ballot 与《ThreadBlockTile协作组all》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [ThreadBlockTile协作组size](size.md)（`same_topic`）：Ballot 与《ThreadBlockTile协作组size》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [ThreadBlockTile协作组sync](sync.md)（`same_topic`）：Ballot 与《ThreadBlockTile协作组sync》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [asc_ballot](../../warp_functions/warp_vote_functions/asc_ballot.md)（`same_topic`）：Ballot 与《asc_ballot》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [binary_partition](../binary_partition.md)（`same_topic`）：Ballot 与《binary_partition》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [thread_block_tile构造函数](thread_block_tile_constructor.md)（`same_topic`）：Ballot 与《thread_block_tile构造函数》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [thread_block_tile简介](thread_block_tile_intro.md)（`same_topic`）：Ballot 与《thread_block_tile简介》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [tiled_partition](../tiled_partition.md)（`same_topic`）：Ballot 与《tiled_partition》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [协作组](../cooperative_groups.md)（`same_topic`）：Ballot 与《协作组》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
<!-- cannbot:related:end -->
