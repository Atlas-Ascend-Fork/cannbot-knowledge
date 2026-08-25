---
type: API
title: GetCmpMask
description: 获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/GetCmpMask_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCmpMask

获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。

逐元素比较两个tensor大小，如果比较后的结果为真，则输出结果的对应比特位为1，否则为0。计算结果存入CmpMask 128bit寄存器中，可用于后续Select计算，也可使用GetCmpMask接口获取寄存器保存的数据。 接口支持多种比较模式： - LT：小于（less than） - GT：大于（greater than） - GE：大于或等于（greater than or equal to） - EQ：等于（equal to） - NE：不等于（not equal to） - LE：小于或等于（less than or equal to）

本接口组包含 Compare（结果存入寄存器）, Compare（结果存入寄存器）, Compare（结果存入寄存器）, LocalTensor, Compare（结果存入寄存器）。

本接口属于 UB 矢量计算比较与选择接口。

约束：操作数地址对齐要求请参见通用地址对齐约束。；本接口没有repeat输入，repeat默认为1，即一条指令计算256B的数据。；本接口将结果写入128bit的CmpMask寄存器中，可以用GetCmpMask接口获取寄存器保存的数据。；对UB空间的占用说明。针对Ascend 950PR/Ascend 950DT，该接口占用8KB Unified Buffer临时空间。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
