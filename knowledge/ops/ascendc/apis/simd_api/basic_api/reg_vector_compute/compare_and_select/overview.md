---
type: API
title: 比较与选择概述
description: 比较与选择支持以下接口：
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 比较与选择概述

比较与选择支持以下接口：

逐元素比较两个RegTensor大小，根据模板参数指定的比较模式，将比较结果写入目的操作数MaskReg中对应比特位，如果比较后的结果为真，则输出结果的对应比特位为1，否则为0。 其中cmp由模板参数mode指定比较模式，取值为EQ/GT/LT/GE/NE/LE。

本接口组包含 Compare, Compares, Select, Squeeze。

本接口属于 Reg 矢量计算比较与选择接口，用于 RegTensor 数据的比较和选择操作。

约束：通过mask参数控制的未选中元素在目的操作数中被置零。；操作数重叠约束：srcReg0和srcReg1可以是同一个RegTensor。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
