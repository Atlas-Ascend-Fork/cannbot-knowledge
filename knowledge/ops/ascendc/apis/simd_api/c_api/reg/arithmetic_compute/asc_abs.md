---
type: API
title: AscAbs
description: 按元素取绝对值，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_abs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscAbs

按元素取绝对值，i为元素索引。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half、int16_t、int32_t、int8_t。

约束：mask未筛选的元素在输出中置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Abs](../../../basic_api/memory_vector_compute/basic_arithmetic/abs.md)（`same_topic`）：Abs 与《AscAbs》的衔接是：这些卡分别给出 Abs 在 Reg、C Reg、C Vector 路径上的同一绝对值语义；原地覆盖时符号位丢失案例是该操作的直接别名风险。
- [Abs](../../../basic_api/reg_vector_compute/basic_arithmetic/abs.md)（`same_topic`）：AscAbs 是 C API 寄存器侧的同一绝对值操作，补充 C/C++ 接口映射和 mask 契约。
- [AscAbs](../../vector_compute/asc_abs.md)（`same_topic`）：AscAbs说明按元素取绝对值，将结果写入目的操作数dst。
- [AscAbsSync](../../deprecated_interface/asc_abs_sync_deprecated.md)（`same_topic`）：《AscAbsSync》处理“已废弃的按元素取绝对值同步计算接口，请改用asc_abs和asc_sync实现精细化调优。”。《AscAbs》提供“按元素取绝对值，将结果写入目的操作数dst。”，其具体合同或探针直接接入废弃 AscAbsSync 拆分为 AscAbs 与 asc_sync 的迁移合同。
<!-- cannbot:related:end -->
