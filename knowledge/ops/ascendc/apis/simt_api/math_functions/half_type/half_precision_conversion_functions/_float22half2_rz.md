---
type: API
title: __float22half2_rz
description: 将float2类型数据的两个分量遵循CAST_TRUNC模式转换为半精度浮点数，返回转换后的half2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float22half2_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22half2_rz

功能：将float2类型数据的两个分量遵循CAST_TRUNC模式转换为半精度浮点数，返回转换后的half2类型数据。

函数原型：half2 __float22half2_rz(const float2 x)

参数：x（输入）源操作数。

返回值：将输入的两个分量遵循CAST_TRUNC模式转换成的half2类型数据。本接口受全局饱和寄存器的影响，。特殊值：±0→±0；nan→±0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float22bfloat162_rz](../../bfloat16_type/bfloat16_precision_conversion_functions/_float22bfloat162_rz.md)（`related`）：两接口都对 float2 两分量采用 CAST_TRUNC，目标分别为 half2 与 bfloat16x2，可按目标精度格式选用。
- [__float22half2_ro_sat](_float22half2_ro_sat.md)（`related`）：《__float22half2_ro_sat》说明饱和模式下，将float2类型数据的两个分量遵循CAST_ODD模式转换为半精度浮点数，返回转换后的half2类型数据。；《__float22half2_rz》说明将float2类型数据的两个分量遵循CAST_TRUNC模式转换为半精度浮点数，返回转换后的half2类型数据。。二者在float2到half2的CAST_ODD饱和转换必须与同舍入非饱和版以及其他舍入模式的饱和/非饱和变体按CTRL与特殊值选择上存在可执行的直接衔接。
- [__half22float2](_half22float2.md)（`related`）：__half22float2 将 half2 两 lane 宽化回 float2，是本 float2→half2 窄化结果的直接逆向消费路径。
- [__float22half2_rd](_float22half2_rd.md)（`same_topic`）：__float22half2_rd 与本接口源/目标类型一致，把舍入从截断改为向下取整。
- [__float22half2_rn](_float22half2_rn.md)（`same_topic`）：RZ 对同一 float2→half2 双分量转换朝零截断，与 RN 的最近偶数行为直接对照。
- [__float22half2_rna](_float22half2_rna.md)（`same_topic`）：《__float22half2_rna》说明将float2类型数据的两个分量遵循CAST_ROUND模式转换为半精度浮点数，返回转换后的half2类型数据。；《__float22half2_rz》说明将float2类型数据的两个分量遵循CAST_TRUNC模式转换为半精度浮点数，返回转换后的half2类型数据。。二者在float2到half2的rna与饱和开关、rn/rd/ro/ru/rz舍入变体共享同一输入输出合同上存在可执行的直接衔接。
- [__float22half2_ro](_float22half2_ro.md)（`same_topic`）：__float22half2_ro 与本接口源/目标类型一致，把舍入从截断改为 ODD。
- [__float22half2_ru](_float22half2_ru.md)（`same_topic`）：__float22half2_ru 与本接口源/目标类型一致，把舍入从截断改为向上取整。
- [__float22half2_rz_sat](_float22half2_rz_sat.md)（`same_topic`）：__float22half2_rz_sat 保持 float2→half2 与 CAST_TRUNC 不变，只增加受 CTRL[60] 控制的饱和模式。
<!-- cannbot:related:end -->
