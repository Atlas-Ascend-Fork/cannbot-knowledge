---
type: API
title: SetCtrlSpr
description: 对CTRL寄存器的特定比特位进行设置，通过模板参数指定比特位范围并写入对应值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/SetCtrlSpr_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# SetCtrlSpr

头文件路径为："basic_api/kernel_operator_common_intf.h"。

对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。

参数：startBit: 起始比特位索引。；endBit: 终止比特位索引。；value(输入): 起止比特位上新设置的值。；CTRL寄存器比特位: 默认值；CTRL[8:6]: 3'b000；CTRL[10:9]: 2'b00；CTRL[45]: 1'b0；CTRL[48]: 1'b0。

支持数据类型：本接口为寄存器访问接口，不涉及张量数据类型操作。参数value类型固定为int64_t。

约束：- Ascend 950PR/Ascend 950DT仅支持CTRL[8:6]、CTRL[10:9]、CTRL[45]、CTRL[48]、CTRL[50]、CTRL[53]、CTRL[59]、CTRL[60]比特位。

- Atlas A3 训练系列产品/Atlas A3 推理系列产品仅支持CTRL[48]比特位。

- Atlas A2 训练系列产品/Atlas A2 推理系列产品仅支持CTRL[48]比特位。

- Ascend 950PR/Ascend 950DT对于CTRL[8:6]和CTRL[10:9]的设置，已封装原子操作API，建议通过这些原子操作API进行配置。
  - SetAtomicType
  - DisableDmaAtomic
  - SetAtomicAdd
  - SetAtomicMax
  - SetAtomicMin

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
