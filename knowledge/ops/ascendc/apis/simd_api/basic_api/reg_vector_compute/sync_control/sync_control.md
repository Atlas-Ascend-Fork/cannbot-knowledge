---
type: API
title: 同步控制
description: Reg矢量计算同步控制接口索引页，包含LocalMemBar。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/sync_control/sync_control.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 同步控制

提供 LocalMemBar 接口，用于 Reg 矢量计算宏函数内不同流水线之间的同步。通过模板参数指定 src 源流水线和 dst 目的流水线，目的流水线等待源流水线上所有指令完成后才执行。

支持的流水线类型包括 VEC_STORE、VEC_LOAD、SCALAR_STORE、SCALAR_LOAD 等。当读写指令使用相同寄存器时硬件自动保序，无需插入同步；使用不同寄存器时需手动插入。仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。
