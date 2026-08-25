---
type: API
title: GetCtrlSpr
description: 读取CTRL寄存器特定比特位上的值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/GetCtrlSpr_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetCtrlSpr

头文件路径为："basic_api/kernel_operator_common_intf.h"。

读取CTRL寄存器（控制寄存器）特定比特位上的值。

参数：startBit: 起始比特位索引。；endBit: 终止比特位索引。

支持数据类型：本接口为寄存器访问接口，不涉及张量数据类型操作。返回值类型固定为int64_t。

约束：- startBit和endBit的取值范围为[0, 63]。
- startBit小于等于endBit。
- 各比特位的说明

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
