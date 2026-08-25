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
