---
type: API
title: AscCopy
description: 完成矢量寄存器之间、掩码寄存器之间以及矢量寄存器到掩码寄存器的数据搬运。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_copy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscCopy

完成数据在寄存器间的搬运，支持以下三种模式： 具体搬运原理请参考关键特性说明。
函数原型：void asc_copy(vector_int8_t& dst, vector_int8_t src, vector_bool mask)
约束：针对矢量数据寄存器复制到矢量数据寄存器：dst中未被mask筛选的位置保持原值。；针对掩码寄存器复制到掩码寄存器：带mask的接口dst中未被mask筛选的位置填0。；针对矢量寄存器复制到掩码寄存器：part的值必须在编译期确定，可传入整数字面量或constexpr整数常量，不支持传入运行时变量。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
