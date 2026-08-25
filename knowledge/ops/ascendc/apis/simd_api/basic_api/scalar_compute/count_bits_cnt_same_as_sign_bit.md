---
type: API
title: CountBitsCntSameAsSignBit
description: 统计int64_t数值二进制表示中从最高数值位开始与符号位相同的连续比特位个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/CountBitsCntSameAsSignBit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# CountBitsCntSameAsSignBit

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

统计int64_t类型数值的二进制表示中，从最高数值位开始与符号位相同的连续比特位的个数。

以如下CountBitsCntSameAsSignBit调用为例
其计算结果如下图所示

参数：valueIn(输入): 被统计的二进制数字。

约束：当输入是-1（比特位全1）或者0（比特位全0）时，返回-1。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030 支持。
