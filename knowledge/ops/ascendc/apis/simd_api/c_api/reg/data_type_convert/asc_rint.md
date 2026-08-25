---
type: API
title: AscRint
description: 将浮点数按RINT（四舍六入五成双）舍入为整数值，结果保持原浮点类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_rint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscRint

将src中的浮点数元素按照RINT（四舍六入五成双）舍入模式舍入到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。

关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half。

约束：float类型只支持不饱和模式。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int16](asc_float2int16.md)（`related`）：《AscFloat2Int16》处理“将float类型数据转化为int16_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。”。《AscRint》明确提供“将浮点数按RINT（四舍六入五成双）舍入为整数值，结果保持原浮点类型。”，其参数、调用或验证步骤直接接入float 到 int16 的同源同目标转换及 rounding/saturation 选择。
- [AscRound](asc_round.md)（`related`）：AscRound 与 AscRint 的核心差别是舍入规则，半整数输入时需根据 ties-to-even 或普通 round 语义选择。
- [Rint](../../../adv_api/math_compute/rint_interface/rint.md)（`related`）：Advanced Rint 与 AscRint 都执行 ties-to-even 且保持浮点结果，前者面向 LocalTensor，后者面向寄存器。
- [Rintf](../../../../simt_api/math_functions/float_math_functions/rintf.md)（`related`）：SIMT rintf 为单线程 float 提供相同 ties-to-even 舍入，可按 SIMD Reg 与 SIMT 标量执行模型选型。
- [Rint接口](../../../adv_api/math_compute/rint_interface/rint_interface.md)（`related`）：“Rint接口”定义：按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。；“AscRint”定义：将浮点数按RINT（四舍六入五成双）舍入为整数值，结果保持原浮点类型。。实质衔接：Rint 接口页汇总 kernel 操作与两种临时空间估算；AscRint 提供寄存器 C API 的同一 ties-to-even 数值语义用于实现路径对照。
- [Llrintf](../../../../simt_api/math_functions/float_math_functions/llrintf.md)（`same_topic`）：Llrintf 与《AscRint》的实质衔接是：Llrintf 按当前 rounding mode 返回 long long；Lrintf、Rintf/Nearbyintf 和 AscRint分别对照返回宽度、异常行为和 Tensor 入口。
<!-- cannbot:related:end -->
