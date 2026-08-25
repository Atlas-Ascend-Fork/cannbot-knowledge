---
type: API
title: AscRound
description: 将浮点数按ROUND（四舍五入）舍入为整数值，结果保持原浮点类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_round.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscRound

将src中的浮点数元素按照ROUND（四舍五入）舍入模式舍入到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。

关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half。

约束：float类型只支持不饱和模式。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int16](asc_float2int16.md)（`related`）：《AscFloat2Int16》处理“将float类型数据转化为int16_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。”。《AscRound》明确提供“将浮点数按ROUND（四舍五入）舍入为整数值，结果保持原浮点类型。”，其参数、调用或验证步骤直接接入float 到 int16 的同源同目标转换及 rounding/saturation 选择。
- [AscRint](asc_rint.md)（`related`）：AscRound 与 AscRint 的核心差别是舍入规则，半整数输入时需根据 ties-to-even 或普通 round 语义选择。
- [Lroundf](../../../../simt_api/math_functions/float_math_functions/lroundf.md)（`related`）：Lroundf 与《AscRound》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [舍入模式与饱和模式](rounding_mode.md)（`related`）：AscRound说明将浮点数按ROUND（四舍五入）舍入为整数值，结果保持原浮点类型。
- [Round](../../../adv_api/math_compute/round_interface/round.md)（`same_topic`）：AscRound 与《Round》的实质衔接是：AscRound 采用 ties-away 的 ROUND 语义，舍入模式页与 AscRint 的 ties-to-even 形成直接对照；高阶 Round 和 SIMT roundf 是同一取整任务在 Tensor 与线程标量层的入口。
- [Roundf](../../../../simt_api/math_functions/float_math_functions/roundf.md)（`same_topic`）：Roundf：Roundf、Lroundf/Llroundf共享 ties-to-even 取整语义但返回类型不同；高级 Round和AscRound提供向量实现时的同语义契约。 目标卡《AscRound》补充：将浮点数按ROUND（四舍五入）舍入为整数值，结果保持原浮点类型。
<!-- cannbot:related:end -->
