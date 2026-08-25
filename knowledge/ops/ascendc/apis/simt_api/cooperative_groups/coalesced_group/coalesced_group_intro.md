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

<!-- cannbot:related:start -->
## 相关

- [SIMT 切分未 coalesce 致 block 边界错位](../../../../runbooks/precision/simt_coalesce_block.md)（`exemplifies`）：coalesced_group简介 与《SIMT 切分未 coalesce 致 block 边界错位》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [同一Warp内避免分支跳转](../../../../guides/operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md)（`explains`）：coalesced_group简介 与《同一Warp内避免分支跳转》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [Ballot](ballot.md)（`related`）：Ballot 与《coalesced_group简介》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [CoalescedGroup协作组shfl](shfl.md)（`related`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《coalesced_group简介》说明在SIMT架构的硬件层面上，处理器以32个线程为一组（一个Warp）来执行线程。如果核函数代码中的条件分支导致Warp内的线程出现发散（Warp Divergence），那么Warp会串行执行每个分支，在执行某个分支时会屏蔽不在该指令路径上的线程。coalesced_group用于获取当前Warp中实际活跃的线程子集。。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [CoalescedGroup协作组size](size.md)（`related`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《coalesced_group简介》说明在SIMT架构的硬件层面上，处理器以32个线程为一组（一个Warp）来执行线程。如果核函数代码中的条件分支导致Warp内的线程出现发散（Warp Divergence），那么Warp会串行执行每个分支，在执行某个分支时会屏蔽不在该指令路径上的线程。coalesced_group用于获取当前Warp中实际活跃的线程子集。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [MetaGroupRank](meta_group_rank.md)（`related`）：《MetaGroupRank》说明获取当前线程所在的组在其父组划分出的子组集合中的排名，排名从0开始。；《coalesced_group简介》说明在SIMT架构的硬件层面上，处理器以32个线程为一组（一个Warp）来执行线程。如果核函数代码中的条件分支导致Warp内的线程出现发散（Warp Divergence），那么Warp会串行执行每个分支，在执行某个分支时会屏蔽不在该指令路径上的线程。coalesced_group用于获取当前Warp中实际活跃的线程子集。。二者在MetaGroupRank只在父组被binary/tiled partition划分后有意义，并与MetaGroupSize共同描述子组编号上存在可执行的直接衔接。
- [NumThreads](num_threads.md)（`related`）：NumThreads 与《coalesced_group简介》的实质衔接是：NumThreads 返回 group 当前线程数，coalesced/thread-block/tile 对应入口、size、ThreadRank、构造与简介共同界定不同协作组作用域。
- [ShflUp](shfl_up.md)（`related`）：ShflUp 与《coalesced_group简介》的实质衔接是：coalesced_group::shfl_up 在当前活跃线程子组内读取前 delta lane；组的构造与简介限定发散后的成员集合，generic shfl、shfl_down、thread_block_tile 和 Warp C API 给出索引方向及作用域对照。
- [ThreadRank](thread_rank.md)（`related`）：coalesced_group简介 与《ThreadRank》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [asc_all](../../warp_functions/warp_vote_functions/asc_all.md)（`related`）：asc_all 与《coalesced_group简介》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
- [binary_partition](../binary_partition.md)（`related`）：coalesced_group简介 与《binary_partition》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [tiled_partition](../tiled_partition.md)（`related`）：coalesced_group简介 与《tiled_partition》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [协作组简介](../cooperative_groups_intro.md)（`related`）：coalesced_group 是协作组简介列出的 Warp 活跃线程子集，专页补充了分支发散和非独立线程调度约束。
- [CoalescedGroup](coalesced_group.md)（`same_topic`）：coalesced_group简介 与《CoalescedGroup》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [CoalescedGroup协作组all](all.md)（`same_topic`）：CoalescedGroup协作组all 与《coalesced_group简介》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
- [CoalescedGroup协作组sync](sync.md)（`same_topic`）：简介说明 coalesced_group 由当前活跃线程动态形成，是理解 sync 必须全组到达的作用域基础。
- [MetaGroupSize](meta_group_size.md)（`same_topic`）：coalesced_group简介 与《MetaGroupSize》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [coalesced_group构造函数](coalesced_group_constructor.md)（`same_topic`）：coalesced_group简介 与《coalesced_group构造函数》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
<!-- cannbot:related:end -->
