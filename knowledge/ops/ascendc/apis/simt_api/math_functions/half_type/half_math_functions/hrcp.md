---
type: API
title: Half数学函数hrcp
description: 获取输入数据x的倒数。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hrcp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Half数学函数hrcp

功能：获取输入数据x的倒数。

函数原型：half hrcp(half x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据的倒数。本接口受全局饱和寄存器的影响，。特殊值：±0→ASCRT_MAX_NORMAL_FP16；nan→0；inf→0；-inf→-0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [BFloat16数学函数hrcp](../../bfloat16_type/bfloat16_math_functions/hrcp.md)（`related`）：half 与 bfloat16 的 hrcp 都计算倒数，可根据源类型精度和范围选择，不需先转 float。
- [Hrsqrt](hrsqrt.md)（`same_topic`）：Hrsqrt 与《Half数学函数hrcp》的实质衔接是：Hrsqrt 可由 Hsqrt 与 Hrcp 分解；精度故障卡给出该替换在实测误差超限时的可执行验证。
<!-- cannbot:related:end -->
