---
type: API
title: __high2bfloat16
description: 从bfloat16x2_t类型输入数据中提取高16位，作为bfloat16_t类型返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__high2bfloat16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __high2bfloat16

提取输入bfloat16x2的高16位，并返回。
函数原型：bfloat16_t __high2bfloat16(const bfloat16x2_t x)
返回值：返回输入bfloat16x2的高16位。特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__lowhigh2highlow](_lowhigh2highlow.md)（`related`）：交换后常需提取新的高分量，__high2bfloat16 提供标量读取路径并明确返回类型。
- [__high2bfloat162](_high2bfloat162.md)（`same_topic`）：《__high2bfloat16》处理“从bfloat16x2_t类型输入数据中提取高16位，作为bfloat16_t类型返回。”。《__high2bfloat162》提供“将bfloat16x2_t输入数据的高16位填充到bfloat16x2_t的前后两个分量，返回填充后的数据。”，其具体合同或探针直接接入packed bfloat16 高 lane 提取、复制、交换和 half2 对应实现。
- [__high2float](_high2float.md)（`same_topic`）：《__high2bfloat16》处理“从bfloat16x2_t类型输入数据中提取高16位，作为bfloat16_t类型返回。”。《__high2float》提供“将bfloat16x2_t输入数据的高16位转换为float类型并返回结果。”，其具体合同或探针直接接入packed bfloat16 高 lane 提取、复制、交换和 half2 对应实现。
- [__high2half](../../half_type/half_precision_conversion_functions/_high2half.md)（`same_topic`）：《__high2bfloat16》处理“从bfloat16x2_t类型输入数据中提取高16位，作为bfloat16_t类型返回。”。《__high2half》提供“提取输入half2的高16位，并返回。”，其具体合同或探针直接接入packed bfloat16 高 lane 提取、复制、交换和 half2 对应实现。
- [__highs2bfloat162](_highs2bfloat162.md)（`same_topic`）：《__high2bfloat16》处理“从bfloat16x2_t类型输入数据中提取高16位，作为bfloat16_t类型返回。”。《__highs2bfloat162》提供“分别提取两个bfloat162输入的高16位，并填充到bfloat162中，返回填充后的数据。”，其具体合同或探针直接接入packed bfloat16 高 lane 提取、复制、交换和 half2 对应实现。
- [__low2bfloat162](_low2bfloat162.md)（`same_topic`）：《__high2bfloat16》处理“从bfloat16x2_t类型输入数据中提取高16位，作为bfloat16_t类型返回。”。《__low2bfloat162》提供“将bfloat16x2_t输入数据的低16位填充到bfloat16x2_t的前后两个分量，返回填充后的数据。”，其具体合同或探针直接接入packed bfloat16 高 lane 提取、复制、交换和 half2 对应实现。
<!-- cannbot:related:end -->
