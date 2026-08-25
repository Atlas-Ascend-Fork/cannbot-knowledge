---
type: API
title: CastMultiTypeToFloat
description: 将bfloat16_t、fp8、fp4等多种类型标量数据转换为float类型。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/Cast_multi_type_to_float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# CastMultiTypeToFloat

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

该接口将输入数据转换为float类型。

在使用该接口之前，用户需要先了解内置数据类型和精度转换。

参数：T: 操作数数据类型。；U: 返回值数据类型。；bVal(输入): 待转换的标量数据。

约束：输入参数为立即数时，需要使用显式类型转换，例如

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [Uint32ToFloat 须用 IEEE754 位操作而非位移乘法](../../../../runbooks/precision/uint32tofloat_ieee754.md)（`exemplifies`）：Uint32ToFloat 须用 IEEE754 位操作而非位移乘法 与《CastMultiTypeToFloat》的实质衔接是：bit-exact 随机链必须与 Philox 原生实现一致：counter/round/offset 先生成 uint32，再按 IEEE754 尾数位重解释；通用 Cast 不能替代该位级契约。
- [CastFloatToHalfInt32](cast_float_to_half_int32.md)（`related`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《CastMultiTypeToFloat》说明将bfloat16_t、fp8、fp4等多种类型标量数据转换为float类型。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
