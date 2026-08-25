---
type: API
title: __hbequx2
description: 比较两个bfloat16x2_t类型数据的两个分量是否相等，当两个分量均相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hbequx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbequx2

功能：比较两个bfloat16x2_t类型数据的两个分量是否相等，当两个分量均相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbequx2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否均相等的结果。特殊值：任意分量含nan→true；0→true；-0→true；inf→true；-inf→true；inf→false；-inf→false。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbeqx2](_hbeqx2.md)（`related`）：“__hbequx2”定义：比较两个bfloat16x2_t类型数据的两个分量是否相等，当两个分量均相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。；“__hbeqx2”定义：比较两个bfloat16x2_t类型数据的两个分量是否相等，仅当两个分量均相等时返回true。。实质衔接：half2 版保持 unordered 双分量全等布尔语义；__hequx2 改为逐分量数值结果，__hbeqx2 改为 NaN 不视为相等，选择时必须区分。
- [__hequx2](_hequx2.md)（`related`）：“__hbequx2”定义：比较两个bfloat16x2_t类型数据的两个分量是否相等，当两个分量均相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。；“__hequx2”定义：比较两个bfloat16x2_t类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。。实质衔接：half2 版保持 unordered 双分量全等布尔语义；__hequx2 改为逐分量数值结果，__hbeqx2 改为 NaN 不视为相等，选择时必须区分。
- [__hbequx2](../../half_type/half2_compare_functions/_hbequx2.md)（`same_topic`）：“__hbequx2”定义：比较两个bfloat16x2_t类型数据的两个分量是否相等，当两个分量均相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。；“__hbequx2”定义：比较两个half2类型数据的两个分量是否相等，当两个分量均相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。。实质衔接：half2 版保持 unordered 双分量全等布尔语义；__hequx2 改为逐分量数值结果，__hbeqx2 改为 NaN 不视为相等，选择时必须区分。
- [__heqx2](_heqx2.md)（`same_topic`）：无序相等变体在 NaN 处理上不同；包含 NaN 的测试必须按所需谓词选择。
<!-- cannbot:related:end -->
