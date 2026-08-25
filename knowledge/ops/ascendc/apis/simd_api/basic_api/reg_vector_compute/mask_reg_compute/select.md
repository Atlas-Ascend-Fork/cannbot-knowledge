---
type: API
title: Select
description: 根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/MaskReg_compute/Select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Select

头文件路径为："basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。

给定两个源操作数src0和src1，根据mask的比特位值选取元素，得到目的操作数dst。选择的规则为：当mask的比特位是1时，从src0中选取对应位置的数，比特位是0时从src1选取对应位置的数。

参数：dst: 目的操作数，类型为MaskReg。；src0: 源操作数，类型为MaskReg。；src1: 源操作数，类型为MaskReg。；mask: 指示选择src0或src1，类型为MaskReg。

仅 Ascend 950PR/Ascend 950DT 支持。
