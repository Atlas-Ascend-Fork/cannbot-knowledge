---
type: API
title: AscSetL0c2gmQuantPost
description: 设置QUANT_POST寄存器值，存储Fixpipe后处理阶段量化信息。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_l0c2gm_quant_post.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetL0c2gmQuantPost

对QUANT_POST寄存器中的值进行设置, QUANT_POST是一个64bit的寄存器，存储Fixpipe后处理阶段量化信息。 其中各bit含义如下，其中各种量化模式的说明可见asc_copy_l0c2l1中对各种量化模式的说明： 表1 QUANT_POST寄存器比特位说明
函数原型：void asc_set_l0c2gm_quant_post(uint64_t config)
参数：config（输入）：待设置的寄存器值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
