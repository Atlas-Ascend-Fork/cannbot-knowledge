---
type: API
title: 数据类型转换概述
description: 类型转换包括隐式转换和显式转换。隐式转换在类型不匹配时由系统自动执行。显式转换则通过调用类型转换API来主动完成，API会将输入数据从源类型转换为目标类型，并返回转换结果。整个转换过程遵循规定的处理规则。类型转换的结果受舍入模式和饱和模式的影响。关于浮点数的表示方式和舍入规则，请参见类型转换的相关说明。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据类型转换概述

功能：类型转换包括隐式转换和显式转换。隐式转换在类型不匹配时由系统自动执行。显式转换则通过调用类型转换API来主动完成，API会将输入数据从源类型转换为目标类型，并返回转换结果。整个转换过程遵循规定的处理规则。类型转换的结果受舍入模式和饱和模式的影响。关于浮点数的表示方式和舍入规则，请参见类型转换的相关说明。CAST_RINT：四舍六入五成双取整：srctype2dsttype_rn；CAST_FLOOR：向下取整：srctype2dsttype_rd；CAST_CEIL：向上取整：srctype2dsttype_ru；CAST_ROUND：四舍五入取整：srctype2dsttype_rna；CAST_TRUNC：向零取整：srctype2dsttype_rz。
