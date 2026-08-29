---
type: API
title: AscCeil
description: 将src中的浮点数元素按照CEIL（向正无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_ceil.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscCeil

将src中的浮点数元素按照CEIL（向正无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。

关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half。

约束：float类型只支持不饱和模式。

仅 Ascend 950PR/Ascend 950DT 支持。
