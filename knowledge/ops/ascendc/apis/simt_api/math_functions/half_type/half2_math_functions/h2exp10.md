---
type: API
title: H2Exp10
description: 指定输入x，对x的各元素，获取10的该元素次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2exp10.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Exp10

功能：指定输入x，对x的各元素，获取10的该元素次方。

函数原型：half2 h2exp10(half2 x)

参数：x（输入）源操作数。

返回值：输入的各元素，10的该元素次方。特殊值：±0→1；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Exp](h2exp.md)（`related`）：H2Exp10：H2Exp10 的 bfloat16x2同名接口和 half/float标量 exp10保持底数10，H2Exp/H2Exp2则直接帮助避免把 e^x、2^x 与10^x混用。 目标卡《H2Exp》补充：指定输入x，对x的各元素，获取e的该元素次方。
- [H2Exp2](h2exp2.md)（`related`）：H2Exp10：H2Exp10 的 bfloat16x2同名接口和 half/float标量 exp10保持底数10，H2Exp/H2Exp2则直接帮助避免把 e^x、2^x 与10^x混用。 目标卡《H2Exp2》补充：指定输入x，对x的各元素，获取2的该元素次方。
- [Exp10f](../../float_math_functions/exp10f.md)（`same_topic`）：H2Exp10：H2Exp10 的 bfloat16x2同名接口和 half/float标量 exp10保持底数10，H2Exp/H2Exp2则直接帮助避免把 e^x、2^x 与10^x混用。 目标卡《Exp10f》补充：指定输入x，获取10的x次方。
- [H2Exp10](../../bfloat16_type/bfloat16x2_math_functions/h2exp10.md)（`same_topic`）：H2Exp10：H2Exp10 的 bfloat16x2同名接口和 half/float标量 exp10保持底数10，H2Exp/H2Exp2则直接帮助避免把 e^x、2^x 与10^x混用。 目标卡《H2Exp10》补充：指定输入x，对x的各元素，获取10的该元素次方。
- [Hexp10](../half_math_functions/hexp10.md)（`same_topic`）：H2Exp10：H2Exp10 的 bfloat16x2同名接口和 half/float标量 exp10保持底数10，H2Exp/H2Exp2则直接帮助避免把 e^x、2^x 与10^x混用。 目标卡《Hexp10》补充：计算half输入x的10的x次方。
<!-- cannbot:related:end -->
