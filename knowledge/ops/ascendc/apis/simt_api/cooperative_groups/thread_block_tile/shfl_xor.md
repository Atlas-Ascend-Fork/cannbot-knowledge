---
type: API
title: ShflXor
description: 将当前线程的rank与lane_mask进行按位异或运算得到的rank，获取该rank的线程输入的var值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/shfl_xor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ShflXor

将当前线程的rank与lane_mask进行按位异或运算得到的rank，获取该rank的线程输入的var值。
函数原型：T shfl_xor(T var, unsigned int lane_mask) const
返回值：thread_block_tile组内指定线程的var值。
约束：仅支持thread_block_tile的模板参数Size小于等于32的场景，即仅支持单Warp内线程子组。；lane_mask必须小于thread_block_tile组内线程数。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscShflXor](../../warp_functions/warp_shfl_functions/asc_shfl_xor.md)（`related`）：AscShflXor 与《ShflXor》的实质衔接是：AscShflXor 与 up/down/general 及 ShflXor 入口共享 warp lane 交换契约；同 warp 避免分支指南直接使用此类 shuffle 做数据重排。
- [ThreadBlockTile协作组shfl](shfl.md)（`same_topic`）：ShflXor 按 laneMask 翻转 rank 位进行蝶形交换，focal Shfl 则固定读取指定 rank；归约/扫描的通信拓扑由此决定。
<!-- cannbot:related:end -->
