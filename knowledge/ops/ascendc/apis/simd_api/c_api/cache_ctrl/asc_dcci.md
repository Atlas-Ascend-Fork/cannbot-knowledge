---
type: API
title: AscDcci
description: 刷新Data Cache保证与GM一致性，支持单Cache Line刷新和整片刷新，用于多核数据一致性和Scalar写GM场景。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_dcci.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscDcci

在AI Core内部，Scalar单元和DMA单元都可能对Global Memory进行访问。

 \\

如上图所示
DMA搬运单元读写Global Memory，数据通过asc_copy_ub2gm和asc_copy_gm2ub等接口在UB等Local Memory和Global Memory间交互，没有Cache一致性问题；
Scalar单元访问Global Memory，首先会访问每个核内的Data Cache，因此存在Data Cache与Global Memory的Cache一致性问题。
该接口用来刷新Cache，保证Cache的一致性，使用场景
读取Global Memory的数据，但该数据可能在外部被其余核修改，此时需要使用asc_dcci接口，直接访问Global Memory，获取最新数据；
用户通过Scalar单元写Global Memory的数据，希望立刻写出，也需要使用asc_dcci接口。

参数：dst(输入): 需要刷新缓存的向量的起始地址。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [arch35 小 per-channel 输出读旧值判别与规避](../../../../runbooks/compilation/arch35_per_channel.md)（`exemplifies`）：Runbook 的直接信号是“per-channel ［C］ 小输出经 `DataCopyPad` 写 GM 后，host/下游读到旧值或错值”；asc_dcci 的适用条件是“读取Global Memory的数据，但该数据可能在外部被其余核修改，此时需要使用asc_dcci接口，直接访问Global Memory，获取最新数据；”。API语义帮助判定该旧值现象是否属于多核缓存一致性路径。
- [AscAtomicExch](../scalar_compute/asc_atomic_exch.md)（`related`）：原子交换接口明确“Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。”；缓存接口解释“Scalar单元访问Global Memory，首先会访问每个核内的Data Cache，因此存在Data Cache与Global Memory的Cache一致性问题。”，给出交换前后插入 DCCI 的一致性原因。
- [AscAtomicInc](../scalar_compute/asc_atomic_inc.md)（`related`）：原子递增接口明确“Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。”；缓存接口解释“Scalar单元访问Global Memory，首先会访问每个核内的Data Cache，因此存在Data Cache与Global Memory的Cache一致性问题。”，给出原子计数器与普通 Scalar/DMA 访问混用时必须补 DCCI 的原因。
- [AscAtomicMax](../scalar_compute/asc_atomic_max.md)（`related`）：需要调用asc_dcci接口确保GM与DCache的一致性；存在Data Cache与Global Memory的Cache一致性问题；连接原子操作的明确后置要求与缓存一致性契约。
- [AscAtomicSub](../scalar_compute/asc_atomic_sub.md)（`related`）：Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。；该接口用来刷新Cache，保证Cache的一致性；AscAtomicSub 明确产生绕过 DCache 的 GM 更新，AscDcci 提供后续缓存一致性动作，二者构成原子写后的必要维护链。
- [AscAtomicXor](../scalar_compute/asc_atomic_xor.md)（`related`）：AscAtomicXor 卡告警“Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。”；AscDcci 卡解释“用户通过Scalar单元写Global Memory的数据，希望立刻写出，也需要使用asc_dcci接口。”，给出原子写 GM 后刷新缓存的直接一致性合同。
<!-- cannbot:related:end -->
