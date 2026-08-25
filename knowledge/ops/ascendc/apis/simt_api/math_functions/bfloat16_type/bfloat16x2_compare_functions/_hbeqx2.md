---
type: API
title: __hbeqx2
description: 比较两个bfloat16x2_t类型数据的两个分量是否相等，仅当两个分量均相等时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hbeqx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbeqx2

功能：比较两个bfloat16x2_t类型数据的两个分量是否相等，仅当两个分量均相等时返回true。

函数原型：bool __hbeqx2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否均相等的结果。特殊值：nan→false；(任意值,nan)→false；0→true；-0→true；inf→true；-inf→true；inf→false。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbequx2](_hbequx2.md)（`related`）：“__hbequx2”定义：比较两个bfloat16x2_t类型数据的两个分量是否相等，当两个分量均相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。；“__hbeqx2”定义：比较两个bfloat16x2_t类型数据的两个分量是否相等，仅当两个分量均相等时返回true。。实质衔接：half2 版保持 unordered 双分量全等布尔语义；__hequx2 改为逐分量数值结果，__hbeqx2 改为 NaN 不视为相等，选择时必须区分。
- [__hbeqx2](../../half_type/half2_compare_functions/_hbeqx2.md)（`related`）：half2 同名函数也要求两个分量都相等才返回 true，是跨 dtype 对应物。
- [__hbnex2](_hbnex2.md)（`related`）：hbeqx2 执行相反的相等判断，可用于核对分支反转或构造不等掩码的验证对照。
- [__heqx2](_heqx2.md)（`same_topic`）：__heqx2 返回逐分量比较结果，而 __hbeqx2 把两分量合并为单 bool；二者按输出粒度选型。
- [__heqx2_mask](_heqx2_mask.md)（`same_topic`）：mask 版本把两个分量编码到位掩码，适合后续位选择而非控制流 bool。
<!-- cannbot:related:end -->
