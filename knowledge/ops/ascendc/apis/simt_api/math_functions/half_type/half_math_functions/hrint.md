---
type: API
title: Hrint
description: 获取与输入half数据最接近的整数，若存在两个同样接近的整数则取偶数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hrint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hrint

功能：获取与输入数据最接近的整数，若存在两个同样接近的整数，则获取其中的偶数。

函数原型：half hrint(half x)

参数：x（输入）源操作数。

返回值：与输入浮点数最接近的整数值。本接口受全局饱和寄存器的影响，。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Hceil](hceil.md)（`related`）：Hceil 向正无穷取整，Hrint nearest-even；正负小数边界需按目标舍入选择。
- [Hfloor](hfloor.md)（`related`）：Hfloor 向负无穷取整，与 Hrint 在非整数及负数上不同。
- [Hrint](../../bfloat16_type/bfloat16_math_functions/hrint.md)（`related`）：Hrint 与《Hrint》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Htrunc](htrunc.md)（`related`）：Htrunc 向零截断，和 Hrint 的 ties-to-even 契约不同。
<!-- cannbot:related:end -->
