---
type: API
title: asc_activemask
description: 查看Warp内所有线程是否为活跃状态。 返回一个32bit的无符号整数，若Warp内某个线程是活跃（已结束线程是非活跃状态）的，则返回值中与线程Lane
  ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_vote_functions/asc_activemask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_activemask

查看Warp内所有线程是否为活跃状态。

返回一个32bit的无符号整数，若Warp内某个线程是活跃（已结束线程是非活跃状态）的，则返回值中与线程Lane ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。

函数原型：inline uint32_t asc_activemask()

返回值：32bit的无符号整数：若Warp内某个线程是活跃的，则返回值中与线程Lane ID对应的bit位为1，否则为0。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [asc_any](asc_any.md)（`related`）：《asc_any》说明判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。；《asc_activemask》说明查看Warp内所有线程是否为活跃状态。 返回一个32bit的无符号整数，若Warp内某个线程是活跃（已结束线程是非活跃状态）的，则返回值中与线程Lane ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。。二者在asc_any对Warp活跃线程做投票，与all/ballot/activemask共同定义聚合谓词并影响分支收敛上存在可执行的直接衔接。
- [asc_ballot](asc_ballot.md)（`related`）：asc_activemask 返回当前活跃 lane 位图，asc_ballot 返回活跃 lane 中 predicate 为真的位图；两者可相与或比较判断分支参与情况。
- [asc_all](asc_all.md)（`same_topic`）：asc_all 与《asc_activemask》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
<!-- cannbot:related:end -->
