---
type: Guide
title: 编译与执行约束说明
description: 编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/compilation_and_execution/operator_compilation/constraints.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 约束说明

- 在同一个编译单元，若存在多个核函数，暂不支持自动推导Kernel类型，需要开发者手动设置Kernel类型。
- 特别地，针对如下型号，无论是否是同一个编译单元多个核函数的场景，均不支持在开发者未设置Kernel类型时进行自动推导。建议开发者手动设置Kernel类型。
- Ascend 950PR/Ascend 950DT
- Atlas 推理系列产品
- Kernel函数推荐使用 __cube__ / __vector__ / __mix__(cube, vec)进行标记，KERNEL_TASK_TYPE_DEFAULT接口即将废弃。
- 纯Scalar算子无法实现自动推导
需手动标记Kernel函数类型，推荐设置为纯Vector类型，添加__vector__ attribute进行标记：
- bfloat16_t等数据类型在Host端仅支持以C++模板的形式进行定义与声明，具体数据类型如下：
Ascend 950PR/Ascend 950DT：bfloat16_t、hifloat8_t、fp8_e5m2_t、fp8_e4m3fn_t、fp8_e8m0_t、fp4x2_e2m1_t、fp4x2_e1m2_t、int4x2_t。
Atlas A2 训练系列产品/Atlas A2 推理系列产品：bfloat16_t。
Atlas A3 训练系列产品/Atlas A3 推理系列产品：bfloat16_t。
- 暂不支持在函数空间外定义和使用device侧的字符串字面量。例如：
