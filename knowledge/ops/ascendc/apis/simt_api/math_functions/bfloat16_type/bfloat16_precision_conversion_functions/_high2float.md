---
type: API
title: __high2float
description: 将bfloat16x2_t输入数据的高16位转换为float类型并返回结果。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__high2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __high2float

功能：将输入数据的高16位转换为float类型并返回结果。

函数原型：float __high2float(const bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据的高16位转换为float类型的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_BF16→3.38953e+38；-ASCRT_MAX_NORMAL_BF16→-3.38953e+38。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__high2float](../../half_type/half_precision_conversion_functions/_high2float.md)（`related`）：该接口执行相同的高 16 位→float 操作，但输入为 half2；用于在 bfloat16x2 与 half2 两种 packed 类型间迁移实现。
- [__high2bfloat16](_high2bfloat16.md)（`same_topic`）：《__high2bfloat16》处理“从bfloat16x2_t类型输入数据中提取高16位，作为bfloat16_t类型返回。”。《__high2float》提供“将bfloat16x2_t输入数据的高16位转换为float类型并返回结果。”，其具体合同或探针直接接入packed bfloat16 高 lane 提取、复制、交换和 half2 对应实现。
- [__low2float](_low2float.md)（`same_topic`）：__low2float 与《__high2float》的实质衔接是：__low2float 从 bfloat16x2 的低 lane 解包并转 float；high lane、整包 float2、标量 bfloat16→float 和 lane 交换接口共同确定 packed lane 的提取与顺序。
<!-- cannbot:related:end -->
