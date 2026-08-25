---
type: API
title: Hceil
description: 获取大于或等于输入bfloat16_t数据的最小整数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hceil.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hceil

获取大于或等于输入数据的最小整数值。
函数原型：bfloat16_t hceil(bfloat16_t x)
返回值：大于或等于输入数据的最小整数值。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Hrint](hrint.md)（`related`）：Hrint 提供最近偶数取整，与 Hceil 的定向向上取整形成舍入模式对照。
- [Hfloor](hfloor.md)（`same_topic`）：Hfloor 与《Hceil》的实质衔接是：Hfloor 对 bfloat16 向负无穷取整；half/packed/float、Hceil/Hrint/Htrunc 和 Tensor/Reg Floor 入口直接对照类型及舍入方向。
<!-- cannbot:related:end -->
