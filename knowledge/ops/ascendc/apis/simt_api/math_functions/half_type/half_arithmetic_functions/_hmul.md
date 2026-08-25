---
type: API
title: __hmul
description: 计算两个half类型数据相乘的结果，并遵循CAST_RINT模式对结果进行舍入处理。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_arithmetic_functions/__hmul.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hmul

功能：计算两个half类型数据相乘的结果，并遵循CAST_RINT模式对结果进行舍入处理。

函数原型：half __hmul(const half x, const half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据相乘的结果。特殊值：(±0,±inf,nan)→0；(inf,inf,inf)→ASCRT_MAX_NORMAL_FP16；(inf,-inf,-inf)→-ASCRT_MAX_NORMAL_FP16；(x，y任意一个为nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hfma](_hfma.md)（`related`）：HFMA 一次舍入，HMul 后 HAdd 是两次舍入，精度可能不同。
- [__hmul](../../bfloat16_type/bfloat16_arithmetic_functions/_hmul.md)（`related`）：两卡提供相同标量低精度乘法并采用 CAST_RINT，但分别面向 half 与 bfloat16；输入类型和特殊值范围决定入口选择。
- [__hadd](_hadd.md)（`same_topic`）：__hadd 与《__hmul》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
- [__hsub](_hsub.md)（`same_topic`）：__hsub 与《__hmul》的实质衔接是：__hsub 与 half/bfloat16/half2 的减法入口共享 RINT 差值语义；add/mul/fma 用于区分相邻算术操作而不能作为等价替换。
<!-- cannbot:related:end -->
