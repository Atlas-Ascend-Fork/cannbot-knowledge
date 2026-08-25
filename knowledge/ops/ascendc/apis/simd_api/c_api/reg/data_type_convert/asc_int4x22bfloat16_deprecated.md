---
type: API
title: asc_int4x22bfloat16 (废弃)
description: 将int4x2_t类型转化为bfloat16_t类型，无舍入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int4x22bfloat16_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_int4x22bfloat16 (废弃)

将int4x2_t类型转化为bfloat16_t类型，无舍入模式。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、int4x2_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt42half](../../vector_compute/asc_int42half.md)（`related`）：asc_int4x22bfloat16 (废弃) 与《AscInt42half》的实质衔接是：该废弃 int4x2→bfloat16 接口没有等价现行候选；废弃接口清单说明迁移状态，AscInt4ToHalf 仅提供仍可用的 int4 输入转换方向而非等价替换。
- [asc_bfloat162e1m2x2 (废弃)](asc_bfloat162e1m2x2_deprecated.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《asc_int4x22bfloat16 (废弃)》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [废弃接口](../../deprecated_interface/deprecated_interface.md)（`related`）：asc_int4x22bfloat16 (废弃) 与《废弃接口》的实质衔接是：该废弃 int4x2→bfloat16 接口没有等价现行候选；废弃接口清单说明迁移状态，AscInt4ToHalf 仅提供仍可用的 int4 输入转换方向而非等价替换。
- [asc_int4x22half (废弃)](asc_int4x22half_deprecated.md)（`same_topic`）：asc_int4x22half (废弃) 与《asc_int4x22bfloat16 (废弃)》的实质衔接是：该废弃接口把 packed int4x2 转 half；同源 bfloat16/int16、逆向转换、废弃接口表及当前 AscInt4ToHalf 用于迁移并核对 packed lane。
<!-- cannbot:related:end -->
