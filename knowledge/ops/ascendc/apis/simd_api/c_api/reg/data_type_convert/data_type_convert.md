---
type: API
title: 类型转换
description: 寄存器侧类型转换类接口汇总，覆盖bfloat16、half、float、int等数据类型间的相互转换及取整操作。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/data_type_convert.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 类型转换

寄存器侧类型转换接口覆盖bfloat16/half/float/int8/int16/int32/int64/uint8/uint16/uint32等数据类型间的相互转换，命名遵循asc_<src>2<dst>规范。
舍入接口含asc_ceil/floor/round/trunc/rint，提供不同的取整模式，舍入模式与饱和模式的配置说明见专文档。
多个e1m2/e2m1/e4m3/e5m2/hif8/int4x2相关转换接口已废弃，建议使用asc_half2hif8/hif82half等替代接口。
