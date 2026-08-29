---
type: API
title: __hnex2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hnex2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hnex2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。

函数原型：bfloat16x2_t __hnex2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否不相等的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：±0→0；nan与任意值→0；±inf与相同值→0；±inf与不同值→1.0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hnex2_mask](_hnex2_mask.md)（`same_topic`）：结果以unsigned int形式返回；对应比较结果为1.0，否则为0.0。两端执行同一 bfloat16x2 不等比较，但分别返回位掩码和数值向量；对照可按后续位操作或数值计算选择正确返回合同。
<!-- cannbot:related:end -->
