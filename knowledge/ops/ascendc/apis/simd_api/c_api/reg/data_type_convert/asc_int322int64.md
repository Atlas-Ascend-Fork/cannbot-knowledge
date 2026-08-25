---
type: API
title: AscInt322Int64
description: 根据mask将src中的int32_t类型元素转换为int64_t类型，结果写入dst，位宽比为1:2。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int322int64.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscInt322Int64

根据mask将src中的每个int32_t类型元素转换为int64_t类型，结果写入dst。由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。伪代码

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 掩码寄存器，用于控制各元素是否参与计算。mask中与元素对应的比特位为1时，该元素参与计算；为0时，该元素不参与计算。

支持数据类型：int32_t、int64_t。

约束：- src与dst的数据类型需要与函数原型匹配。
- mask掩码位为0时，dst对应元素置0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt322int64](../../vector_compute/asc_int322int64.md)（`related`）：AscInt322Int64 与《AscInt322int64》的实质衔接是：AscInt32ToInt64 的 Reg 与 C 向量入口执行同一有符号扩宽，反向 Int64ToInt32 明确窄化时的溢出边界。
- [AscInt642int32](asc_int642int32.md)（`related`）：《AscInt642int32》说明将int64_t类型源操作数转换为int32_t类型，支持饱和与非饱和模式。；《AscInt322Int64》说明根据mask将src中的int32_t类型元素转换为int64_t类型，结果写入dst，位宽比为1:2。。二者在int64到int32窄化的饱和/非饱和语义需与反向扩宽及同源转换对照验证上存在可执行的直接衔接。
<!-- cannbot:related:end -->
