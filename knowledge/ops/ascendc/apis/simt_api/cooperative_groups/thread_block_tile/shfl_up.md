---
type: API
title: ShflUp
description: 获取thread_block_tile组内当前线程向前偏移delta的线程的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/shfl_up.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ShflUp

获取thread_block_tile组内当前线程向前偏移delta的线程的数据。
函数原型：T shfl_up(T var, unsigned int delta) const
返回值：协作组内当前线程向前偏移delta的线程输入的var值。若偏移后超出组范围，返回当前线程输入的var值。
约束：仅支持thread_block_tile的模板参数Size小于等于32的场景，即仅支持单Warp内线程子组。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [ShflDown](shfl_down.md)（`related`）：ShflUp 沿相反方向取 lane，扫描/归约算法按方向选。
- [AscShflUp](../../warp_functions/warp_shfl_functions/asc_shfl_up.md)（`same_topic`）：thread_block_tile::ShflUp 与 AscShflUp 都从较低 lane 读取值；前者受 tile Size 约束，后者直接以 warp 为作用域。
- [ShflUp](../coalesced_group/shfl_up.md)（`same_topic`）：ShflUp 与《ShflUp》的实质衔接是：coalesced_group::shfl_up 在当前活跃线程子组内读取前 delta lane；组的构造与简介限定发散后的成员集合，generic shfl、shfl_down、thread_block_tile 和 Warp C API 给出索引方向及作用域对照。
<!-- cannbot:related:end -->
