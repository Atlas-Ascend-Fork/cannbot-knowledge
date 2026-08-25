---
type: API
title: Lroundf
description: 获取对输入数据四舍五入后的整数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/lroundf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Lroundf

功能：获取对输入数据四舍五入后的整数。

函数原型：long int lroundf(float x)

参数：x（输入）源操作数。

返回值：对输入四舍五入后的整数。特殊值：nan→0。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscRound](../../../simd_api/c_api/reg/data_type_convert/asc_round.md)（`related`）：Lroundf 与《AscRound》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [GetRoundMaxMinTmpSize](../../../simd_api/adv_api/math_compute/round_interface/get_round_max_min_tmp_size.md)（`related`）：Lroundf 与《GetRoundMaxMinTmpSize》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [GetRoundTmpBufferFactorSize](../../../simd_api/adv_api/math_compute/round_interface/get_round_tmp_buffer_factor_size.md)（`related`）：Lroundf 与《GetRoundTmpBufferFactorSize》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [Round](../../../simd_api/adv_api/math_compute/round_interface/round.md)（`related`）：Lroundf 与《Round》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [RoundMode](../../../simd_api/basic_api/reg_vector_compute/aux_data_types/round_mode.md)（`related`）：Lroundf 与《RoundMode》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [Round接口](../../../simd_api/adv_api/math_compute/round_interface/round_interface.md)（`related`）：Lroundf 与《Round接口》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [Llroundf](llroundf.md)（`same_topic`）：Lroundf 与《Llroundf》的实质衔接是：Lroundf 与 llroundf/roundf 及高阶/C API Round 共享舍入任务，RoundMode 解释 ties 与返回整数宽度的选择。
- [Roundf](roundf.md)（`same_topic`）：Roundf：Roundf、Lroundf/Llroundf共享 ties-to-even 取整语义但返回类型不同；高级 Round和AscRound提供向量实现时的同语义契约。 目标卡《Lroundf》补充：获取对输入数据四舍五入后的整数。
<!-- cannbot:related:end -->
