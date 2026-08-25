---
type: API
title: AscInt42half
description: 将int4_t类型数据转换为half类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_int42half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscInt42half

将int4_t类型数据转换为half类型。
函数原型：void asc_int42half(__ubuf__ half* dst, __ubuf__ int4b_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。；当src为int4b_t时，前n个数据计算接口与同步计算接口的count必须为偶数。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscHalf2int4](asc_half2int4.md)（`related`）：两接口提供 int4↔half 的相反方向转换，可用于构建量化输入解包与输出重新量化链。
- [asc_int4x22bfloat16 (废弃)](../reg/data_type_convert/asc_int4x22bfloat16_deprecated.md)（`related`）：asc_int4x22bfloat16 (废弃) 与《AscInt42half》的实质衔接是：该废弃 int4x2→bfloat16 接口没有等价现行候选；废弃接口清单说明迁移状态，AscInt4ToHalf 仅提供仍可用的 int4 输入转换方向而非等价替换。
- [asc_int4x22half (废弃)](../reg/data_type_convert/asc_int4x22half_deprecated.md)（`same_topic`）：asc_int4x22half (废弃) 与《AscInt42half》的实质衔接是：该废弃接口把 packed int4x2 转 half；同源 bfloat16/int16、逆向转换、废弃接口表及当前 AscInt4ToHalf 用于迁移并核对 packed lane。
<!-- cannbot:related:end -->
