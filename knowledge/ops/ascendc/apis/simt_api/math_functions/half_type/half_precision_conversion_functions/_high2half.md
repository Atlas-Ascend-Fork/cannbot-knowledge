---
type: API
title: __high2half
description: 提取输入half2的高16位，并返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__high2half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __high2half

功能：提取输入half2的高16位，并返回。

函数原型：half __high2half(const half2 x)

参数：x（输入）源操作数。

返回值：返回输入half2的高16位。特殊值：±0→±0；nan→nan；±inf→±inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__high2half2](_high2half2.md)（`related`）：__high2half2 duplicates the high lane into a half2, while __high2half extracts that lane as a scalar half.
- [__low2half](_low2half.md)（`related`）：__high2half 提取同一 half2 的高 16 位，与 low 接口成对用于拆解两个分量。
- [__high2bfloat16](../../bfloat16_type/bfloat16_precision_conversion_functions/_high2bfloat16.md)（`same_topic`）：《__high2bfloat16》处理“从bfloat16x2_t类型输入数据中提取高16位，作为bfloat16_t类型返回。”。《__high2half》提供“提取输入half2的高16位，并返回。”，其具体合同或探针直接接入packed bfloat16 高 lane 提取、复制、交换和 half2 对应实现。
<!-- cannbot:related:end -->
