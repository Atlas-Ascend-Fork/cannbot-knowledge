---
type: API
title: __hbgtx2
description: 比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数大于第二个数时，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hbgtx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbgtx2

功能：比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数大于第二个数时，返回true。

函数原型：bool __hbgtx2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数大于第二个数的结果。特殊值：任一分量含nan→false；inf→true；inf→true；-inf→false；0→false。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgtx2](_hgtx2.md)（`related`）：__hbgtx2 把两个 ordered > lane 聚合成单 bool，只有两 lane 都成立才为 true；focal 保留逐 lane 1.0/0.0。
- [__hbgtux2](_hbgtux2.md)（`same_topic`）：__hbgtux2说明比较两个bfloat16x2_t类型数据的两个分量，当两个分量均满足第一个数大于第二个数时，返回true。若任一输入的分量为nan，该分量的比较结果为true。
- [__hbgtx2](../../half_type/half2_compare_functions/_hbgtx2.md)（`same_topic`）：__hbgtx2说明比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于第二个数时返回true。
- [__hgtx2_mask](_hgtx2_mask.md)（`same_topic`）：__hgtx2_mask说明比较两个bfloat16x2_t类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于第二个数，则对应16位掩码为0xFFFF，否则为0x0。
<!-- cannbot:related:end -->
