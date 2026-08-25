---
type: API
title: AscShflXor
description: 获取Warp内当前线程Lane ID与lane_mask异或后对应线程的变量值，支持width分组
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_shfl_functions/asc_shfl_xor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_shfl_xor

获取Warp内当前线程Lane ID与输入lane_mask做异或操作（Lane ID ^ lane_mask）得到的dstLaneId对应线程输入的用于交换的var值；如果目标线程是非活跃状态，获取到寄存器中未初始化的值。其中，参数width用于划分Warp内线程的分组。参数width设置参与交换的32个线程的分组宽度，默认值为32，即所有线程分为1组。

在多个分组场景（width小于32）下，每个线程获取位于本组内或线程编号更小的组内的dstLaneId对应线程的var值；也就是说，如果dstLaneId小于当前线程所在分组的起始Lane ID，dstLaneId对应的线程位于线程编号更小的组内，则可以获取该dstLaneId线程的var值；如果dstLaneId大于当前线程所在分组的最大Lane ID，则返回当前线程的var值。

例如，Warp内32个活跃线程调用asc_shfl_xor(LaneId, 1, 16)接口，每个线程的返回值为当前线程Lane ID ^ 1对应线程的var值。

函数原型：inline int32_t asc_shfl_xor(int32_t var, int32_t lane_mask, int32_t width = warpSize)；inline uint32_t asc_shfl_xor(uint32_t var, int32_t lane_mask, int32_t width = warpSize)；inline float asc_shfl_xor(float var, int32_t lane_mask, int32_t width = warpSize) 等9种重载

参数：var（输入）：线程用于交换的输入操作数。；lane_mask（输入）：与当前线程Lane ID做异或运算的操作数。取值范围为[0, 32)，且小于width。；width（输入）：Warp内参与交换的线程的分组宽度，默认值为32。width的取值范围为(0, 32]，width必须是2的倍数。

返回值：Warp内指定线程的var值。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
约束：如果目标线程是非活跃状态，获取到寄存器中未初始化的值。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [同一Warp内避免分支跳转](../../../../guides/operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md)（`explains`）：AscShflXor 与《同一Warp内避免分支跳转》的实质衔接是：AscShflXor 与 up/down/general 及 ShflXor 入口共享 warp lane 交换契约；同 warp 避免分支指南直接使用此类 shuffle 做数据重排。
- [AscShflUp](asc_shfl_up.md)（`related`）：AscShflXor 按 laneMask 配对交换，适合蝶形归约；AscShflUp 的有向偏移更适合扫描，二者给出算法选型。
- [ShflXor](../../cooperative_groups/thread_block_tile/shfl_xor.md)（`related`）：AscShflXor 与《ShflXor》的实质衔接是：AscShflXor 与 up/down/general 及 ShflXor 入口共享 warp lane 交换契约；同 warp 避免分支指南直接使用此类 shuffle 做数据重排。
- [Warp Shfl类函数](warp_shfl_functions.md)（`related`）：AscShflXor 与《Warp Shfl类函数》的实质衔接是：AscShflXor 与 up/down/general 及 ShflXor 入口共享 warp lane 交换契约；同 warp 避免分支指南直接使用此类 shuffle 做数据重排。
- [AscShfl](asc_shfl.md)（`same_topic`）：AscShflXor 与《AscShfl》的实质衔接是：AscShflXor 与 up/down/general 及 ShflXor 入口共享 warp lane 交换契约；同 warp 避免分支指南直接使用此类 shuffle 做数据重排。
- [AscShflDown](asc_shfl_down.md)（`same_topic`）：AscShflXor 与《AscShflDown》的实质衔接是：AscShflXor 与 up/down/general 及 ShflXor 入口共享 warp lane 交换契约；同 warp 避免分支指南直接使用此类 shuffle 做数据重排。
<!-- cannbot:related:end -->
