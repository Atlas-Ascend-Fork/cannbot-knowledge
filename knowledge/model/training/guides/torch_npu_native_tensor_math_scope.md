---
type: Guide
title: Tensor数学方法：dtype、950精度与CPU回退
description: 按Tensor方法与原地变体分别记录运算类型、矩阵乘版本差异和可能回退CPU的入口。
tags:
- task.optimization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Tensor.md
  role: constraint
created_at: '2026-11-09T13:59:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# Tensor数学方法：dtype、950精度与CPU回退

## 固定版本与表的读法

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的2.7.1、2.9至2.14中英文Tensor支持页，以下默认展示2.14，较早版本的不同表另列。所列三产品指A2/A3训练系列与950DT，不包含950PR，不回推26.0/PyTorch2.8发布基线。

类型表只描述该方法的self，既不是返回值类型，也不是整个模型应转换成的类型。原文未给独立类型表、语言缺项或版本未收录均不等于已证实不支持；明确的产品排除和方法特有限制另列，优先于概括。FP16/FP32/FP64分别对应fp16/fp32/fp64；保留原文DOUBLE名称，不代填转换规则。本卡仅静态核对，未运行上游、编译或进行设备实验。

## 产品和原地方法分别核对

本表已收录数学方法的产品表列三产品。acos_/arccos_基础self表为FP16/FP32/FP64，另有A3支持BF16的说明，不扩到A2或950。addcdiv_/addcmul_类型表明确A2/A3范围；英文另给未进一步映射的“Atlas训练系列产品”不含BF16的表，不能把两者取并集或替950补dtype。

方法别名和原地变体也有不同表，例如abs_与absolute_、div与div_、neg与neg_，必须按准确方法名查询，不能由名称相近直接互换。中文额外收录的一组方法只有产品表，不借torch.*同名函数补参数或dtype。
## 方法级self类型

| 方法/属性 | self类型范围 | 来源 |
| --- | --- | --- |
| `torch.Tensor.erfinv_`、`torch.Tensor.logit`、`torch.Tensor.logit_`、`torch.Tensor.matmul` | BF16/FP16/FP32 | 中英文 |
| `torch.Tensor.cos_`、`torch.Tensor.exp_`、`torch.Tensor.log_`、`torch.Tensor.sin_` | BF16/FP16/FP32/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.div_`、`torch.Tensor.norm` | BF16/FP16/FP32/FP64 | 中英文 |
| `torch.Tensor.addcdiv_` | A2/A3：BF16/FP16/FP32/FP64 | 中英文 |
| `torch.Tensor.acosh_`、`torch.Tensor.arccosh_`、`torch.Tensor.cosh_`、`torch.Tensor.log10_`、`torch.Tensor.sigmoid_`、`torch.Tensor.sqrt_` | BF16/FP16/FP32/FP64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.pow` | BF16/FP16/FP32/FP64/INT16/INT64 | 中英文 |
| `torch.Tensor.pow_` | BF16/FP16/FP32/FP64/INT64 | 中英文 |
| `torch.Tensor.clip`、`torch.Tensor.floor`、`torch.Tensor.floor_`、`torch.Tensor.sub`、`torch.Tensor.tanh` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.abs`、`torch.Tensor.absolute`、`torch.Tensor.equal` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.acosh`、`torch.Tensor.arccosh`、`torch.Tensor.cos`、`torch.Tensor.cosh`、`torch.Tensor.isinf`、`torch.Tensor.isnan`、`torch.Tensor.log10`、`torch.Tensor.log2`、`torch.Tensor.square`、`torch.Tensor.tan` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.sub_` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.addcmul_` | A2/A3：BF16/FP16/FP32/FP64/UINT8/INT8/INT32/INT64 | 中英文 |
| `torch.Tensor.sign` | BF16/FP16/FP32/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.addcdiv` | BF16/FP16/FP32/INT64 | 中英文 |
| `torch.Tensor.exp`、`torch.Tensor.log` | BF16/FP16/FP32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.neg_` | BF16/FP16/FP32/INT8/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.abs_`、`torch.Tensor.clamp` | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.add`、`torch.Tensor.add_`、`torch.Tensor.copysign`、`torch.Tensor.div`、`torch.Tensor.divide`、`torch.Tensor.ge`、`torch.Tensor.greater`、`torch.Tensor.gt`、`torch.Tensor.gt_`、`torch.Tensor.isfinite`、`torch.Tensor.le`、`torch.Tensor.less`、`torch.Tensor.lt`、`torch.Tensor.mul_`、`torch.Tensor.tril`、`torch.Tensor.tril_`、`torch.Tensor.triu`、`torch.Tensor.triu_` | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.eq`、`torch.Tensor.logical_and`、`torch.Tensor.logical_and_`、`torch.Tensor.logical_or`、`torch.Tensor.mul`、`torch.Tensor.multiply`、`torch.Tensor.ne`、`torch.Tensor.not_equal`、`torch.Tensor.reciprocal`、`torch.Tensor.sin` | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.float_power_` | DOUBLE | 中英文 |
| `torch.Tensor.addbmm`、`torch.Tensor.addbmm_`、`torch.Tensor.addmm`、`torch.Tensor.addmm_`、`torch.Tensor.arcsin_`、`torch.Tensor.arctan2_`、`torch.Tensor.arctan_`、`torch.Tensor.asin_`、`torch.Tensor.atan2_`、`torch.Tensor.atan_`、`torch.Tensor.baddbmm`、`torch.Tensor.baddbmm_`、`torch.Tensor.bmm`、`torch.Tensor.ceil`、`torch.Tensor.ceil_`、`torch.Tensor.divide_`、`torch.Tensor.dot`、`torch.Tensor.erf_`、`torch.Tensor.erfc_`、`torch.Tensor.expm1_`、`torch.Tensor.fix`、`torch.Tensor.fix_`、`torch.Tensor.frac`、`torch.Tensor.frac_`、`torch.Tensor.hardshrink`、`torch.Tensor.inner`、`torch.Tensor.lerp`、`torch.Tensor.lerp_`、`torch.Tensor.log1p_`、`torch.Tensor.logaddexp2`、`torch.Tensor.matrix_power`、`torch.Tensor.mm`、`torch.Tensor.round`、`torch.Tensor.round_`、`torch.Tensor.tanh_`、`torch.Tensor.true_divide_`、`torch.Tensor.trunc`、`torch.Tensor.trunc_`、`torch.Tensor.xlogy`、`torch.Tensor.xlogy_` | FP16/FP32 | 中英文 |
| `torch.Tensor.arcsinh_`、`torch.Tensor.arctanh_`、`torch.Tensor.asinh_`、`torch.Tensor.atanh_`、`torch.Tensor.ldexp_`、`torch.Tensor.log2_`、`torch.Tensor.reciprocal_`、`torch.Tensor.rsqrt_`、`torch.Tensor.tan_` | FP16/FP32/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.acos_`、`torch.Tensor.arccos_`、`torch.Tensor.sinh`、`torch.Tensor.sinh_`、`torch.Tensor.softmax` | FP16/FP32/FP64 | 中英文 |
| `torch.Tensor.sgn_` | FP16/FP32/FP64/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.less_equal`、`torch.Tensor.outer`、`torch.Tensor.sqrt` | FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.cov` | FP16/FP32/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.logaddexp` | FP16/FP32/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.remainder`、`torch.Tensor.remainder_` | FP16/FP32/INT32/INT64 | 中英文 |
| `torch.Tensor.sign_` | FP16/FP32/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.sgn` | FP16/FP32/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.addcmul` | FP16/FP32/INT64 | 中英文 |
| `torch.Tensor.erf`、`torch.Tensor.erfc`、`torch.Tensor.expm1` | FP16/FP32/INT64/BOOL | 中英文 |
| `torch.Tensor.neg`、`torch.Tensor.negative`、`torch.Tensor.negative_` | FP16/FP32/INT8/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.isclose` | FP16/FP32/UINT8/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.absolute_`、`torch.Tensor.addmv`、`torch.Tensor.addmv_`、`torch.Tensor.clip_`、`torch.Tensor.floor_divide`、`torch.Tensor.floor_divide_`、`torch.Tensor.subtract_` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.acos`、`torch.Tensor.addr`、`torch.Tensor.addr_`、`torch.Tensor.allclose`、`torch.Tensor.arccos`、`torch.Tensor.arcsin`、`torch.Tensor.arctan`、`torch.Tensor.arctan2`、`torch.Tensor.asin`、`torch.Tensor.atan`、`torch.Tensor.atan2`、`torch.Tensor.deg2rad`、`torch.Tensor.erfinv`、`torch.Tensor.ge_`、`torch.Tensor.greater_`、`torch.Tensor.greater_equal`、`torch.Tensor.greater_equal_`、`torch.Tensor.isneginf`、`torch.Tensor.isposinf`、`torch.Tensor.le_`、`torch.Tensor.less_`、`torch.Tensor.less_equal_`、`torch.Tensor.log1p`、`torch.Tensor.logical_not`、`torch.Tensor.logical_not_`、`torch.Tensor.lt_`、`torch.Tensor.rad2deg`、`torch.Tensor.true_divide` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.float_power` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX128 | 中英文 |
| `torch.Tensor.angle` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64 | 中英文 |
| `torch.Tensor.arcsinh`、`torch.Tensor.arctanh`、`torch.Tensor.asinh`、`torch.Tensor.atanh`、`torch.Tensor.eq_`、`torch.Tensor.isreal`、`torch.Tensor.ldexp`、`torch.Tensor.logical_or_`、`torch.Tensor.logical_xor`、`torch.Tensor.logical_xor_`、`torch.Tensor.multiply_`、`torch.Tensor.ne_`、`torch.Tensor.not_equal_`、`torch.Tensor.rsqrt` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.cross`、`torch.Tensor.positive`、`torch.Tensor.square_` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.fmod`、`torch.Tensor.fmod_` | FP16/FP32/UINT8/INT8/INT32/INT64 | 中英文 |
| `torch.Tensor.slogdet` | FP32/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.bitwise_and`、`torch.Tensor.bitwise_and_`、`torch.Tensor.bitwise_not`、`torch.Tensor.bitwise_not_`、`torch.Tensor.bitwise_or`、`torch.Tensor.bitwise_or_`、`torch.Tensor.bitwise_xor`、`torch.Tensor.bitwise_xor_` | UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.apply_`、`torch.Tensor.clamp_`、`torch.Tensor.dist`、`torch.Tensor.ger`、`torch.Tensor.heaviside`、`torch.Tensor.map_`、`torch.Tensor.nan_to_num`、`torch.Tensor.nan_to_num_`、`torch.Tensor.nextafter_` | 未给独立self类型表 | 中英文 |
| `torch.Tensor.bitwise_left_shift`、`torch.Tensor.bitwise_left_shift_`、`torch.Tensor.bitwise_right_shift`、`torch.Tensor.bitwise_right_shift_`、`torch.Tensor.cholesky_inverse`、`torch.Tensor.cholesky_solve`、`torch.Tensor.conj_physical`、`torch.Tensor.conj_physical_`、`torch.Tensor.copysign_`、`torch.Tensor.corrcoef`、`torch.Tensor.det`、`torch.Tensor.digamma`、`torch.Tensor.digamma_`、`torch.Tensor.fmax`、`torch.Tensor.fmin`、`torch.Tensor.frexp`、`torch.Tensor.gcd`、`torch.Tensor.gcd_`、`torch.Tensor.geqrf`、`torch.Tensor.hypot`、`torch.Tensor.hypot_`、`torch.Tensor.i0`、`torch.Tensor.i0_`、`torch.Tensor.igamma`、`torch.Tensor.igamma_`、`torch.Tensor.igammac`、`torch.Tensor.igammac_`、`torch.Tensor.inverse`、`torch.Tensor.lcm`、`torch.Tensor.lcm_`、`torch.Tensor.lgamma`、`torch.Tensor.lgamma_`、`torch.Tensor.logdet`、`torch.Tensor.matrix_exp`、`torch.Tensor.mv`、`torch.Tensor.mvlgamma`、`torch.Tensor.mvlgamma_`、`torch.Tensor.nextafter`、`torch.Tensor.orgqr`、`torch.Tensor.ormqr`、`torch.Tensor.pinverse`、`torch.Tensor.polygamma`、`torch.Tensor.polygamma_`、`torch.Tensor.renorm`、`torch.Tensor.renorm_`、`torch.Tensor.sigmoid`、`torch.Tensor.signbit`、`torch.Tensor.sinc`、`torch.Tensor.sinc_`、`torch.Tensor.stft`、`torch.Tensor.trace`、`torch.Tensor.vdot` | 未给独立self类型表 | 仅中文 |

## 较早版本的不同类型表

| 方法 | 文档版本 | 当时self表 | 2.14 self表 | 来源 |
| --- | --- | --- | --- | --- |
| `torch.Tensor.addmm`、`torch.Tensor.bmm`、`torch.Tensor.mm` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32 | FP16/FP32 | 中英文 |
| `torch.Tensor.remainder` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/INT32/INT64 | FP16/FP32/INT32/INT64 | 中英文 |
| `torch.Tensor.sign` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/INT32/INT64/BOOL | BF16/FP16/FP32/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.exp` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/INT64/BOOL | BF16/FP16/FP32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.pow` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | BF16/FP16/FP32/FP64/INT16/INT64 | 中英文 |
| `torch.Tensor.clamp` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.log` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | BF16/FP16/FP32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.add`、`torch.Tensor.ge`、`torch.Tensor.gt`、`torch.Tensor.le`、`torch.Tensor.lt`、`torch.Tensor.tril`、`torch.Tensor.triu` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.sin` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.sqrt` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.logical_not` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.div` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.eq`、`torch.Tensor.logical_and_`、`torch.Tensor.mul`、`torch.Tensor.ne`、`torch.Tensor.reciprocal` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.rsqrt` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.sigmoid` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 未给独立self类型表 | zh |
| `torch.Tensor.neg` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/INT8/INT32/INT64 | FP16/FP32/INT8/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.addcdiv_` | 2.9.0 | 未给独立self类型表 | BF16/FP16/FP32/FP64 | en |
| `torch.Tensor.addcmul_` | 2.9.0 | 未给独立self类型表 | BF16/FP16/FP32/FP64/UINT8/INT8/INT32/INT64 | en |

英文sigmoid只在2.7.1/2.9/2.10收录，其self表与中文这些版本一致；中文其余四版本仍收录但无独立self表，英文缺项不直接证明删除。英文2.9的addcdiv_/addcmul_未给独立self表，也不反推后来各版本范围。

## 广播、形状和数值条件

addcdiv.self为BF16/FP16/FP32/INT64，addcmul.self为FP16/FP32/INT64；两者INT64时不支持三个Tensor同时广播。addcdiv_/addcmul_也保留INT64广播限制，即使addcdiv_的局部类型表未列INT64，不能据这句话反填INT64支持。cross要求输入shape一致。logit/logit_的eps大于1时结果为NaN、等于1时为Inf。tan记录输入值范围[-65504,65504]，不擅自为复数定义新的区间判断。

950DT下dist排除BOOL、UINT8、原文“int”、FP64、COMPLEX64/128；不能把未细分的int自行展开成完整整数矩阵。norm/tanh的950说明排除FP64，nan_to_num排除FP64和COMPLEX64/128，这些局部说明不自动套到各自的原地变体。

## 矩阵乘的版本与950精度

addmm/bmm/mm在2.11至2.14的self表为FP16/FP32，2.7.1/2.9/2.10另列BF16。950DT对这三个方法的FP32/complex64描述默认高性能模式下精度可能与GPU及A2/A3不同；英文导言还对Tensor.__matmul__作同样提示。设置cube_math_type为4可以选择高精度但影响性能，具体上下文与枚举使用见[CubeMathType与HF32](torch_npu_native_convolution_constraints.md)。说明出现complex64不等于上述self表已允许该类型，不替来源消除这一范围差异，也不把整数4当作所有版本和入口通用配置。

## CPU路径单独影响性能预期

apply_/map_仅支持CPU；nextafter_明确通过CPU回退实现。acos、atan2_、clamp_、copysign、acosh、heaviside、logical_xor、not_equal、neg_说明可能触发CPU回退。没有回退说明的其他条目不因此获得“纯NPU执行”或更快的保证。

评估时分别记录准确方法名、原地与否、self dtype、版本语言、产品、数值模式与CPU/NPU实际执行路径；支持清单不能替代结果误差、搬运与同步开销测量。

- [Tensor索引、排序和归约](torch_npu_native_tensor_index_reduce_scope.md)
- [Tensor类型与设备转换](../../inference/guides/optimization/torch_npu/torch_npu_native_tensor_conversion_scope.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Tensor.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）
