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

<!-- cannbot:related:start -->
## 相关

- [Reg CastTrait RoundMode 命名空间编译失败](../../../../runbooks/compilation/casttrait_roundmode_is_in_ascendc.md)（`exemplifies`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《Reg CastTrait RoundMode 命名空间编译失败》说明dav-3510 Reg CastTrait 的 RoundMode 枚举不在 Reg 子命名空间；按编译器声明位置改用 AscendC::RoundMode 后恢复构建。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
- [CastFloatToBfloat16](cast_float_to_bfloat16.md)（`related`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《CastFloatToBfloat16》说明将float类型标量数据转换为bfloat16_t类型标量数据。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
- [CastMultiTypeToFloat](cast_multi_type_to_float.md)（`related`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《CastMultiTypeToFloat》说明将bfloat16_t、fp8、fp4等多种类型标量数据转换为float类型。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
- [RoundMode](../reg_vector_compute/aux_data_types/round_mode.md)（`related`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《RoundMode》说明枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
- [标量计算](scalar_compute.md)（`related`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《标量计算》说明标量计算接口索引页，汇总GetBitCount、CountLeadingZero、Cast类型转换及Gm旁路DCache读写(ISASI)等。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
- [AscFloat2Int32](../../c_api/scalar_compute/asc_float2int32.md)（`same_topic`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《AscFloat2Int32》说明将float类型转换为int32_t类型，支持RINT、ROUND、FLOOR、CEIL四种舍入模式。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
