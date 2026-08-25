---
type: API
title: ThreadBlockTile协作组shfl
description: thread_block_tile组内线程的数据交换接口，用于获取组内指定rank线程输入的var值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/shfl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlockTile协作组shfl

thread_block_tile组内线程的数据交换接口，用于获取组内指定rank线程输入的var值。
函数原型：T shfl(T var, int src_rank) const
返回值：thread_block_tile组内指定线程输入的var值。
约束：在跨Warp的thread_block_tile场景（Size>32）下；必须保证thread_block_tile组内线程指定相同的src_rank，否则是未定义行为。；必须保证thread_block_tile组内线程均处于活跃状态，否则是未定义行为。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscShfl](../../warp_functions/warp_shfl_functions/asc_shfl.md)（`related`）：AscShfl 与《ThreadBlockTile协作组shfl》的实质衔接是：AscShfl 与 up/down/xor 变体及 cooperative-group 对应入口共享 warp lane 交换契约，分支优化卡直接使用该类 warp 通信。
- [CoalescedGroup协作组shfl](../coalesced_group/shfl.md)（`related`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《ThreadBlockTile协作组shfl》说明thread_block_tile组内线程的数据交换接口，用于获取组内指定rank线程输入的var值。。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [ShflDown](shfl_down.md)（`same_topic`）：Shfl 从绝对 src_rank 取值，ShflDown 从当前 rank 加 delta 取值；两者对应广播指定 lane 与向下邻域交换两类通信模式。
- [ShflXor](shfl_xor.md)（`same_topic`）：ShflXor 按 laneMask 翻转 rank 位进行蝶形交换，focal Shfl 则固定读取指定 rank；归约/扫描的通信拓扑由此决定。
- [Warp Shfl类函数](../../warp_functions/warp_shfl_functions/warp_shfl_functions.md)（`same_topic`）：Warp Shfl类函数 与《ThreadBlockTile协作组shfl》的实质衔接是：Warp Shfl 总览覆盖 general/down/up/xor 四种 lane 交换；coalesced/tile 对应入口和分支优化指南说明作用域及真实使用。
<!-- cannbot:related:end -->
