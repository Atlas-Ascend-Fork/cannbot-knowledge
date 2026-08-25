---
type: API
title: __float22half2_rd
description: 将float2类型数据的两个分量遵循CAST_FLOOR模式转换为半精度浮点数，返回转换后的half2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float22half2_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22half2_rd

功能：将float2类型数据的两个分量遵循CAST_FLOOR模式转换为半精度浮点数，返回转换后的half2类型数据。

函数原型：half2 __float22half2_rd(const float2 x)

参数：x（输入）源操作数。

返回值：将输入的两个分量遵循CAST_FLOOR模式转换成的half2类型数据。本接口受全局饱和寄存器的影响，。特殊值：±0→±0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float22half2_ro_sat](_float22half2_ro_sat.md)（`related`）：《__float22half2_ro_sat》说明饱和模式下，将float2类型数据的两个分量遵循CAST_ODD模式转换为半精度浮点数，返回转换后的half2类型数据。；《__float22half2_rd》说明将float2类型数据的两个分量遵循CAST_FLOOR模式转换为半精度浮点数，返回转换后的half2类型数据。。二者在float2到half2的CAST_ODD饱和转换必须与同舍入非饱和版以及其他舍入模式的饱和/非饱和变体按CTRL与特殊值选择上存在可执行的直接衔接。
- [__float22half2_ru](_float22half2_ru.md)（`related`）：RD 向下舍入，与 RU 的方向相反，可按误差单调性要求选型。
- [__floats2half2_rn](_floats2half2_rn.md)（`related`）：__float22half2_rd 与《__floats2half2_rn》的实质衔接是：float2→half2 RD 与饱和、其他舍入、反向 half2→float2 和双 float 拼装入口共享双 lane 窄化契约。
- [__half22float2](_half22float2.md)（`related`）：__float22half2_rd 与《__half22float2》的实质衔接是：float2→half2 RD 与饱和、其他舍入、反向 half2→float2 和双 float 拼装入口共享双 lane 窄化契约。
- [__float22half2_rd_sat](_float22half2_rd_sat.md)（`same_topic`）：《__float22half2_rd_sat》说明将float2类型数据的两个分量遵循CAST_FLOOR模式转换为半精度浮点数，返回转换后的half2类型数据。；《__float22half2_rd》说明将float2类型数据的两个分量遵循CAST_FLOOR模式转换为半精度浮点数，返回转换后的half2类型数据。。二者在float2到half2的向下舍入与饱和是两个独立维度，同输入输出的非饱和版和其他舍入版可直接对照上存在可执行的直接衔接。
- [__float22half2_rn](_float22half2_rn.md)（`same_topic`）：__float22half2_rd 与《__float22half2_rn》的实质衔接是：float2→half2 RD 与饱和、其他舍入、反向 half2→float2 和双 float 拼装入口共享双 lane 窄化契约。
- [__float22half2_rna](_float22half2_rna.md)（`same_topic`）：《__float22half2_rna》说明将float2类型数据的两个分量遵循CAST_ROUND模式转换为半精度浮点数，返回转换后的half2类型数据。；《__float22half2_rd》说明将float2类型数据的两个分量遵循CAST_FLOOR模式转换为半精度浮点数，返回转换后的half2类型数据。。二者在float2到half2的rna与饱和开关、rn/rd/ro/ru/rz舍入变体共享同一输入输出合同上存在可执行的直接衔接。
- [__float22half2_ro](_float22half2_ro.md)（`same_topic`）：__float22half2_ro 与《__float22half2_rd》的实质衔接是：__float22half2_ro 与 RO-sat、RD/RN/RNA/RU/RZ 变体共享 float2→half2 双 lane 窄化，只改变舍入或饱和；scalar RO 和反向 half2→float2 明确向量封装及转换方向。
- [__float22half2_rz](_float22half2_rz.md)（`same_topic`）：__float22half2_rd 与本接口源/目标类型一致，把舍入从截断改为向下取整。
<!-- cannbot:related:end -->
