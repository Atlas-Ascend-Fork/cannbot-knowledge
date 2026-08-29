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
