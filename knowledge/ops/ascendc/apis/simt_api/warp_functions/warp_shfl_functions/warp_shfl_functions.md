---
type: API
title: Warp Shfl类函数
description: 提供Warp级别的数据交换接口。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_shfl_functions/Warp_shfl_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Warp Shfl类函数

提供 Warp 内的数据交换接口，包括同步交换（asc_shfl）、前缀交换（asc_shfl_up）、后缀交换（asc_shfl_down）和蝶形交换（asc_shfl_xor）。这些函数允许同一 Warp 内不同 Lane 之间直接交换寄存器数据，无需经过共享内存，适用于 Warp 级别的并行规约和数据重排。

<!-- cannbot:related:start -->
## 相关

- [同一Warp内避免分支跳转](../../../../guides/operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md)（`explains`）：Warp Shfl类函数 与《同一Warp内避免分支跳转》的实质衔接是：Warp Shfl 总览覆盖 general/down/up/xor 四种 lane 交换；coalesced/tile 对应入口和分支优化指南说明作用域及真实使用。
- [AscShflXor](asc_shfl_xor.md)（`related`）：AscShflXor 与《Warp Shfl类函数》的实质衔接是：AscShflXor 与 up/down/general 及 ShflXor 入口共享 warp lane 交换契约；同 warp 避免分支指南直接使用此类 shuffle 做数据重排。
- [AscShfl](asc_shfl.md)（`same_topic`）：AscShfl 与《Warp Shfl类函数》的实质衔接是：AscShfl 与 up/down/xor 变体及 cooperative-group 对应入口共享 warp lane 交换契约，分支优化卡直接使用该类 warp 通信。
- [AscShflDown](asc_shfl_down.md)（`same_topic`）：AscShflDown 与《Warp Shfl类函数》的实质衔接是：AscShflDown 从较高 lane 读取值；general/up/xor 与 cooperative-group ShflDown 对照偏移方向和 warp/group 作用域。
- [AscShflUp](asc_shfl_up.md)（`same_topic`）：Warp Shfl类函数 与《AscShflUp》的实质衔接是：Warp Shfl 总览覆盖 general/down/up/xor 四种 lane 交换；coalesced/tile 对应入口和分支优化指南说明作用域及真实使用。
- [CoalescedGroup协作组shfl](../../cooperative_groups/coalesced_group/shfl.md)（`same_topic`）：Warp Shfl类函数 与《CoalescedGroup协作组shfl》的实质衔接是：Warp Shfl 总览覆盖 general/down/up/xor 四种 lane 交换；coalesced/tile 对应入口和分支优化指南说明作用域及真实使用。
- [ThreadBlockTile协作组shfl](../../cooperative_groups/thread_block_tile/shfl.md)（`same_topic`）：Warp Shfl类函数 与《ThreadBlockTile协作组shfl》的实质衔接是：Warp Shfl 总览覆盖 general/down/up/xor 四种 lane 交换；coalesced/tile 对应入口和分支优化指南说明作用域及真实使用。
- [Warp函数](../warp_functions.md)（`same_topic`）：Warp Shfl类函数 与《Warp函数》的实质衔接是：Warp Shfl 总览覆盖 general/down/up/xor 四种 lane 交换；coalesced/tile 对应入口和分支优化指南说明作用域及真实使用。
- [Warp函数](../warp_functions_intro.md)（`same_topic`）：Warp Shfl类函数 与《Warp函数》的实质衔接是：Warp Shfl 总览覆盖 general/down/up/xor 四种 lane 交换；coalesced/tile 对应入口和分支优化指南说明作用域及真实使用。
<!-- cannbot:related:end -->
