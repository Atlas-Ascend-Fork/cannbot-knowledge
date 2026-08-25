---
type: Guide
title: Scalar读写数据
description: Scalar计算单元仅支持读写Global Memory和Unified Buffer，介绍其读写方式及同步机制。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/concepts_and_terms/memory_access/scalar_read_write.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Scalar读写数据

AI Core中Scalar计算单元负责各类型的标量数据运算和程序的流程控制。根据硬件架构设计，Scalar仅支持对Global Memory和Unified Buffer的读写操作，而不支持对L1 Buffer、L0A Buffer、L0B Buffer和L0C Buffer等其他类型存储的访问。下文分别介绍了Scalar读写Global Memory和Unified Buffer的方式和Scalar读写数据时的同步机制。
## Scalar读写Global Memory
如上图所示，Scalar读写GM数据时会经过DataCache，DataCache主要用于提高标量访存指令的执行效率，每一个AIC/AIV核内均有一个独立的DataCache。下面通过一个具体示例来讲解DataCache的具体工作机制。
globalTensor1是位于GM上的Tensor：
-   执行完GetValue(0)后，globalTensor1的前8个元素会进入DataCache，后续GetValue(1)\~GetValue(7)不需要再访问GM，而可以直接从DataCache的Cache Line中读取数据，提高了标量连续访问的效率。
-   执行完SetValue(8, val)后，globalTensor1的index为8\~15的元素会进入DataCache，SetValue只会修改DataCache中的Cache Line数据，同时将Cache Line的状态设置为Dirty，表明Cache Line中的数据与GM中的数据不一致。
根据上文的工作机制（如下图所示），多核间访问globalTensor1会出现数据不一致的情况，如果其余核需要获取GM数据的变化，则需要开发者手动调用DataCacheCleanAndInvalid来保证数据的一致性。
## Scalar读写Unified Buffer
Scalar读写Unified Buffer时，可以使用LocalTensor的SetValue和GetValue接口。示例如下：
## Scalar读写数据时的同步
Scalar读写Global Memory和Unified Buffer时属于PIPE_S（Scalar流水）操作，当用户使用SetValue或者GetValue接口，且算子工程开启自动同步时，不需要手动插入同步事件。
如果用户关闭算子工程的自动同步功能时，则需要手动插入同步事件：

<!-- cannbot:related:start -->
## 相关

- [SetValue](../../../../apis/simd_api/basic_api/data_structures/global_tensor/set_value.md)（`explains`）：《SetValue》的任务是“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”。《Scalar读写数据》具体提供“Scalar计算单元仅支持读写Global Memory和Unified Buffer，介绍其读写方式及同步机制。”，它直接用于GlobalTensor 标量写入后的 DCache 可见性与 GetValue 验证。
- [asc_dcci_entire](../../../../apis/simt_api/memory_access_functions/asc_dcci_entire.md)（`explains`）：asc_dcci_entire 与《Scalar读写数据》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
- [asc_ldcg（内存访问函数）](../../../../apis/simt_api/memory_access_functions/asc_ldcg.md)（`explains`）：asc_ldcg（内存访问函数） 与《Scalar读写数据》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
- [asc_stwt（内存访问函数）](../../../../apis/simt_api/memory_access_functions/asc_stwt.md)（`explains`）：asc_stwt（内存访问函数） 与《Scalar读写数据》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
- [GM SetValue 写回后 GetValue 读到旧值](../../../../runbooks/precision/gm_setvalue_getvalue_reads_stale_within_kernel.md)（`related`）：Scalar 读写指南要求 GM 写入后处理缓存一致性；该 runbook 给出同一 Kernel 内 SetValue 后 GetValue 读旧值的具体失效信号。
- [VF 归约落 UB 后 GetValue 读取陈旧标量](../../../../runbooks/precision/vector_scalar_ub_handoff_requires_explicit_completion.md)（`related`）：指南中的 Scalar↔UB 访问还需尊重异步 Vector 流水；该卡验证 StoreAlign 后立即 GetValue 会读陈旧标量，并给出完成边界。
<!-- cannbot:related:end -->
