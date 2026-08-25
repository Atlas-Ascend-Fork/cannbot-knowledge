---
type: API
title: __float22bfloat162_rd_sat
description: 饱和模式下，将float2类型数据的两个分量遵循CAST_FLOOR模式转换为bfloat16精度，返回转换后的bfloat16x2_t类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float22bfloat162_rd_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22bfloat162_rd_sat

饱和模式下，将float2类型数据的两个分量遵循CAST_FLOOR模式转换为bfloat16精度，返回转换后的bfloat16x2_t类型数据。
函数原型：bfloat16x2_t __float22bfloat162_rd_sat(const float2 x)
返回值：饱和模式下将输入的两个分量遵循CAST_FLOOR模式转换成的bfloat16x2_t类型数据。特殊值如下：
约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。；SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__float22bfloat162_rz_sat](_float22bfloat162_rz_sat.md)（`related`）：rd_sat 保持相同 float2→bfloat16x2 饱和路径但改为 CAST_FLOOR，可用于需要向下舍入而非截断的选择。
- [__float22half2_rd_sat](../../half_type/half_precision_conversion_functions/_float22half2_rd_sat.md)（`related`）：half2 目标位宽相同但格式/范围不同，不能复用 bfloat16 饱和边界。
- [__float22bfloat162_rd](_float22bfloat162_rd.md)（`same_topic`）：两卡同为 float2→bfloat16x2 且采用 floor，sat 版本增加显式饱和路径并要求 CTRL[60]=0；SIMT 无法设置 CTRL 时该饱和不生效。
- [__float22bfloat162_rn](_float22bfloat162_rn.md)（`same_topic`）：__float22bfloat162_rn 与《__float22bfloat162_rd_sat》的实质衔接是：这些入口保持 float2→bfloat16x2，切换舍入/饱和或打包来源；逆转换用于对拍两 lane 结果，避免混用 scalar 与 packed 形式。
- [__float22bfloat162_rn_sat](_float22bfloat162_rn_sat.md)（`same_topic`）：rd_sat 与 rn_sat 只改变为 floor 舍入，保留相同 CTRL[60] 和 SIMT 饱和边界，适合按误差方向选择。
- [__float22bfloat162_rna_sat](_float22bfloat162_rna_sat.md)（`same_topic`）：__float22bfloat162_rna_sat 与《__float22bfloat162_rd_sat》的实质衔接是：该接口保持 float2→bfloat16x2 并同时启用 rna 与饱和；无饱和、其他舍入及逆转换卡用于逐项核对舍入和特殊值裁剪。
- [__float22bfloat162_ru_sat](_float22bfloat162_ru_sat.md)（`same_topic`）：ru_sat 提供向上舍入，与 rd_sat 构成上下界。
- [__float2bfloat16_rd_sat](_float2bfloat16_rd_sat.md)（`same_topic`）：《__float22bfloat162_rd_sat》明确“饱和模式下，将float2类型数据的两个分量遵循CAST_FLOOR模式转换为bfloat16精度，返回转换后的bfloat16x2_t类型数据。”；它与《__float2bfloat16_rd_sat》的“饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_FLOOR模式，返回转换后的值。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
