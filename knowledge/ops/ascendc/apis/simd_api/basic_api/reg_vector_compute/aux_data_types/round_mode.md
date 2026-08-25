---
type: API
title: RoundMode
description: 枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/RoundMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# RoundMode

枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。

本接口属于 Reg 矢量计算辅助数据类型定义。

# RoundMode | 参数名 | 描述 | | :-- | :-- | | RoundMode | 用于设置控制舍入模式。 enum class RoundMode { CAST_NONE = 0, CAST_RINT, CAST_FLOOR, CAST_CEIL, CAST_ROUND, CAST_TRUNC, CAST_ODD, CAST_HYBRID }; • CAST_NONE：当转换过程存在精度损失时，按 CAST_RINT 模式处理；当不存在精度损失时，不进行舍入。 • CAST_RINT：向最近的偶数舍入。 - 若待舍入部分的首位为 0，则不进位。 - 若待舍入部分的首位为 1 且后续位不全为 0，则进位。 - 若待舍入部分的首位为 1 且后续位全为 0：当非舍入部分的末位为 0，则不进位。当非舍入部分的末位为 1，则进位。 • CAST_FLOOR：向负无穷大方向舍入。 - 若符号位（S）为 0（正数），不进位。 - 若符号位（S）为 1（负数）：当待舍入部分全为 0，则不进位。否则，进位。 • CAST_CEIL：向正无穷大方向舍入。 - 若符号位（S）为 1（

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
