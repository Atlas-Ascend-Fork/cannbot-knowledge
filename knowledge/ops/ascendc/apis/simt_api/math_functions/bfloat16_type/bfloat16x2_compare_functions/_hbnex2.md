---
type: API
title: __hbnex2
description: 比较两个bfloat16x2_t类型数据的两个分量是否不相等，仅当两个分量均不相等时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hbnex2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbnex2

功能：比较两个bfloat16x2_t类型数据的两个分量是否不相等，仅当两个分量均不相等时返回true。

函数原型：bool __hbnex2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否均不相等的结果。特殊值：任一分量为nan→false；±0→false；±inf→相同符号inf返回false，不同符号inf返回true。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbeqx2](_hbeqx2.md)（`related`）：hbeqx2 执行相反的相等判断，可用于核对分支反转或构造不等掩码的验证对照。
- [__hbnex2](../../half_type/half2_compare_functions/_hbnex2.md)（`related`）：bfloat16x2 __hbnex2 保持“两个分量均不等才为 true”的归约规则，仅替换数值格式。
- [__hbneux2](_hbneux2.md)（`same_topic`）：__hbneux2 与 __hbnex2 都在两个 lane 均不等时返回 bool，唯一关键差异是 unordered 版本把 NaN 分量判为不等，而 ordered 版本含 NaN 返回 false。
- [__hnex2](_hnex2.md)（`same_topic`）：hnex2 是对应的 half2/packed 比较入口，便于按输入表示映射同一逐 lane 不等判定。
- [__hnex2_mask](_hnex2_mask.md)（`same_topic`）：mask 版本把逐 lane 比较结果编码为掩码，适合后续分支/选择而非直接 packed 布尔结果。
<!-- cannbot:related:end -->
