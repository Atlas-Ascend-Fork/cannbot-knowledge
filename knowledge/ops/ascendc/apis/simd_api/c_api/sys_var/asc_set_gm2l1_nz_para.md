---
type: API
title: AscSetGm2l1NzPara
description: 设置MTE2_NZ_PARA寄存器值，用于DN2NZ搬运前配置参数。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_gm2l1_nz_para.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetGm2l1NzPara

对MTE2_NZ_PARA寄存器中的值进行设置，可以在调用asc_copy_gm2l1_dn2nz和asc_copy_gm2l1_nd2nz前设置相关参数。 MTE2_NZ_PARA是一个64bit的寄存器，其中各bit含义如下： 表1 MTE2_NZ_PARA寄存器比特位说明
函数原型：void asc_set_gm2l1_nz_para(uint64_t config)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
