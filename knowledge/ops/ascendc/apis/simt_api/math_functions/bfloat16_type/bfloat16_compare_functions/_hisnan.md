---
type: API
title: __hisnan
description: 判断bfloat16类型浮点数是否为nan，输入为nan时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hisnan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hisnan

判断bfloat16类型浮点数是否为nan，输入为nan时返回true。
判断浮点数是否为nan。
函数原型：bool __hisnan(bfloat16_t x)
返回值：接口功能不受全局饱和模式影响。返回值为：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [IsNan接口](../../../../simd_api/adv_api/math_compute/is_nan_interface/is_nan_interface.md)（`related`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《__hisnan》提供“判断bfloat16类型浮点数是否为nan，输入为nan时返回true。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [__hleu](_hleu.md)（`same_topic`）：__hleu 与《__hisnan》的实质衔接是：bfloat16 unordered LE 需与 ordered LE、GE/LT/GT、isnan 和 neq 对照 NaN 行为。
<!-- cannbot:related:end -->
