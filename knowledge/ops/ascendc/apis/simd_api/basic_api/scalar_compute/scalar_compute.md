---
type: API
title: 标量计算
description: 标量计算接口索引页，汇总GetBitCount、CountLeadingZero、Cast类型转换及Gm旁路DCache读写(ISASI)等。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/scalar_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 标量计算

标量计算接口提供位计数与前导零查询（GetBitCount、CountLeadingZero、CountBitsCntSameAsSignBit）、GetSFFValue和CeilDivision等数学辅助计算，以及Cast系列标量类型转换（float转half/int32_t/bfloat16_t及多类型转float）。
另含Nop空操作及WriteGmByPassDCache/ReadGmByPassDCache(ISASI)旁路DCache的GM读写接口，适用于特定性能优化场景。

<!-- cannbot:related:start -->
## 相关

- [CastFloatToHalfInt32](cast_float_to_half_int32.md)（`related`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《标量计算》说明标量计算接口索引页，汇总GetBitCount、CountLeadingZero、Cast类型转换及Gm旁路DCache读写(ISASI)等。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
- [WriteGmByPassDCache](write_gm_by_pass_d_cache_isasi.md)（`related`）：标量计算总览收录 bypass DCache 的 GM 读写，并将其与转换、位操作等 Scalar 能力区分。
- [CeilDivision](ceil_division.md)（`same_topic`）：CeilDivision 与《标量计算》的实质衔接是：CeilDivision 与 CeilDiv 执行整数向上整除，快速除法与 SIMT divide 接口提供实现和舍入边界，标量计算页说明 device 使用域。
<!-- cannbot:related:end -->
