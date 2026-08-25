---
type: API
title: __hle
description: 比较两个bfloat16类型的数据，仅当第一个数据小于或等于第二个数据时，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hle.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hle

比较两个bfloat16类型的数据，仅当第一个数据小于或等于第二个数据时，返回true。
函数原型：bool __hle(bfloat16_t x, bfloat16_t y)
返回值：输入的第一个数是否小于或等于第二个数的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hle](../../half_type/half_compare_functions/_hle.md)（`related`）：half __hle 与 BF16 __hle 具有相同 ordered <= 和 NaN=false 契约，可在低精度 dtype 切换时保持比较语义。
- [__hlt](_hlt.md)（`related`）：__hlt 把 <= 收紧为 < 且同为 ordered，比边界相等元素是否命中时可直接对照。
- [__hleu](_hleu.md)（`same_topic`）：__hle 与 __hleu 都执行 bfloat16 的 ≤ 比较；区别仅在 NaN 时 ordered 版本返回 false、unordered 版本返回 true，核心谓词合同相同。
<!-- cannbot:related:end -->
