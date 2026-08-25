---
type: API
title: __half2uint_rd
description: 遵循CAST_FLOOR模式，将half类型数据转换为unsigned int类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2uint_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2uint_rd

功能：遵循CAST_FLOOR模式，将half类型数据转换为unsigned int类型数据，返回转换后的值。

函数原型：unsigned int __half2uint_rd(const half x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的无符号整数。特殊值：±0→0；nan→0；inf→4294967295（uint32_t最大值）；-inf→0；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→0；ASCRT_MIN_DENORM_FP16→0；0.5→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2uint_rd](../../data_type_conversion/type_conversion_functions/_float2uint_rd.md)（`related`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《__half2uint_rd》说明遵循CAST_FLOOR模式，将half类型数据转换为unsigned int类型数据，返回转换后的值。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [__half2ull_rd](_half2ull_rd.md)（`related`）：__half2ull_rd 与《__half2uint_rd》的实质衔接是：half→unsigned long long 的 floor 模式与同目标的 RN/RNA/RU/RZ 及同 floor 的有符号/其他源类型形成可执行舍入选择矩阵。
- [__bfloat162uint_rd](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162uint_rd.md)（`same_topic`）：__bfloat162uint_rd 与《__half2uint_rd》的衔接是：这些接口都把浮点半精度值转为无符号整数，候选分别对比源类型及 rn/rd/ru/rz 舍入方向，可直接核对边界输入的转换结果。
- [__half2int_rd](_half2int_rd.md)（`same_topic`）：__half2int_rd 与《__half2uint_rd》的实质衔接是：这些卡保持 half 到整数转换并切换 rd/rn/rna/ru/rz 或目标有无符号；C 的 half2int16/32 入口说明向量执行层的目标位宽选择。
- [__half2uint_rn](_half2uint_rn.md)（`same_topic`）：rn nearest-even 与 focal rd floor 处理相同 half→uint32，非整数尤其负值附近会产生不同结果。
- [__half2uint_ru](_half2uint_ru.md)（`same_topic`）：ru ceil 与 rd floor 给出同一 half→uint32 的上下界舍入，正非整数输入差一单位。
- [__half2uint_rz](_half2uint_rz.md)（`same_topic`）：__half2uint_rz 的核心契约是“遵循CAST_TRUNC模式，将half类型数据转换为无符号整数，返回转换后的值”；__half2uint_rd 补充“遵循CAST_FLOOR模式，将half类型数据转换为unsigned int类型数据，返回转换后的值”。
<!-- cannbot:related:end -->
