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

- [Ascend950 DataCopy 写回 L2 驱逐丢对角线](../../../../runbooks/precision/ascend950_datacopy_l2.md)（`exemplifies`）：AscDcci 与《Ascend950 DataCopy 写回 L2 驱逐丢对角线》的实质衔接是：AscDcci 的 single/entire 变体与 C++ DataCacheCleanAndInvalid 操作同一 DCache；缓存概述、L2 驱逐故障和编译选项提供验证与尾开销决策。
- [arch35 小 per-channel 输出读旧值判别与规避](../../../../runbooks/compilation/arch35_per_channel.md)（`exemplifies`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《AscDcci》提供“刷新Data Cache保证与GM一致性，支持单Cache Line刷新和整片刷新，用于多核数据一致性和Scalar写GM场景。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
- [设置DCI编译选项来减少算子尾开销](../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/dci_compile_option.md)（`explains`）：AscDcci 与《设置DCI编译选项来减少算子尾开销》的实质衔接是：AscDcci 的 single/entire 变体与 C++ DataCacheCleanAndInvalid 操作同一 DCache；缓存概述、L2 驱逐故障和编译选项提供验证与尾开销决策。
- [AscAtomicSub](../scalar_compute/asc_atomic_sub.md)（`related`）：AscAtomicSub 与《AscDcci》的实质衔接是：SIMT asc_atomic_sub 是同一 GM 原子减；原子加提供逆操作对照，绕过 DCache 的读写和 AscDcci 共同落实 focal 明示的缓存一致性要求。
- [DataCacheCleanAndInvalid](../../basic_api/cache_control/data_cache_clean_and_invalid.md)（`related`）：AscDcci 与《DataCacheCleanAndInvalid》的实质衔接是：AscDcci 的 single/entire 变体与 C++ DataCacheCleanAndInvalid 操作同一 DCache；缓存概述、L2 驱逐故障和编译选项提供验证与尾开销决策。
- [DataCachePreload](../../basic_api/cache_control/data_cache_preload.md)（`related`）：DataCachePreload 与《AscDcci》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [WriteGmByPassDCache](../../basic_api/scalar_compute/write_gm_by_pass_d_cache_isasi.md)（`related`）：AscDcci 是 C API 的数据缓存清理/失效入口，可与 bypass 写对照确定是维护已有缓存行还是避免写入 DCache。
- [asc_dcci_single](../../../simt_api/memory_access_functions/asc_dcci_single.md)（`related`）：AscDcci 与《asc_dcci_single》的实质衔接是：AscDcci 的 single/entire 变体与 C++ DataCacheCleanAndInvalid 操作同一 DCache；缓存概述、L2 驱逐故障和编译选项提供验证与尾开销决策。
- [系统缓存概述（缓存控制）](../../basic_api/cache_control/system_cache_overview.md)（`related`）：AscDcci 与《系统缓存概述（缓存控制）》的实质衔接是：AscDcci 的 single/entire 变体与 C++ DataCacheCleanAndInvalid 操作同一 DCache；缓存概述、L2 驱逐故障和编译选项提供验证与尾开销决策。
- [asc_dcci_entire](../../../simt_api/memory_access_functions/asc_dcci_entire.md)（`same_topic`）：asc_dcci_entire 与《AscDcci》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_ldcg（内存访问函数）](../../../simt_api/memory_access_functions/asc_ldcg.md)（`same_topic`）：asc_ldcg（内存访问函数） 与《AscDcci》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [asc_stwt（内存访问函数）](../../../simt_api/memory_access_functions/asc_stwt.md)（`same_topic`）：asc_stwt（内存访问函数） 与《AscDcci》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
<!-- cannbot:related:end -->
