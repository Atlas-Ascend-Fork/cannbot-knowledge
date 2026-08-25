---
type: API
title: AscShfl
description: Warp级数据交换接口，按分组宽度获取指定线程持有的变量值，支持数据分发与动态交换场景
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_shfl_functions/asc_shfl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_shfl

Warp Shfl类接口主要实现Warp级数据交换，能够实现直接读取某个线程的数据，而不需要通过共享内存。这类接口主要通过Warp分组实现组内线程间的数据交换操作。

-   Warp分组

    Warp内的线程可分为多个组，用户通过参数width配置分组宽度（分组的线程数），分组内的线程可进行数据交换，组内线程通过相对组内起始线程位置来标识索引，称为逻辑Lane ID。

-   数据交换

    本接口主要是获取分组内指定线程持有的var值，用户通过参数src_lane指定线程。如果src_lane大于等于width，指定线程的逻辑Lane ID是src_lane%width。

主要使用场景

-   数据分发：将固定位置的线程数据广播给其他线程；
-   动态数据交换：每个线程从不同的源线程读取数据；

例如，Warp内32个活跃线程调用asc_shfl(LaneId, 5, 16)接口，每个线程的返回值为当前线程所在分组内线程编号为5的var值。

函数原型：inline int32_t asc_shfl(int32_t var, int32_t src_lane, int32_t width = warpSize)；inline uint32_t asc_shfl(uint32_t var, int32_t src_lane, int32_t width = warpSize)；inline float asc_shfl(float var, int32_t src_lane, int32_t width = warpSize) 等9种重载

参数：var（输入）：线程用于交换的输入操作数。；src_lane（输入）：期望获取的var值所在线程的Lane ID。；width（输入）：Warp内参与交换的线程的分组宽度，默认值为32。width的取值范围为(0, 32]，width必须是2的倍数。

返回值：Warp内指定线程的var值。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
约束：-   如果目标线程是非活跃状态，获取到寄存器中未初始化的值。
-   若入参width不是2的倍数或超出32，返回值异常。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [同一Warp内避免分支跳转](../../../../guides/operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md)（`explains`）：AscShfl 与《同一Warp内避免分支跳转》的实质衔接是：AscShfl 与 up/down/xor 变体及 cooperative-group 对应入口共享 warp lane 交换契约，分支优化卡直接使用该类 warp 通信。
- [CoalescedGroup协作组shfl](../../cooperative_groups/coalesced_group/shfl.md)（`related`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《AscShfl》说明Warp级数据交换接口，按分组宽度获取指定线程持有的变量值，支持数据分发与动态交换场景。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [ThreadBlockTile协作组shfl](../../cooperative_groups/thread_block_tile/shfl.md)（`related`）：AscShfl 与《ThreadBlockTile协作组shfl》的实质衔接是：AscShfl 与 up/down/xor 变体及 cooperative-group 对应入口共享 warp lane 交换契约，分支优化卡直接使用该类 warp 通信。
- [AscShflDown](asc_shfl_down.md)（`same_topic`）：AscShflDown 与《AscShfl》的实质衔接是：AscShflDown 从较高 lane 读取值；general/up/xor 与 cooperative-group ShflDown 对照偏移方向和 warp/group 作用域。
- [AscShflUp](asc_shfl_up.md)（`same_topic`）：AscShfl 与《AscShflUp》的实质衔接是：AscShfl 与 up/down/xor 变体及 cooperative-group 对应入口共享 warp lane 交换契约，分支优化卡直接使用该类 warp 通信。
- [AscShflXor](asc_shfl_xor.md)（`same_topic`）：AscShflXor 与《AscShfl》的实质衔接是：AscShflXor 与 up/down/general 及 ShflXor 入口共享 warp lane 交换契约；同 warp 避免分支指南直接使用此类 shuffle 做数据重排。
- [Warp Shfl类函数](warp_shfl_functions.md)（`same_topic`）：AscShfl 与《Warp Shfl类函数》的实质衔接是：AscShfl 与 up/down/xor 变体及 cooperative-group 对应入口共享 warp lane 交换契约，分支优化卡直接使用该类 warp 通信。
<!-- cannbot:related:end -->
