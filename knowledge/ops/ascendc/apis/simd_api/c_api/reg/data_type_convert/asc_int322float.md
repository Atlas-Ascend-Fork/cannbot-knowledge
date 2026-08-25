---
type: API
title: AscInt322Float
description: 根据mask将src中的int32_t类型数据转换为float类型，支持多种舍入模式，结果写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int322float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscInt322Float

根据mask将src中的每个int32_t类型数据转换成float类型，并支持多种舍入模式，结果写入dst。参考伪代码
关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 掩码寄存器，用于控制各元素是否参与计算。mask中与元素对应的比特位为1时，该元素参与计算；为0时，该元素不参与计算。

支持数据类型：float、int32_t。

约束：- src与dst的数据类型需要与函数原型匹配。
- 掩码位为0时，dst对应元素置0。
- 当int32_t的绝对值大于时，按函数后缀指定的舍入模式进行舍入。

仅 Ascend 950PR/Ascend 950DT 支持。
