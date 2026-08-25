---
type: API
title: 接口变更说明（附录）
description: 为了优化API命名，使其更加清晰和易于理解，当前版本相比于CANN8.5.0及前序版本，部分API命名有变更，具体变更情况请参考以下表格：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/interface_change_description.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 接口变更说明（附录）

为了优化API命名，使其更加清晰和易于理解，当前版本相比于CANN8.5.0及前序版本，部分API命名有变更，具体变更情况请参考以下表格：

统计uint64_t类型数值的二进制表示中前导0的个数（二进制表示中最高有效位到第一个'1'的'0'的数量，输入为0时返回64）。 以如下CountLeadingZero调用为例： 其计算结果如下图所示： 图1 CountLeadingZero计算示意图

本接口组包含 CountLeadingZero, Cast（float转half、int32_t）, Cast（float转bfloat16_t），辅助接口包括 GetBitCount, GetSFFValue。

返回值：返回valueIn的前导0的个数。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
