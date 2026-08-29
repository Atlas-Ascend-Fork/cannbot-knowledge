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

- [CoalescedGroup协作组shfl](shfl.md)（`same_topic`）：coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；获取coalesced_group组内当前线程向后偏移delta的线程的数据。。前者定义 coalesced_group 的指定线程寄存器读取原语，后者是以当前线程加 delta 计算来源线程的方向性变体，联合阅读可在同一组内交换任务中选择绝对 rank 或相对偏移。
<!-- cannbot:related:end -->
