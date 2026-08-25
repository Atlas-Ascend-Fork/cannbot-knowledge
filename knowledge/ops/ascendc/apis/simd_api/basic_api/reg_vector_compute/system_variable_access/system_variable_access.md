---
type: API
title: 系统变量访问
description: 寄存器矢量系统变量访问接口集合，包含ClearSpr接口。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/system_variable_access/system_variable_access.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 系统变量访问

提供 ClearSpr 接口，用于对指定的特殊目的寄存器（SpecialPurposeReg）进行清零操作。通过模板参数 spr 指定目标寄存器，当前支持 AR 寄存器（配合 Squeeze 接口存储有效元素总字节数）。

该接口只能在 VF 函数内调用，命名空间为 AscendC::Reg。仅 Ascend 950PR/Ascend 950DT 支持。
