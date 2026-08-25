---
type: API
title: Roundf
description: 获取对输入数据四舍五入后的整数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/roundf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Roundf

功能：获取对输入数据四舍五入后的整数。

函数原型：float roundf(float x)

参数：x（输入）源操作数。

返回值：对输入四舍五入后的整数。特殊值：nan→nan；inf→inf；-inf→-inf。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Llroundf](llroundf.md)（`related`）：Roundf 保持浮点返回值而 Llroundf 直接产生 long long，二者适合后续仍需浮点或需要整数索引的不同链路。
- [Round](../../../simd_api/adv_api/math_compute/round_interface/round.md)（`related`）：Round：Round 的 kernel 调用直接依赖同名临时空间接口；AscRound/Roundf提供不同编程模型下相同 ties-to-even 语义的对照。 目标卡《Roundf》补充：获取对输入数据四舍五入后的整数。
- [AscRound](../../../simd_api/c_api/reg/data_type_convert/asc_round.md)（`same_topic`）：Roundf：Roundf、Lroundf/Llroundf共享 ties-to-even 取整语义但返回类型不同；高级 Round和AscRound提供向量实现时的同语义契约。 目标卡《AscRound》补充：将浮点数按ROUND（四舍五入）舍入为整数值，结果保持原浮点类型。
- [Lroundf](lroundf.md)（`same_topic`）：Roundf：Roundf、Lroundf/Llroundf共享 ties-to-even 取整语义但返回类型不同；高级 Round和AscRound提供向量实现时的同语义契约。 目标卡《Lroundf》补充：获取对输入数据四舍五入后的整数。
<!-- cannbot:related:end -->
