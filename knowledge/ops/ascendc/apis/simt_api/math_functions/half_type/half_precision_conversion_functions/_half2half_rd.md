---
type: API
title: __half2half_rd
description: 将half类型数据遵循CAST_FLOOR模式取整。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2half_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2half_rd

功能：将half类型数据遵循CAST_FLOOR模式取整。

函数原型：half __half2half_rd(const half x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式取整后的half类型数据。本接口受全局饱和寄存器的影响，。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__half2half_rn](_half2half_rn.md)（`same_topic`）：两卡都保持 half 类型并取整，分别使用 floor 与 nearest-even，源/目标和饱和行为相同。
- [__half2half_rna](_half2half_rna.md)（`same_topic`）：__half2half_rna 与《__half2half_rd》的实质衔接是：同类型 rd/rn/ru/rz 与 bfloat16/float 输入的 rna/sat 变体共同界定 CAST_ROUND 的 tie-away 和饱和特殊值行为。
- [__half2half_ru](_half2half_ru.md)（`same_topic`）：两卡都保持 half 类型并取整，分别向负无穷和正无穷，是上下界舍入的成对接口。
- [__half2half_rz](_half2half_rz.md)（`same_topic`）：两卡都保持 half 类型并取整，分别为 floor 与 toward-zero；负分数输入会产生关键差异。
<!-- cannbot:related:end -->
