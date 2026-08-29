---
type: API
title: GetSFFValue
description: 查找uint64_t数值二进制表示中从最低有效位开始的首个指定比特值位置，未找到则返回-1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/GetSFFValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetSFFValue

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

查找uint64_t类型数值的二进制表示中从最低有效位开始的首个指定比特值（0或1）的位置，如果没找到则返回-1。

以如下GetSFFValue调用为例
其计算结果如下图所示

参数：countValue: 指定要查找的比特值，取值为0或1。；valueIn(输入): 被查找的二进制数字。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_ffs（标量计算）](../../c_api/scalar_compute/asc_ffs.md)（`same_topic`）：FindFirstSet接口，输入数据的二进制表示中从最低位向最高位查找第一个值为1的位，并返回其位置，如果没找到则返回-1。；查找uint64_t类型数值的二进制表示中从最低有效位开始的首个指定比特值（0或1）的位置，如果没找到则返回-1。。两张接口卡共享从低位搜索首个目标 bit 的核心契约，GetSFFValue 将 asc_ffs 的固定查 1 扩展为可指定查 0 或 1。
<!-- cannbot:related:end -->
