---
type: Guide
title: torch逐点与foreach运算：函数级类型和数值限制
description: 核对torch数学函数及foreach条目的局部类型、广播、输出dtype和可能CPU回退条件。
tags:
- task.optimization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md
  role: constraint
created_at: '2026-11-09T14:10:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# torch逐点与foreach运算：函数级类型和数值限制

## 固定来源与参数表的范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的2.7.1、2.9至2.14中英文torch页；下表默认2.14，较早版本与实际收录语言另列。产品为A2/A3训练系列和950DT，不扩到950PR，不回推26.0/PyTorch2.8发布基线。

每行的input、dtype、tensors等是该条目的局部字段，不与Tensor方法的self表互换，不表示返回值或整个模型的数据类型。没有独立类型表、未收录语言/版本不等于已证实不支持；显式产品排除和额外条件另列。不借同名别名、父对象或相邻函数补齐参数、默认值与实现。这里仅静态核对，没有运行上游、编译、加载文件或进行设备实验。

## 函数与别名分别消费

已收录条目的产品表列三产品，局部dtype和限制仍分别适用。例如abs与absolute、asin与arcsin、atan与arctan、clamp与clip有不同表，不能据别名关系取并集，也不沿用Tensor同名方法的self范围。foreach的大量中文条目只有产品表，既不证明任意列表/stride/原地组合都可用，也不保证批量融合或性能收益。
## 函数级参数类型

| 函数/对象 | 局部参数类型表 | 来源 |
| --- | --- | --- |
| `torch.fix`、`torch.logit` | input=BF16/FP16/FP32 | 中英文 |
| `torch.pow` | input=BF16/FP16/FP32/FP64/INT16/INT64 | 中英文 |
| `torch.round` | input=BF16/FP16/FP32/FP64/INT32/INT64 | 中英文 |
| `torch.erf`、`torch.expm1` | input=BF16/FP16/FP32/FP64/INT64/BOOL | 中英文 |
| `torch.exp` | input=BF16/FP16/FP32/FP64/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.clip`、`torch.floor`、`torch.sub` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch._foreach_sqrt`、`torch.abs`、`torch.add`、`torch.asin`、`torch.atan`、`torch.deg2rad`、`torch.rad2deg`、`torch.sqrt` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.acosh`、`torch.arccosh`、`torch.cosh`、`torch.log`、`torch.log10`、`torch.log2`、`torch.square`、`torch.tan` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.addcmul` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT32/INT64 | 中英文 |
| `torch.sign` | input=BF16/FP16/FP32/INT32/INT64/BOOL | 中英文 |
| `torch.sgn` | input=BF16/FP16/FP32/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch._foreach_neg_` | input=BF16/FP16/FP32/INT8/INT32/INT64 | 中英文 |
| `torch.neg`、`torch.negative` | input=BF16/FP16/FP32/INT8/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.absolute`、`torch.clamp` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch._foreach_asin`、`torch.arcsin`、`torch.copysign`、`torch.div`、`torch.divide`、`torch.exp2`、`torch.nan_to_num`、`torch.tanh`、`torch.true_divide` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.float_power` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX128 | 中英文 |
| `torch.cos`、`torch.logical_and`、`torch.logical_or`、`torch.mul`、`torch.multiply`、`torch.reciprocal`、`torch.rsqrt`、`torch.sin` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.positive` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.fmod` | input=BF16/FP16/FP32/UINT8/INT8/INT32/INT64 | 中英文 |
| `torch.addcdiv`、`torch.ceil`、`torch.lerp`、`torch.trunc` | input=FP16/FP32 | 中英文 |
| `torch.real` | input=FP16/FP32/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.sinh` | input=FP16/FP32/FP64 | 中英文 |
| `torch.combinations` | input=FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.remainder` | input=FP16/FP32/INT16/INT32/INT64 | 中英文 |
| `torch.erfc` | input=FP16/FP32/INT64/BOOL | 中英文 |
| `torch.floor_divide` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.acos`、`torch.arccos`、`torch.arctan`、`torch.arctan2`、`torch.atan2`、`torch.erfinv`、`torch.log1p`、`torch.logical_not`、`torch.xlogy` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.angle` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64 | 中英文 |
| `torch.arcsinh`、`torch.arctanh`、`torch.asinh`、`torch.atanh`、`torch.logical_xor`、`torch.sigmoid` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.ldexp` | input=FP16/FP64/COMPLEX64 | 中英文 |
| `torch.softmax` | input=FP32 | 中英文 |
| `torch.bitwise_left_shift`、`torch.bitwise_right_shift` | input=UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.bitwise_and`、`torch.bitwise_not`、`torch.bitwise_or`、`torch.bitwise_xor` | input=UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.heaviside`、`torch.logaddexp`、`torch.logaddexp2` | 未给独立参数类型表 | 中英文 |
| `torch._foreach_abs`、`torch._foreach_abs_`、`torch._foreach_acos`、`torch._foreach_acos_`、`torch._foreach_asin_`、`torch._foreach_atan`、`torch._foreach_atan_`、`torch._foreach_ceil`、`torch._foreach_ceil_`、`torch._foreach_cos`、`torch._foreach_cos_`、`torch._foreach_cosh`、`torch._foreach_cosh_`、`torch._foreach_erf`、`torch._foreach_erf_`、`torch._foreach_erfc`、`torch._foreach_erfc_`、`torch._foreach_exp`、`torch._foreach_exp_`、`torch._foreach_expm1`、`torch._foreach_expm1_`、`torch._foreach_floor`、`torch._foreach_floor_`、`torch._foreach_frac`、`torch._foreach_frac_`、`torch._foreach_lgamma`、`torch._foreach_lgamma_`、`torch._foreach_log`、`torch._foreach_log10`、`torch._foreach_log10_`、`torch._foreach_log1p`、`torch._foreach_log1p_`、`torch._foreach_log2`、`torch._foreach_log2_`、`torch._foreach_log_`、`torch._foreach_neg`、`torch._foreach_reciprocal`、`torch._foreach_reciprocal_`、`torch._foreach_round`、`torch._foreach_round_`、`torch._foreach_sigmoid`、`torch._foreach_sigmoid_`、`torch._foreach_sin`、`torch._foreach_sin_`、`torch._foreach_sinh`、`torch._foreach_sinh_`、`torch._foreach_sqrt_`、`torch._foreach_tan`、`torch._foreach_tan_`、`torch._foreach_trunc`、`torch._foreach_trunc_`、`torch._foreach_zero_`、`torch.conj_physical`、`torch.fill_`、`torch.frac`、`torch.frexp`、`torch.gcd`、`torch.hypot`、`torch.imag`、`torch.lcm`、`torch.lgamma`、`torch.nan_to_num_`、`torch.nextafter`、`torch.renorm`、`torch.rsub`、`torch.signbit`、`torch.threshold` | 未给独立参数类型表 | 仅中文 |

## 较早版本的不同参数表

| 函数/对象 | 文档版本 | 当时参数表 | 2.14参数表 | 来源 |
| --- | --- | --- | --- | --- |
| `torch.softmax` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64 | input=FP32 | 中英文 |
| `torch.remainder` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/INT32/INT64 | input=FP16/FP32/INT16/INT32/INT64 | 中英文 |
| `torch.sign` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/INT32/INT64/BOOL | input=BF16/FP16/FP32/INT32/INT64/BOOL | 中英文 |
| `torch.exp` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/INT64/BOOL | input=BF16/FP16/FP32/FP64/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.pow` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | input=BF16/FP16/FP32/FP64/INT16/INT64 | 中英文 |
| `torch.clamp` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.floor_divide` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.log` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.mul`、`torch.sin` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.logical_not` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.div` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.cos`、`torch.reciprocal`、`torch.rsqrt` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.neg` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/INT8/INT32/INT64 | input=BF16/FP16/FP32/INT8/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.sigmoid` | 2.10.0、2.7.1、2.9.0 | input=FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |

## 文档收录版本与语言

| 函数/对象 | 中文收录版本 | 英文收录版本 |
| --- | --- | --- |
| `torch._foreach_abs`、`torch._foreach_abs_`、`torch._foreach_acos`、`torch._foreach_acos_`、`torch._foreach_asin_`、`torch._foreach_atan`、`torch._foreach_atan_`、`torch._foreach_ceil`、`torch._foreach_ceil_`、`torch._foreach_cos`、`torch._foreach_cos_`、`torch._foreach_cosh`、`torch._foreach_cosh_`、`torch._foreach_erf`、`torch._foreach_erf_`、`torch._foreach_erfc`、`torch._foreach_erfc_`、`torch._foreach_exp`、`torch._foreach_exp_`、`torch._foreach_expm1`、`torch._foreach_expm1_`、`torch._foreach_floor`、`torch._foreach_floor_`、`torch._foreach_frac`、`torch._foreach_frac_`、`torch._foreach_lgamma`、`torch._foreach_lgamma_`、`torch._foreach_log`、`torch._foreach_log10`、`torch._foreach_log10_`、`torch._foreach_log1p`、`torch._foreach_log1p_`、`torch._foreach_log2`、`torch._foreach_log2_`、`torch._foreach_log_`、`torch._foreach_neg`、`torch._foreach_reciprocal`、`torch._foreach_reciprocal_`、`torch._foreach_round`、`torch._foreach_round_`、`torch._foreach_sigmoid`、`torch._foreach_sigmoid_`、`torch._foreach_sin`、`torch._foreach_sin_`、`torch._foreach_sinh`、`torch._foreach_sinh_`、`torch._foreach_sqrt_`、`torch._foreach_tan`、`torch._foreach_tan_`、`torch._foreach_trunc`、`torch._foreach_trunc_`、`torch._foreach_zero_`、`torch.conj_physical`、`torch.frac`、`torch.frexp`、`torch.gcd`、`torch.hypot`、`torch.imag`、`torch.lcm`、`torch.lgamma`、`torch.nextafter`、`torch.renorm`、`torch.signbit` | 2.10.0、2.11.0、2.12.0、2.13.0、2.14.0、2.7.1、2.9.0 | 未收录 |
| `torch.fill_`、`torch.nan_to_num_`、`torch.rsub`、`torch.threshold` | 2.13.0、2.14.0 | 未收录 |

## 广播、移位和输出类型

addcmul在FP64、UINT8、INT8、INT64下不支持三个Tensor同时广播；addcdiv的input仅FP16/FP32，不从Tensor.addcdiv的更宽表补类型。bitwise_left_shift/right_shift仅在shiftBits小于self数据类型位宽时保证精度无误差，不据此为等于/超过位宽的行为设定结果。

log10的UINT8、INT8/16/32/64和BOOL输入要求out为FP32，其余支持类型out与input一致；这是特定out参数约束，不是所有log函数输出都应FP32。logaddexp/logaddexp2不支持double；logit的eps大于1输出NaN、等于1输出Inf；tan记录数值范围[-65504,65504]。

## CPU回退和950局部约束

acosh、copysign、trunc可能CPU回退，不能把Tensor.acos/nextafter_等方法的回退说明自动套给所有同名torch函数。950DT的_foreach_abs不支持complex，中文对应条目及英文Math导言均保留该限制；它不自动排除_foreach_abs_或其他foreach函数。

softmax在2.11至2.14的input表仅FP32、较早三版本列BF16/FP16/FP32/FP64，并说明支持Named Tensor。此局部说明不扩大[旧具名Tensor页](../../inference/guides/optimization/torch_npu/torch_npu_native_tensor_layout.md)的产品、类型或版本范围。支持表也不独自证明NaN/Inf、溢出与CPU参考结果完全相同，实际误差和回退开销需单独检查。

- [Tensor数学方法](torch_npu_native_tensor_math_scope.md)
- [矩阵、距离和信号运算](torch_npu_native_torch_matrix_signal_scope.md)

## 私有foreach清单的类型与双语产品差异

同提交private_apis说明未特别标注者按该页口径支持其全部PyTorch版本，不能把这句推广为当前主线包兼容任意历史/未来发行版或26.0发布组合。以下是原文“支持”的类型，没有指明每个参数名，不改成完整“仅支持”的范围或全部列表元素、标量参数的统一规则。

| 准确入口 | 来源列出的支持类型 |
| --- | --- |
| _foreach_maximum_ | BF16/FP16/FP32/FP64、UINT8、INT8/16/32/64 |
| _foreach_pow、_foreach_pow_ | BF16/FP16/FP32/INT32 |
| _foreach_tanh | BF16/FP16/FP32、UINT8、INT8/16/32/64、BOOL |
| _foreach_tanh_、_foreach_addcdiv、_foreach_norm、_foreach_lerp | BF16/FP16/FP32 |
| _foreach_div | BF16/FP16/FP32、UINT8、INT8/16/32/64、BOOL |
| _foreach_add | BF16/FP16/FP32/INT32/BOOL |

以上均为torch根命名空间。除_foreach_pow_和_foreach_tanh_中文列三产品、英文明确950不支持外，其他表列三产品。原地/非原地变体独立消费，不用pow或tanh支持替各自原地版补950；也不从本页出现更多foreach名字推导所有foreach家族都具备同一类型、融合或性能合同。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md)（primary）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md)（constraint）
