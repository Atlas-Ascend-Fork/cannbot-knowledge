---
type: API
title: __bfloat162bfloat16_rd
description: 将bfloat16_t数据遵循CAST_FLOOR模式取整。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162bfloat16_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162bfloat16_rd

将bfloat16_t数据遵循CAST_FLOOR模式取整。
函数原型：bfloat16_t __bfloat162bfloat16_rd(const bfloat16_t x)
返回值：输入遵循CAST_FLOOR模式取整后的bfloat16_t类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__bfloat162half_rd](../../half_type/half_precision_conversion_functions/_bfloat162half_rd.md)（`related`）：__bfloat162half_rd 从同一 bfloat16 源按 CAST_FLOOR 转到 half，适合对照 focal 保持 bfloat16 与跨格式转换的特殊值处理。
- [__float2bfloat16_rd](_float2bfloat16_rd.md)（`related`）：__float2bfloat16_rd 与 focal 都采用 CAST_FLOOR 并受全局饱和模式影响，前者完成 float 降精度，后者在 bfloat16 域执行同模式取整。
- [__half2bfloat16_rd](_half2bfloat16_rd.md)（`related`）：__half2bfloat16_rd 把 half 按 CAST_FLOOR 转入 bfloat16，可与 focal 的 bfloat16 域取整组成混合低精度路径。
- [__bfloat162bfloat16_rn](_bfloat162bfloat16_rn.md)（`same_topic`）：焦点处理bfloat16 自身取整的舍入模式族；__bfloat162bfloat16_rd正文界定“将bfloat16_t数据遵循CAST_FLOOR模式取整”。候选保持 bfloat16 输入输出，仅改变 FLOOR/RINT/ROUND/CEIL/TRUNC 舍入方向。
- [__bfloat162bfloat16_rna](_bfloat162bfloat16_rna.md)（`same_topic`）：__bfloat162bfloat16_rna 与 focal 使用同一 bfloat16 输入输出和饱和规则，但采用 CAST_ROUND，可用于需要 ties-away 类语义而非 floor 的取整路径。
- [__bfloat162bfloat16_ru](_bfloat162bfloat16_ru.md)（`same_topic`）：__bfloat162bfloat16_rd说明将bfloat16_t数据遵循CAST_FLOOR模式取整；对__bfloat162bfloat16_ru而言，四个同源同目的转换只改变 floor、nearest、nearest-away 与 trunc 舍入决策，需并列选择而不能默认等价。
- [__bfloat162bfloat16_rz](_bfloat162bfloat16_rz.md)（`same_topic`）：焦点处理bfloat16 自身 CAST_TRUNC 取整与其他舍入模式；__bfloat162bfloat16_rd正文说明“将bfloat16_t数据遵循CAST_FLOOR模式取整”。候选保持相同 bfloat16 输入输出，仅改变舍入方向，可直接对照边界行为。
<!-- cannbot:related:end -->
