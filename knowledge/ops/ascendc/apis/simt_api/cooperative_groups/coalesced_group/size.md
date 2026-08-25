---
type: API
title: CoalescedGroup协作组size
description: 获取coalesced_group组内线程总数，与接口num_threads功能相同。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# CoalescedGroup协作组size

获取coalesced_group组内线程总数，与接口num_threads功能相同。
函数原型：unsigned long long size() const
返回值：coalesced_group组内线程总数。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [SIMT 切分未 coalesce 致 block 边界错位](../../../../runbooks/precision/simt_coalesce_block.md)（`exemplifies`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《SIMT 切分未 coalesce 致 block 边界错位》说明多维大 shape 随机算子触发 SIMT split-block 切分时，op_host 侧 InitTensorSliceState 直接写原始多维 shape，未像 PyTorch TensorIterator 那样先 coalesce_dimensions，使 block0 numel 比参考实现少 stride[0]/2，block1 首元素 global idx 整体错位、counter 跳变点位置错。判别信号：block1 首 idx 与期望差恰好等于 stride[0]/2。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [Ballot](ballot.md)（`related`）：Ballot 与《CoalescedGroup协作组size》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [CoalescedGroup](coalesced_group.md)（`related`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《CoalescedGroup》说明SIMT协作线程组coalesced_group接口集合，涵盖构造、同步、尺寸查询、shuffle和投票等操作。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [ThreadRank](thread_rank.md)（`related`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《ThreadRank》说明获取当前线程在coalesced_group组内的排名，排名从0开始。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [binary_partition](../binary_partition.md)（`related`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《binary_partition》说明根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [coalesced_group构造函数](coalesced_group_constructor.md)（`related`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《coalesced_group构造函数》说明coalesced_group不提供默认的构造函数，用户使用coalesced_threads函数创建coalesced_group对象。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [coalesced_group简介](coalesced_group_intro.md)（`related`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《coalesced_group简介》说明在SIMT架构的硬件层面上，处理器以32个线程为一组（一个Warp）来执行线程。如果核函数代码中的条件分支导致Warp内的线程出现发散（Warp Divergence），那么Warp会串行执行每个分支，在执行某个分支时会屏蔽不在该指令路径上的线程。coalesced_group用于获取当前Warp中实际活跃的线程子集。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [CoalescedGroup协作组all](all.md)（`same_topic`）：CoalescedGroup协作组all 与《CoalescedGroup协作组size》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
- [NumThreads](num_threads.md)（`same_topic`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《NumThreads》说明获取coalesced_group组内线程总数。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
<!-- cannbot:related:end -->
