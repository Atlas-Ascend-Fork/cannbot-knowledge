---
type: API
title: __hadd
description: 计算两个half类型数据相加的结果，并遵循CAST_RINT模式对结果进行舍入处理。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_arithmetic_functions/__hadd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hadd

功能：计算两个half类型数据相加的结果，并遵循CAST_RINT模式对结果进行舍入处理。

函数原型：half __hadd(const half x, const half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据相加的结果。特殊值：(±inf,±inf,±inf)→±ASCRT_MAX_NORMAL_FP16；(±inf,∓inf,nan)→0；(±0,±0,±0)→±0；(x，y任意一个为nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hadd](../../bfloat16_type/bfloat16_arithmetic_functions/_hadd.md)（`same_topic`）：__hadd 与《__hadd》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
- [__haddx2](../../bfloat16_type/bfloat16x2_arithmetic_functions/_haddx2.md)（`same_topic`）：__hadd 与《__haddx2》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
- [__haddx2](../half2_arithmetic_functions/_haddx2.md)（`same_topic`）：__hadd 与《__haddx2》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
- [__hfma](_hfma.md)（`same_topic`）：__hadd 与《__hfma》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
- [__hmul](_hmul.md)（`same_topic`）：__hadd 与《__hmul》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
- [__hsub](_hsub.md)（`same_topic`）：__hadd 与《__hsub》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
<!-- cannbot:related:end -->
