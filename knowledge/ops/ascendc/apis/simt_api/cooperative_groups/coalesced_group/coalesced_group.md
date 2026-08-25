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

<!-- cannbot:related:start -->
## 相关

- [SIMT 切分未 coalesce 致 block 边界错位](../../../../runbooks/precision/simt_coalesce_block.md)（`exemplifies`）：CoalescedGroup 与《SIMT 切分未 coalesce 致 block 边界错位》的实质衔接是：CoalescedGroup 表示分支发散后当前 warp 的活跃子集；构造/简介、协作组总览、未 coalesce 故障和分支优化指南共同界定成员身份与适用场景。
- [SIMT协作组简介（高级编程）](../../../../guides/programming_guide/advanced_programming/simt_cooperative_groups.md)（`explains`）：CoalescedGroup 与《SIMT协作组简介（高级编程）》的实质衔接是：CoalescedGroup 表示分支发散后当前 warp 的活跃子集；构造/简介、协作组总览、未 coalesce 故障和分支优化指南共同界定成员身份与适用场景。
- [同一Warp内避免分支跳转](../../../../guides/operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md)（`explains`）：CoalescedGroup 与《同一Warp内避免分支跳转》的实质衔接是：CoalescedGroup 表示分支发散后当前 warp 的活跃子集；构造/简介、协作组总览、未 coalesce 故障和分支优化指南共同界定成员身份与适用场景。
- [CoalescedGroup协作组shfl](shfl.md)（`related`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《CoalescedGroup》说明SIMT协作线程组coalesced_group接口集合，涵盖构造、同步、尺寸查询、shuffle和投票等操作。。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [CoalescedGroup协作组size](size.md)（`related`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《CoalescedGroup》说明SIMT协作线程组coalesced_group接口集合，涵盖构造、同步、尺寸查询、shuffle和投票等操作。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [NumThreads](num_threads.md)（`related`）：NumThreads 与《CoalescedGroup》的实质衔接是：NumThreads 返回 group 当前线程数，coalesced/thread-block/tile 对应入口、size、ThreadRank、构造与简介共同界定不同协作组作用域。
- [ShflUp](shfl_up.md)（`related`）：ShflUp 与《CoalescedGroup》的实质衔接是：coalesced_group::shfl_up 在当前活跃线程子组内读取前 delta lane；组的构造与简介限定发散后的成员集合，generic shfl、shfl_down、thread_block_tile 和 Warp C API 给出索引方向及作用域对照。
- [协作组](../cooperative_groups.md)（`related`）：CoalescedGroup 把分支后仍活跃的 Warp 线程组成子组，并提供投票与 shuffle，具体化汇总页的动态活跃线程协作能力。
- [Ballot](ballot.md)（`same_topic`）：Ballot 与《CoalescedGroup》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [CoalescedGroup协作组all](all.md)（`same_topic`）：CoalescedGroup协作组all 与《CoalescedGroup》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
- [coalesced_group构造函数](coalesced_group_constructor.md)（`same_topic`）：CoalescedGroup 与《coalesced_group构造函数》的实质衔接是：CoalescedGroup 表示分支发散后当前 warp 的活跃子集；构造/简介、协作组总览、未 coalesce 故障和分支优化指南共同界定成员身份与适用场景。
- [coalesced_group简介](coalesced_group_intro.md)（`same_topic`）：coalesced_group简介 与《CoalescedGroup》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
<!-- cannbot:related:end -->
