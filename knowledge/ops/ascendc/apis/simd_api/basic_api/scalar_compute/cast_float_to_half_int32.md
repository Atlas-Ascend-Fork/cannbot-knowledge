---
type: API
title: CastFloatToHalfInt32
description: 将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/Cast_float_to_half_int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# CastFloatToHalfInt32

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

对标量的数据类型进行转换。

在使用该接口之前，用户需要先了解内置数据类型和精度转换。

参数：T: valueIn的数据类型。；U: 转换后的数据类型。；roundMode: 精度转换处理模式，类型是RoundMode。 RoundMode为枚举类型，用以控制精度转换处理模式，参考精度舍入模式，可取值为: • CAST_NONE：当转换过程存在精度损失时，按CAST_RINT模式处理；当不存在精度损失时，不进行舍入； • CAST_RINT：向最近的偶数舍入； • CAST_FLOOR：向负无穷大方向舍入； • CAST_CEIL：向正无穷大方向舍入； • CAST_ROUND：四舍五入； • CAST_TRUNC：截断模式； • CAST_ODD：向最近的奇数舍入。；valueIn(输入): 被转换数据类型的标量。

支持数据类型：支持的数据类型
- valueIn支持float。
- 返回值支持half、int32_t。

约束：支持的数据类型组合及对应支持的RoundMode

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030 支持。
