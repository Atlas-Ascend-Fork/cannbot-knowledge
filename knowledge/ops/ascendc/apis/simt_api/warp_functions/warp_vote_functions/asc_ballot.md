---
type: API
title: asc_ballot
description: 判断Warp中每个活跃线程的输入是否非零。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，返回一个32bit的无符号整数，若Warp内活跃线程输入的predicate不为0，则返回值中与线程Lane
  ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_vote_functions/asc_ballot.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_ballot

判断Warp中每个活跃线程的输入是否非零。

当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，返回一个32bit的无符号整数，若Warp内活跃线程输入的predicate不为0，则返回值中与线程Lane ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。

函数原型：inline uint32_t asc_ballot(int32_t predicate)

参数：predicate（输入）：操作数。

返回值：32bit的无符号整数：若Warp内活跃线程输入的predicate不为0，则返回值中与线程Lane ID对应的bit位为1，否则为0。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [Ballot](../../cooperative_groups/coalesced_group/ballot.md)（`related`）：Ballot 与《asc_ballot》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [asc_activemask](asc_activemask.md)（`related`）：asc_activemask 返回当前活跃 lane 位图，asc_ballot 返回活跃 lane 中 predicate 为真的位图；两者可相与或比较判断分支参与情况。
- [asc_any](asc_any.md)（`related`）：《asc_any》说明判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。；《asc_ballot》说明判断Warp中每个活跃线程的输入是否非零。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，返回一个32bit的无符号整数，若Warp内活跃线程输入的predicate不为0，则返回值中与线程Lane ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。。二者在asc_any对Warp活跃线程做投票，与all/ballot/activemask共同定义聚合谓词并影响分支收敛上存在可执行的直接衔接。
- [Ballot](../../cooperative_groups/thread_block_tile/ballot.md)（`same_topic`）：Ballot 与《asc_ballot》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [asc_all](asc_all.md)（`same_topic`）：asc_all 与《asc_ballot》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
<!-- cannbot:related:end -->
