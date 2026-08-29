---
type: API
title: CountLeadingZero
description: 统计uint64_t数值二进制表示中前导0的个数，输入为0时返回64。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/CountLeadingZero.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# CountLeadingZero

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

统计uint64_t类型数值的二进制表示中前导0的个数（二进制表示中最高有效位到第一个'1'的'0'的数量，输入为0时返回64）。

以如下CountLeadingZero调用为例
其计算结果如下图所示

参数：valueIn(输入): 被统计的二进制数字。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_clz（标量计算）](../../c_api/scalar_compute/asc_clz.md)（`same_topic`）：计算一个uint64_t类型整数在二进制表示下的前导零个数；统计uint64_t类型数值的二进制表示中前导0的个数（二进制表示中最高有效位到第一个'1'的'0'的数量，输入为0时返回64）。。两页提供同一 uint64 前导零计数语义，分别是 C API 标量入口与基础 API 入口。
<!-- cannbot:related:end -->
