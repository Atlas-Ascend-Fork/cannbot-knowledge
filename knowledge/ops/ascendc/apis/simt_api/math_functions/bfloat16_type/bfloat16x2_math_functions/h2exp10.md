---
type: API
title: H2Exp10
description: 指定输入x，对x的各元素，获取10的该元素次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2exp10.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Exp10

功能：指定输入x，对x的各元素，获取10的该元素次方。

函数原型：bfloat16x2_t h2exp10(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入的各元素，10的该元素次方。本接口受全局饱和模式影响，。特殊值：0→0；-0→0；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→0。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Hexp10](../bfloat16_math_functions/hexp10.md)（`related`）：H2Exp10 对两个 bfloat16 lane 计算 10 的幂，Hexp10 是同 dtype 的标量版本，连接 packed 与 scalar 实现。
- [H2Exp10](../../half_type/half2_math_functions/h2exp10.md)（`same_topic`）：H2Exp10：H2Exp10 的 bfloat16x2同名接口和 half/float标量 exp10保持底数10，H2Exp/H2Exp2则直接帮助避免把 e^x、2^x 与10^x混用。 目标卡《H2Exp10》补充：指定输入x，对x的各元素，获取10的该元素次方。
<!-- cannbot:related:end -->
