---
type: API
title: Hexp10
description: 计算bfloat16_t输入x的10的x次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hexp10.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hexp10

指定输入x，获取10的x次方。
函数原型：bfloat16_t hexp10(bfloat16_t x)
返回值：10的x次方。本接口受全局饱和模式影响，特殊值如下：
约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [BFloat16数学函数hexp](hexp.md)（`related`）：Hexp 计算 e^x，与 Hexp10 共同覆盖自然指数和十进制指数转换需求，并共享 FTZ 特殊值边界。
- [Exp10f](../../float_math_functions/exp10f.md)（`related`）：Hexp10 与 Exp10f 都计算 10^x，但分别处理 bfloat16_t 与 float；BF16 版本还明确 subnormal 刷零边界。
- [H2Exp10](../bfloat16x2_math_functions/h2exp10.md)（`related`）：H2Exp10 对两个 bfloat16 lane 计算 10 的幂，Hexp10 是同 dtype 的标量版本，连接 packed 与 scalar 实现。
- [Hexp10](../../half_type/half_math_functions/hexp10.md)（`related`）：bfloat16 Hexp10 与 focal 数学语义相同但精度类型不同，可用于 half 与 bfloat16 计算路径选型。
- [Hexp2](hexp2.md)（`related`）：Hexp2 与 Hexp10 仅指数底数不同，分别实现 2^x 与 10^x，可按缩放公式和数值范围选择。
<!-- cannbot:related:end -->
