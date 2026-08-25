---
type: API
title: H2Rint
description: 获取与输入数据各元素最接近的整数，若存在两个同样接近的整数，则取其中的偶数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2rint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# H2Rint

功能：获取与输入数据各元素最接近的整数，若存在两个同样接近的整数，则取其中的偶数。

函数原型：bfloat16x2_t h2rint(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：与输入各元素最接近的整数值。本接口受全局饱和模式影响，。特殊值：0→0；-0→0；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→-ASCRT_MIN_DENORM_BF16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Ceil](h2ceil.md)（`related`）：H2Ceil 按向正无穷取整，是 H2Rint 的方向性替代，并共享全局饱和影响。
- [H2Floor](h2floor.md)（`related`）：H2Floor 与 H2Rint 处理相同 packed BF16x2，但按向负无穷取整；负数和半整数结果需按 oracle 选型。
- [H2Rint](../../half_type/half2_math_functions/h2rint.md)（`related`）：两者都对 packed 两元素执行 nearest-even 整数化并受全局饱和状态影响，差别仅为 BF16x2 与 half2，可用于 dtype 迁移。
- [H2Trunc](h2trunc.md)（`related`）：H2Trunc 向零截断，与 nearest-even 在小数输入上不同；可据目标舍入契约直接选择。
<!-- cannbot:related:end -->
