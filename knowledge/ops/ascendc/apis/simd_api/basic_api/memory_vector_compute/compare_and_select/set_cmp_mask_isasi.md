---
type: API
title: SetCmpMask
description: 设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/SetCmpMask_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetCmpMask(ISASI)

## 产品支持情况

- Ascend 950PR/Ascend 950DT：支持

- Atlas A3 训练系列产品/Atlas A3 推理系列产品：支持

- Atlas A2 训练系列产品/Atlas A2 推理系列产品：支持

- Atlas 200I/500 A2 推理产品：不支持

- Atlas 推理系列产品 AI Core：支持

- Atlas 推理系列产品 Vector Core：不支持

- Atlas 训练系列产品：不支持

## 功能说明

头文件路径为：`"basic_api/kernel_operator_vec_cmpsel_intf.h"`。

设置比较寄存器的值，配合不传入mask参数的Select接口使用，根据不同的selMode传入不同的数据。

- 模式0（SELMODE::VSEL_CMPMASK_SPR）

    SetCmpMask中传入selMask LocalTensor。

- 模式1（SELMODE::VSEL_TENSOR_SCALAR_MODE）

    SetCmpMask中传入src1 LocalTensor。

- 模式2（SELMODE::VSEL_TENSOR_TENSOR_MODE）

    SetCmpMask中传入LocalTensor，LocalTensor中存放的是selMask的地址。

## 函数原型

## 参数说明

**表1**  模板参数说明

**表2**  参数说明

## 数据类型

支持数据类型为：b8、b16、b32、b64。

## 返回值说明

无

## 约束说明

无

## 调用示例

- 当selMode为模式0或模式2时：



- 当selMode为模式1时：
