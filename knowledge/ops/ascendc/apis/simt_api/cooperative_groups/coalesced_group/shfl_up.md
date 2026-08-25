---
type: API
title: ShflUp
description: 获取coalesced_group组内当前线程向前偏移delta的线程的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/shfl_up.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ShflUp

获取coalesced_group组内当前线程向前偏移delta的线程的数据。
函数原型：T shfl_up(T var, unsigned int delta) const
返回值：coalesced_group组内当前线程向前偏移delta的线程输入的var值。若偏移后超出组范围，返回当前线程输入的var值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [CoalescedGroup](coalesced_group.md)（`related`）：ShflUp 与《CoalescedGroup》的实质衔接是：coalesced_group::shfl_up 在当前活跃线程子组内读取前 delta lane；组的构造与简介限定发散后的成员集合，generic shfl、shfl_down、thread_block_tile 和 Warp C API 给出索引方向及作用域对照。
- [coalesced_group简介](coalesced_group_intro.md)（`related`）：ShflUp 与《coalesced_group简介》的实质衔接是：coalesced_group::shfl_up 在当前活跃线程子组内读取前 delta lane；组的构造与简介限定发散后的成员集合，generic shfl、shfl_down、thread_block_tile 和 Warp C API 给出索引方向及作用域对照。
- [AscShflUp](../../warp_functions/warp_shfl_functions/asc_shfl_up.md)（`same_topic`）：ShflUp 与《AscShflUp》的实质衔接是：coalesced_group::shfl_up 在当前活跃线程子组内读取前 delta lane；组的构造与简介限定发散后的成员集合，generic shfl、shfl_down、thread_block_tile 和 Warp C API 给出索引方向及作用域对照。
- [CoalescedGroup协作组shfl](shfl.md)（`same_topic`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《ShflUp》说明获取coalesced_group组内当前线程向前偏移delta的线程的数据。。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [ShflDown](shfl_down.md)（`same_topic`）：ShflUp 与《ShflDown》的实质衔接是：coalesced_group::shfl_up 在当前活跃线程子组内读取前 delta lane；组的构造与简介限定发散后的成员集合，generic shfl、shfl_down、thread_block_tile 和 Warp C API 给出索引方向及作用域对照。
- [ShflUp](../thread_block_tile/shfl_up.md)（`same_topic`）：ShflUp 与《ShflUp》的实质衔接是：coalesced_group::shfl_up 在当前活跃线程子组内读取前 delta lane；组的构造与简介限定发散后的成员集合，generic shfl、shfl_down、thread_block_tile 和 Warp C API 给出索引方向及作用域对照。
<!-- cannbot:related:end -->
