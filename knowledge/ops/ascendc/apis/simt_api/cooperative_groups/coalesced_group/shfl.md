---
type: API
title: CoalescedGroup协作组shfl
description: coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/shfl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# CoalescedGroup协作组shfl

coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。
函数原型：T shfl(T var, int src_rank) const
返回值：coalesced_group组内指定线程输入的var值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [SIMT 切分未 coalesce 致 block 边界错位](../../../../runbooks/precision/simt_coalesce_block.md)（`exemplifies`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《SIMT 切分未 coalesce 致 block 边界错位》说明多维大 shape 随机算子触发 SIMT split-block 切分时，op_host 侧 InitTensorSliceState 直接写原始多维 shape，未像 PyTorch TensorIterator 那样先 coalesce_dimensions，使 block0 numel 比参考实现少 stride[0]/2，block1 首元素 global idx 整体错位、counter 跳变点位置错。判别信号：block1 首 idx 与期望差恰好等于 stride[0]/2。。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [AscShfl](../../warp_functions/warp_shfl_functions/asc_shfl.md)（`related`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《AscShfl》说明Warp级数据交换接口，按分组宽度获取指定线程持有的变量值，支持数据分发与动态交换场景。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [CoalescedGroup](coalesced_group.md)（`related`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《CoalescedGroup》说明SIMT协作线程组coalesced_group接口集合，涵盖构造、同步、尺寸查询、shuffle和投票等操作。。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [ShflDown](shfl_down.md)（`related`）：通用 Shfl 按目标 rank 取值，而 ShflDown 按相对 delta 取值，用户需按索引表达方式选择。
- [ThreadBlockTile协作组shfl](../thread_block_tile/shfl.md)（`related`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《ThreadBlockTile协作组shfl》说明thread_block_tile组内线程的数据交换接口，用于获取组内指定rank线程输入的var值。。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [coalesced_group简介](coalesced_group_intro.md)（`related`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《coalesced_group简介》说明在SIMT架构的硬件层面上，处理器以32个线程为一组（一个Warp）来执行线程。如果核函数代码中的条件分支导致Warp内的线程出现发散（Warp Divergence），那么Warp会串行执行每个分支，在执行某个分支时会屏蔽不在该指令路径上的线程。coalesced_group用于获取当前Warp中实际活跃的线程子集。。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [ShflUp](shfl_up.md)（`same_topic`）：《CoalescedGroup协作组shfl》说明coalesced_group组内线程的数据交换接口，不通过共享内存实现直接读取组内指定线程的寄存器中的值。；《ShflUp》说明获取coalesced_group组内当前线程向前偏移delta的线程的数据。。二者在coalesced_group shfl直接读取组内目标线程寄存器，up/down、Warp shfl及切分后coalesce合同决定lane映射上存在可执行的直接衔接。
- [Warp Shfl类函数](../../warp_functions/warp_shfl_functions/warp_shfl_functions.md)（`same_topic`）：Warp Shfl类函数 与《CoalescedGroup协作组shfl》的实质衔接是：Warp Shfl 总览覆盖 general/down/up/xor 四种 lane 交换；coalesced/tile 对应入口和分支优化指南说明作用域及真实使用。
<!-- cannbot:related:end -->
