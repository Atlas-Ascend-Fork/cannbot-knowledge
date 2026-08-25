---
type: API
title: ShflDown
description: 获取coalesced_group组内当前线程向后偏移delta的线程的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/shfl_down.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ShflDown

获取coalesced_group组内当前线程向后偏移delta的线程的数据。
函数原型：T shfl_down(T var, unsigned int delta) const
返回值：coalesced_group组内当前线程向后偏移delta的线程输入的var值。若偏移后超出组范围，返回当前线程输入的var值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [CoalescedGroup协作组shfl](shfl.md)（`related`）：通用 Shfl 按目标 rank 取值，而 ShflDown 按相对 delta 取值，用户需按索引表达方式选择。
- [ShflDown](../thread_block_tile/shfl_down.md)（`related`）：ThreadBlockTile 的 ShflDown 具有相似位移语义，但作用域是静态 tile 而不是活动线程形成的 coalesced group。
- [AscShflDown](../../warp_functions/warp_shfl_functions/asc_shfl_down.md)（`same_topic`）：AscShflDown 与《ShflDown》的实质衔接是：AscShflDown 从较高 lane 读取值；general/up/xor 与 cooperative-group ShflDown 对照偏移方向和 warp/group 作用域。
- [ShflUp](shfl_up.md)（`same_topic`）：ShflUp 与《ShflDown》的实质衔接是：coalesced_group::shfl_up 在当前活跃线程子组内读取前 delta lane；组的构造与简介限定发散后的成员集合，generic shfl、shfl_down、thread_block_tile 和 Warp C API 给出索引方向及作用域对照。
<!-- cannbot:related:end -->
