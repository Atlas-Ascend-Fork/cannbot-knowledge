---
type: API
title: Reg矢量计算概述
description: 逻辑计算支持以下接口：
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/logical_compute/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Reg矢量计算概述

逻辑计算支持以下接口：

（对RegTensor操作）、"basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"（对MaskReg操作）。 本节介绍两种接口，分别用于对RegTensor和MaskReg进行操作： - 对RegTensor操作： 根据mask对输入数据srcReg执行按位取反操作，将结果写入dstReg。 - 对MaskReg操作： 根据mask对输入数据src执行按位取反操作，将结果写入dst。

本接口组包含 Not, And, Or, Xor, ShiftLeft。

本接口属于 Reg 矢量计算逻辑运算接口，用于 RegTensor 数据的按位逻辑操作。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
