---
type: API
title: AscSetL0c2gmReluAlpha
description: 设置RELU_ALPHA寄存器值，存储Scalar ReLU使用的alpha值。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_l0c2gm_relu_alpha.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetL0c2gmReluAlpha

对RELU_ALPHA寄存器中的值进行设置。这是一个64bit的寄存器，存储在fixpipe或cube指令中进行Scalar ReLU时使用的alpha值。 其中各bit含义如下： 表1 RELU_ALPHA寄存器比特位说明
函数原型：void asc_set_l0c2gm_relu_alpha(uint64_t config)
参数：config（输入）：待设置的寄存器值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
