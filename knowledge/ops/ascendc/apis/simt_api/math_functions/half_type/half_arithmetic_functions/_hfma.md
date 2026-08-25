---
type: API
title: __hfma
description: 对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_arithmetic_functions/__hfma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# __hfma

功能：对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理。

函数原型：half __hfma(half x, half y, half z)

参数：x（输入）源操作数，y（输入）源操作数，z（输入）源操作数。

返回值：x * y + z的值。本接口受全局饱和模式影响，。特殊值：(x*y = inf,-inf,nan)→0；(x*y = -inf,inf,nan)→0；(x*y+z超出ASCRT_MAX_NORMAL_FP16,inf)→ASCRT_MAX_NORMAL_FP16；(x*y+z小于ASCRT_MAX_NORMAL_FP16,-inf)→-ASCRT_MAX_NORMAL_FP16；(x、y、z任意一个为nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：该卡用抵消输入验证一次与两次舍入的 ULP 差异。
- [__hfmax2](../../bfloat16_type/bfloat16x2_arithmetic_functions/_hfmax2.md)（`related`）：焦点处理half/bfloat16 x2 融合乘加与 ReLU 变体；__hfma正文界定“对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理”。候选保持 x2 乘加语义，只改变 half/bfloat16、scalar 或 ReLU 融合形态。
- [__hmul](_hmul.md)（`related`）：HFMA 一次舍入，HMul 后 HAdd 是两次舍入，精度可能不同。
- [__hadd](_hadd.md)（`same_topic`）：__hadd 与《__hfma》的实质衔接是：__hadd 与 half/bfloat16/half2 的加法入口共享加法与 RINT 语义；sub、mul、fma 用于区分运算符而避免把算术族名称当作等价替换。
- [__hfma](../../bfloat16_type/bfloat16_arithmetic_functions/_hfma.md)（`same_topic`）：bfloat16 版本完成同一融合乘加，源精度不同。
- [__hfma_relu](_hfma_relu.md)（`same_topic`）：__hfma_relu 与《__hfma》的实质衔接是：__hfma_relu 在 half 上执行 x*y+z 后 ReLU；基础 hfma 与 bfloat16 对应入口拆分类型，两个历史命名为 hfmax2_relu 的卡正文同样是 packed FMA+ReLU 契约。
- [__hsub](_hsub.md)（`same_topic`）：__hsub 与《__hfma》的实质衔接是：__hsub 与 half/bfloat16/half2 的减法入口共享 RINT 差值语义；add/mul/fma 用于区分相邻算术操作而不能作为等价替换。
<!-- cannbot:related:end -->
