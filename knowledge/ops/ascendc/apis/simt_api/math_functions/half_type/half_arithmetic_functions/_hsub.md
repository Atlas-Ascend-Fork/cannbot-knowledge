---
type: API
title: __hsub
description: 计算两个half类型数据相减的结果，并遵循CAST_RINT模式对结果进行舍入处理。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_arithmetic_functions/__hsub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hsub

功能：计算两个half类型数据相减的结果，并遵循CAST_RINT模式对结果进行舍入处理。

函数原型：half __hsub(const half x, const half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据相减的结果。本接口受全局饱和模式影响，。特殊值：(±inf,±inf,nan)→0；(±inf,∓inf,±inf)→±ASCRT_MAX_NORMAL_FP16；(x，y任意一个为nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hneg](_hneg.md)（`related`）：取负常用于 x-y = x+(-y)，但直接 HSub 的舍入链不同。
- [__hadd](_hadd.md)（`same_topic`）：__hadd 与《__hsub》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
- [__hfma](_hfma.md)（`same_topic`）：__hsub 与《__hfma》的实质衔接是：__hsub 与 half/bfloat16/half2 的减法入口共享 RINT 差值语义；add/mul/fma 用于区分相邻算术操作而不能作为等价替换。
- [__hmul](_hmul.md)（`same_topic`）：__hsub 与《__hmul》的实质衔接是：__hsub 与 half/bfloat16/half2 的减法入口共享 RINT 差值语义；add/mul/fma 用于区分相邻算术操作而不能作为等价替换。
- [__hsub](../../bfloat16_type/bfloat16_arithmetic_functions/_hsub.md)（`same_topic`）：__hsub 与《__hsub》的实质衔接是：__hsub 与 half/bfloat16/half2 的减法入口共享 RINT 差值语义；add/mul/fma 用于区分相邻算术操作而不能作为等价替换。
- [__hsubx2](../../bfloat16_type/bfloat16x2_arithmetic_functions/_hsubx2.md)（`same_topic`）：__hsub 与《__hsubx2》的实质衔接是：__hsub 与 half/bfloat16/half2 的减法入口共享 RINT 差值语义；add/mul/fma 用于区分相邻算术操作而不能作为等价替换。
<!-- cannbot:related:end -->
