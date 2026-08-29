---
type: API
title: __hbneux2
description: 比较两个bfloat16x2_t类型数据的两个分量是否不相等，当两个分量均不相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hbneux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbneux2

功能：比较两个bfloat16x2_t类型数据的两个分量是否不相等，当两个分量均不相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbneux2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否均不相等的结果。特殊值：±0→false；inf→false；-inf→false；inf→true；任一分量含nan→true（任一输入分量为nan时，该分量≠比较结果为true）。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbnex2](_hbnex2.md)（`same_topic`）：返回值：比较输入数据各分量是否均不相等的结果。特殊值：±0→false；inf→false；-inf→false；inf→true；任一分量含nan→true（任一输入分量为nan时，该分量≠比较结果为true）。；返回值：比较输入数据各分量是否均不相等的结果。特殊值：任一分量为nan→false；±0→false；±inf→相同符号inf返回false，不同符号inf返回true。。两接口都判断 bfloat16x2 两分量是否均不相等，关键差异是 NaN 与无穷值的比较语义，选型时必须成对辨析。
<!-- cannbot:related:end -->
