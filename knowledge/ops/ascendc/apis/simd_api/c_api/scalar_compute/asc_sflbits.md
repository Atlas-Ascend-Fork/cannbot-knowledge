---
type: API
title: AscSflbits
description: 计算一个int64_t类型数字的二进制中，从最高数值位开始与符号位相同的连续比特位的个数。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_sflbits.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSflbits

计算一个int64_t类型数字的二进制中，从最高数值位开始与符号位相同的连续比特位的个数。 符号位为0，从最高数值位开始往后（不包含符号位）与符号位相同的连续比特数为3，故返回3。
函数原型：int64_t asc_sflbits(int64_t value)
返回值：返回从最高数值位开始和符号位相同的连续比特位的个数，数据类型为int64_t。
约束：当输入是-1（比特位全1）或者0（比特位全0）时，返回-1。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
