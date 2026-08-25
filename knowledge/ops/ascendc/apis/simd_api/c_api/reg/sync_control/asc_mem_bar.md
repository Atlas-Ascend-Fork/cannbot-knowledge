---
type: API
title: AscMemBar
description: Reg计算宏函数内不同流水线之间的同步指令，目的流水线等待源流水线所有指令完成后执行。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/sync_control/asc_mem_bar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscMemBar

Reg计算宏函数内不同流水线之间的同步指令。该同步指令指定源流水线和目的流水线，如下图所示，目的流水线将等待源流水线上所有指令完成才进行执行。 读写场景下，当读指令使用的寄存器和写指令使用的寄存器相同时，可以触发寄存器保序，指令将会按照代码顺序执行，不需要插入同步指令，而当使用的寄存器不同时，如果要确保读写指令执行，则需要插入同步指令。写写场景同理。
函数原型：void asc_mem_bar(MEM_TYPE mem_type)
约束：读写依赖的场景下，如果读指令和写指令使用的寄存器相同，会触发寄存器保序，指令将会按照代码顺序执行，无需额外插入同步指令。；冗余的同步指令会导致性能下降，可以通过外提出循环或者循环切分避免多次调用同步指令。；当UB数据存在依赖时，才需要插入同步，判断是否有依赖取决于指令读写的内存是否有重叠。部分搬运指令读写内存的模式如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
