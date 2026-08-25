---
type: API
title: asc_any
description: 判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_vote_functions/asc_any.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_any

判断是否有活跃线程的输入不为0。

当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。

函数原型：inline int32_t asc_any(int32_t predicate)

参数：predicate（输入）：操作数。

返回值：当Warp内所有活跃线程的输入均为0，返回0，否则返回1。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [同一Warp内避免分支跳转](../../../../guides/operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md)（`explains`）：《asc_any》说明判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。；《同一Warp内避免分支跳转》说明同一Warp内线程应避免分支跳转以防止分支发散，减少掩码屏蔽等待，提升SIMT算子执行效率。。二者在asc_any对Warp活跃线程做投票，与all/ballot/activemask共同定义聚合谓词并影响分支收敛上存在可执行的直接衔接。
- [Warp Vote类函数](warp_vote_functions.md)（`related`）：《asc_any》说明判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。；《Warp Vote类函数》说明提供Warp级别的投票与掩码接口。。二者在asc_any对Warp活跃线程做投票，与all/ballot/activemask共同定义聚合谓词并影响分支收敛上存在可执行的直接衔接。
- [asc_activemask](asc_activemask.md)（`related`）：《asc_any》说明判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。；《asc_activemask》说明查看Warp内所有线程是否为活跃状态。 返回一个32bit的无符号整数，若Warp内某个线程是活跃（已结束线程是非活跃状态）的，则返回值中与线程Lane ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。。二者在asc_any对Warp活跃线程做投票，与all/ballot/activemask共同定义聚合谓词并影响分支收敛上存在可执行的直接衔接。
- [asc_ballot](asc_ballot.md)（`related`）：《asc_any》说明判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。；《asc_ballot》说明判断Warp中每个活跃线程的输入是否非零。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，返回一个32bit的无符号整数，若Warp内活跃线程输入的predicate不为0，则返回值中与线程Lane ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。。二者在asc_any对Warp活跃线程做投票，与all/ballot/activemask共同定义聚合谓词并影响分支收敛上存在可执行的直接衔接。
- [asc_all](asc_all.md)（`same_topic`）：《asc_any》说明判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。；《asc_all》说明判断是否所有活跃线程的输入均不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均不为0，返回1，否则返回0。Warp内所有活跃线程返回相同的结果。。二者在asc_any对Warp活跃线程做投票，与all/ballot/activemask共同定义聚合谓词并影响分支收敛上存在可执行的直接衔接。
<!-- cannbot:related:end -->
