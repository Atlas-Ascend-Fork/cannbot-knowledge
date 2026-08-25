---
type: API
title: __low2bfloat162
description: 将bfloat16x2_t输入数据的低16位填充到bfloat16x2_t的前后两个分量，返回填充后的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__low2bfloat162.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __low2bfloat162

功能：将输入数据的低16位填充到bfloat16x2并返回。

函数原型：bfloat16x2_t __low2bfloat162(const bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据的低16位填充到bfloat16x2的结果。特殊值：0→(0, 0)；-0→(-0, -0)；nan→(nan, nan)；inf→(inf, inf)；-inf→(-inf, -inf)；ASCRT_MAX_NORMAL_BF16→(ASCRT_MAX_NORMAL_BF16, ASCRT_MAX_NORMAL_BF16)；-ASCRT_MAX_NORMAL_BF16→(-ASCRT_MAX_NORMAL_BF16, -ASCRT_MAX_NORMAL_BF16)。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__high2bfloat162](_high2bfloat162.md)（`related`）：__low2bfloat162 与《__high2bfloat162》的实质衔接是：low/high 与单输入复制、双输入拼装接口共同定义 bfloat16x2 的分量选择和装配顺序。
- [__lows2bfloat162](_lows2bfloat162.md)（`related`）：__lows2bfloat162 与《__low2bfloat162》的实质衔接是：lows/highs、单输入复制与双输入拼装共同定义 bfloat16x2 低高 lane 的提取和构造顺序。
- [__high2bfloat16](_high2bfloat16.md)（`same_topic`）：《__high2bfloat16》处理“从bfloat16x2_t类型输入数据中提取高16位，作为bfloat16_t类型返回。”。《__low2bfloat162》提供“将bfloat16x2_t输入数据的低16位填充到bfloat16x2_t的前后两个分量，返回填充后的数据。”，其具体合同或探针直接接入packed bfloat16 高 lane 提取、复制、交换和 half2 对应实现。
- [__highs2bfloat162](_highs2bfloat162.md)（`same_topic`）：__low2bfloat162 与《__highs2bfloat162》的实质衔接是：low/high 与单输入复制、双输入拼装接口共同定义 bfloat16x2 的分量选择和装配顺序。
- [__low2bfloat16](_low2bfloat16.md)（`same_topic`）：__low2bfloat162 与《__low2bfloat16》的实质衔接是：low/high 与单输入复制、双输入拼装接口共同定义 bfloat16x2 的分量选择和装配顺序。
<!-- cannbot:related:end -->
