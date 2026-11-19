---
type: Guide
title: 一元与逐元素数学生成包装路线：dtype 提升、整数恒等守卫与版本分支
description: 汇总 g18 元素数学 121 个 gen_opapi 登记名的生成包装行为：struct_codegen 模板展开、逐族 dtype/size 公式（整型→Float、complex→实部、clamp 版本门控）、structured_inherit 委托、主线独有 integral_identity 守卫（round/trunc 整数恒等）与 round_/trunc_ 主线与发布两版本 派发差、angle 无 acl_op 回退边界。
tags:
- task.implementation
- topic.precision
- topic.compute.elementwise.math_function
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/model.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputDtype.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputDtype.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RoundKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RoundKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TruncKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TruncKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AcosKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PolarKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
created_at: "2026-11-12T17:35:29Z"
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 一元与逐元素数学生成包装路线：dtype 提升、整数恒等守卫与版本分支

## 固定来源与实际边界

本卡聚合 `op_v2_partition` zone1（g18_elementwise_math）中 121 个 **gen_opapi 登记名**的 op-plugin 包装层行为；lerp/rsub 8 名（cpu_scalar 生成标记族，标记实际见于其中 5 名）与 maximum.out/minimum.out 已由既有卡核对（见文末链接），手写包装 45 名另见[二元数学卡](torch_npu_native_binary_math_scalar_overload_routes.md)。OpPlugin 主线 `d84e9b1d`、发布 `dedc3167`，PyTorch 主线 `ac0e1564`、发布 `f3ecfe4a`。静态阅读：主线与发布两版本 的 `op_plugin_functions.yaml` 121 名条目逐名核对、`torchnpugen/struct/struct_codegen.py` 主线与发布两版本 全文、发布 `model.py` 全文、`KernelNpuOutputDtype.cpp` 主线与发布两版本 全文、`OpUtils.cpp`/`op_api_common.h`/`OpPreparation.cpp` 定向段、aclops Round/Trunc/Acos/Polar 定向段。未导入上游、执行算子或测试；平台未知，保持 draft 与空平台。

## 生成机制：yaml 条目如何变成包装代码

gen_opapi 名不在 `op_plugin/ops/opapi` 手写；包装体由 `torchnpugen/struct/struct_codegen.py` 的 `ACLNN_FUNCTIONS_DEFINITION` 模板在构建期展开（主线 43–58 模板体），**生成体不随仓提交**。模板顺序固定：`integral_identity_guard → DO_COMPATIBILITY → new_params → cpu_scalar_h2d → compute_names → define_size_or_dtype → check_or_apply_tensor → cpu_scalar_op → exec_cmd → infer_name → return`。三种 schema 形态：

| 形态 | 生成行为 | 源码依据 |
|---|---|---|
| functional（acos/cos/exp2/…） | `DO_COMPATIBILITY(aclnnX, acl_op::name(args))`；`auto output_size_N = <size 公式>; auto output_dtype_N = <dtype 公式>;`；`at::Tensor result = npu_preparation::apply_tensor_without_format(size, option.options().dtype(dtype));` 后单次 `EXEC_NPU_CMD(aclnnX, …, result)`，返回 | struct_codegen.py 394–427、416–427（APPLY_TENSOR 83–86） |
| out（acos.out/sign.out/…） | 同上 define；`npu_preparation::check_tensor({<输入张量>}, out, <dtype>, <size>)` 后单次 `EXEC_NPU_CMD(aclnnX, …, out)` | 同上 399–412（CHECK_TENSOR 89–91） |
| inplace 直发（acos_ 等 `exec: aclnnInplaceXxx`） | 不申请/不检查输出，直接 `EXEC_NPU_CMD(aclnnInplaceXxx, self)` | 同上 397（inplace 无 define/apply） |

`EXEC_NPU_CMD` 按运行时 TaskQueue 开关分派 V1/V2（op_api_common.h 485–493）；V1 先 `TORCH_CHECK(aclnnX 与 aclnnXGetWorkspaceSize 符号均存在, "... not in <lib>...", ErrCode::PTR)`，设备侧两段式执行内部未核对。`apply_tensor_without_format` 经 pytorch pin `OpPreparation.cpp` 401–417：非 PrivateUse1 设备强制改为 NPU、`NPUNativeFunctions::empty(..., Contiguous)`。`check_tensor`（同文件 167–207）顺序：`check_memory` 输入输出重叠检查 → TORCH_CHECK out 在 NPU（原文 "output with device … doesn't match the desired device NPU"）→ TORCH_CHECK out dtype==期望 dtype（原文 "expected dtype … but got dtype …"，**不自动转换**）→ 尺寸不匹配时：out 同时是输入（原地）则 TORCH_CHECK 报错，否则保留 legacy 行为 `resize_output_check+resize_`（146–160）。两 pytorch pin 该函数逐字等价（格式差）。

**dtype 公式若写在 yaml 的 `out:/result:` 块**（`dtype:` 字段），functional 用它申请结果、out 变体用它做 check 期望；`ResInfo.parse` 对「块中缺 dtype/size 的 out 变体」取缺省 `dtype=out、size=out`（model.py 63–92：结果名 `out` 再映射为 `out.sizes()/out.scalar_type()`），即**out 路按 out 自身 dtype/shape 校验、不强制提升**。发布版本 `cos` 条目把结果块键名误拼为 `resutl:`（主线 1835–1844 `result:`，发布 1776–1785）；`ResInfo.parse` 对 functional 用 `results.keys()` 作结果名，仅生成变量名变体，行为等价——不据此推断发布 cos 语义不同。

## 逐族 dtype 提升/尺寸公式

生成 functional 的输出 dtype 由 yaml 公式决定；下表为 121 名的完整分组（主线与发布两版本 公式相同者不另注）：

| 组 | 名单（同组行为一致） | functional 输出 dtype | 备注 |
|---|---|---|---|
| 三角/双曲 16 | acos、acosh、asin、asinh、atan、atanh、cos、cosh、sin、sinc、sinh、tan、exp2、log10、log1p、log2 | `isIntegralType(self, true) ? kFloat : self` | 整型（含 Bool）→Float；组内 `log_950`/`asin_950` 等设备侧卡另见文末 |
| expm1 | expm1 | `isFloatingType(self) ? self : kFloat` | 反向公式：整型提升 Float，但**非浮点非整型（如 Bool）也落 Float** |
| abs.out | abs.out | `abs_out_dtype(self)` | ComplexFloat/Double/Half→Float/Double/Half（KernelNpuOutputDtype.cpp 131–146）；abs functional 由 DVM 卡核对，不在此重复 |
| angle.out | angle.out（angle 经 structured_inherit 复用） | `angle_out_dtype(self)` | complex→Float/Double、整型→Float（同文件 24–33） |
| polar.out | polar.out（polar 复用） | `polar_out_dtype(abs, angle)` | result_type Float/Double/Half→对应 Complex*（同文件 35–48） |
| clamp 族 | clamp、clamp.Tensor、clamp_max(.Tensor)、clamp_min(.Tensor) | `is_gte_cann_version_820rc1() ? <result_type 提升公式> : typeMetaToScalarType(self.dtype())` | **运行时 CANN 版本门控**（OpUtils.cpp 468–472：`IsGteCANNVersion("8.2.RC1","CANN")` 静态缓存一次）；<8.2.RC1 时输出 dtype 保持 self；scalar 路用 `clamp_scalar_out_dtype`、Tensor 路用 `clamp_out_dtype`（后者先 TORCH_CHECK min/max 至少一个非空，KernelNpuOutputDtype.cpp 87–120）。size：Tensor 路三重广播 `clamp_npu_output_size`（KernelNpuOutputSize.cpp 1787+，min/max 都在时 self×min×max），clamp_max/min.Tensor 为 `broadcast_ops_npu_output_size(self, max/min)` |
| xlogy 族 | xlogy.Tensor、xlogy.Scalar_Other、xlogy.Scalar_Self | `isIntegralType(at::result_type(self, other), true) ? kFloat : result_type` | Tensor 路尺寸为广播；Scalar_Self 路尺寸取 other |
| pow 标量族 | pow.Scalar、pow.Tensor_Scalar_out | `at::result_type(self, exponent)` | pow.Scalar 尺寸取 exponent；pow.Tensor_Tensor/_Tensor_Scalar functional 已由 DVM 卡核对 |
| fmod.Scalar | fmod.Scalar | `at::native::result_type(self, other)` | 其余 fmod 过载是手写卡范围 |
| isfinite | isfinite | `at::kBool` | 尺寸 self；Bool 输出 |
| bitwise_not.out、ceil.out、floor、frac.out、neg.out、round.out、sign.out、trunc 等显式 `dtype: self` 组 8 | bitwise_not.out、ceil.out、floor、frac.out、neg.out、round.out、sign.out、bitwise_not(functional 复用) | 输出=输入 dtype | 整型输入保持整型（floor/ceil/frac/trunc/sign 等不做 Float 提升） |
| `dtype: out` 组 9 | acosh.out、sin.out、sinc.out、sinh.out、sqrt.out、tan.out、xlogy.OutTensor、xlogy.OutScalar_Other、xlogy.OutScalar_Self | out 自身 dtype | 即 out 变体不强制提升 |
| 其余 out/`无 dtype` 70 名（组内含 18 名 structured_inherit 委托） | acos.out、acos_、acosh_、…（见「登记面」小节全清单） | out 自身 dtype / 原地直发 | ResInfo 缺省 `dtype=out` |

acl_op 回退命令名（DO_COMPATIBILITY 缺符号时）：unary 数学 aclops 是 ACE `OpCommand "Acos"/"Add"/…` + `CheckOut/check_match/format_contiguous/format_fresh_view` 模式（AcosKernelNpu.cpp 19–52 全文已读为代表）；**polar 的 aclops 回退是 CPU 往返**（PolarKernelNpu.cpp：`TORCH_WARN_ONCE("Warning: kernel [polar] is not supported by NPU currently. Now this kernel is running on CPU.")` 后 `.cpu()`/`at::polar`/`copy_`，发布同构）——主线 aclnnPolar 缺符号时 functional/out 均走 CPU。DO_COMPATIBILITY 本体是静态双符号探测 + Aclnn-only 抬错或 ASCEND_LOGW 后整函数 return 回退（op_api_common.h 95–119，与[logsumexp 卡](torch_npu_logsumexp_logaddexp_gcd_routes.md)已核对描述一致）。

## structured_inherit 委托（18 名）

`structured_inherit` 在**非原地**名上表示复用被指向名的 gen_opapi 配置（model.py 181–185：取 `struct_map[目标].gen_opapi` 展开为 functional 包装），**原地**名上生成纯委托（struct_codegen.py 311–324：`return op_api::<目标out>(args, self)`）。两类共 18 名：

| 名 | 继承目标 | 生成语义 |
|---|---|---|
| abs_、bitwise_not_、ceil、clamp_、clamp_min_、frac、neg_、round、round_、sign、sign_、trunc、trunc_（13 名） | 各自 `.out` | 原地→委托 `op_api::<base>_out(self, …, self)`（cpp 名即 `<base>_out` 重载，以 self 作 out 实参）；ceil/frac/sign/round/trunc functional 名经 `.out` 配置申请（dtype=self） |
| angle | angle.out | functional 复用 angle.out 配置（dtype=angle_out_dtype，exec aclnnAngleV2） |
| bitwise_not、round、trunc（functional，与上行并集计） | bitwise_not.out / round.out / trunc.out | functional 复用 out 配置（dtype=self、尺寸 self） |
| clamp_.Tensor | clamp.Tensor_out | 委托 `op_api::clamp_out(self, min, max, self)`（Tensor min/max 重载） |
| xlogy_.Tensor | xlogy.OutTensor | 委托 `op_api::xlogy_out(self, other, self)`（Tensor other 重载） |

注意 round_/trunc_ 的**主线与发布两版本 派发差**：主线 `structured_inherit: round.out/trunc.out`（委托 out 包装，含主线 integral guard）；发布改为直发 `exec: aclnnInplaceRound/aclnnInplaceTrunc`（发布 yaml 4295–4300/5050–5055，无 guard、无检查）。同族 `round`/`trunc` functional 主线与发布两版本 一致走 structured_inherit。另 clamp_max_ 是**直发** `exec: aclnnInplaceClampMax`（非委托），clamp_max_.Tensor/clamp_min_.Tensor 直发 aclnnInplaceClampMaxTensor/aclnnInplaceClampMinTensor，fmod_.Scalar 直发 aclnnInplaceFmodScalar（手写卡只覆盖 fmod 的 Tensor 过载）。

## 主线独有 integral_identity 守卫：round.out / trunc.out

主线 yaml 在 round.out（4403–4413）、trunc.out（5206–5216）多出 `integral_identity_tensor: self`，生成模板最前的守卫（struct_codegen.py 75–80、338–344）：

```text
if (at::isIntegralType(self.scalar_type(), /*includeBool=*/false)) {
    return acl_op::round_out(self, out);   // trunc 同构
}
```

即整型（不含 Bool）输入绕过 aclnnRound/aclnnTrunc 直落 aclops；主线 aclops `round_out`/`trunc_out` 实现**整数恒等**（RoundKernelNpu.cpp 22–53：`round_integral_identity` 命中时 `out.copy_(self)`，源码注释明示 "round on integer tensors is identity. CANN aclnn round ops do not support int8 / int16 / uint8"；TruncKernelNpu.cpp 29–34 同构）。**发布版本 两侧都无该行为**：发布 yaml 无 integral_identity_tensor，发布 aclops Round/Trunc 亦无恒等分支（整型输入发布走 ACE "Round"/"Trunc" 命令）。这是主线对齐 PyTorch 整数恒等语义的修复、发布缺失的版本差；主线与发布两版本 发布差均为静态阅读，未数值验证。

主线 `integral_identity_guard` 模板段与 cpu_scalar 生成特性（lerp/rsub 已核对）同为主线独有；发布 struct_codegen.py 296 行无该模板。

## 登记面（121 名全清单）

按 exec 命令聚合（主线与发布两版本 除已注明差异外逐字相同；`*.out` 除注明外 check 期望=out 自身 dtype）：

| exec 命令 | 名 |
|---|---|
| aclnnAbs | abs.out（dtype=abs_out_dtype）、abs_（委托 abs.out） |
| aclnnAcos | acos、acos.out、acos_ |
| aclnnAcosh | acosh、acosh.out（dtype=out）、acosh_ |
| aclnnAngleV2 | angle、angle.out（dtype=angle_out_dtype；**无 acl_op 登记**，缺符号时 EXEC_NPU_CMD 抬 ErrCode::PTR、无回退） |
| aclnnAsin / aclnnInplaceAsin | asin、asin.out、asin_ |
| aclnnAsinh | asinh、asinh.out、asinh_ |
| aclnnAtan | atan、atan.out、atan_ |
| aclnnAtanh | atanh、atanh.out、atanh_ |
| aclnnBitwiseNot | bitwise_not、bitwise_not.out（dtype=self）、bitwise_not_（均委托/复用 out 配置） |
| aclnnCeil | ceil、ceil.out、ceil_（dtype=self 组） |
| aclnnClamp | clamp、clamp.out、clamp_（8.2.RC1 门控 dtype；clamp_ 委托 clamp.out） |
| aclnnClampTensor | clamp.Tensor、clamp.Tensor_out、clamp_.Tensor（后者委托 clamp.Tensor_out） |
| aclnnClampMax | clamp_max、clamp_max.out、clamp_max_（直发 aclnnInplaceClampMax） |
| aclnnClampMaxTensor | clamp_max.Tensor、clamp_max.Tensor_out、clamp_max_.Tensor（直发 aclnnInplaceClampMaxTensor） |
| aclnnClampMin / aclnnClampMinTensor | clamp_min、clamp_min.out、clamp_min_（委托 clamp_min.out）；clamp_min.Tensor、clamp_min.Tensor_out、clamp_min_.Tensor（直发 aclnnInplaceClampMinTensor） |
| aclnnCos | cos（主线 result 块 / 发布 resutl 拼写差，行为等价）、cos.out、cos_ |
| aclnnCosh | cosh、cosh.out、cosh_ |
| aclnnExp | exp.out、exp_（exp functional 已由 DVM 卡核对） |
| aclnnExp2 | exp2、exp2.out、exp2_ |
| aclnnExpm1 | expm1、expm1.out、expm1_ |
| aclnnFloor | floor、floor.out、floor_ |
| aclnnFmodScalar | fmod.Scalar、fmod.Scalar_out；fmod_.Scalar 直发 aclnnInplaceFmodScalar（其余 fmod Tensor 过载在手写卡） |
| aclnnFrac | frac、frac.out、frac_ |
| aclnnIsFinite | isfinite（dtype=kBool） |
| aclnnLog1p | log1p、log1p.out、log1p_ |
| aclnnLog2 | log2、log2.out、log2_ |
| aclnnLog10 | log10、log10.out、log10_ |
| aclnnNeg | neg.out、neg_（neg functional DVM 卡核对） |
| aclnnPolar | polar、polar.out（dtype=polar_out_dtype；aclops 回退 CPU 往返） |
| aclnnPowScalarTensor | pow.Scalar、pow.Scalar_out（尺寸=exponent） |
| aclnnPowTensorScalar | pow.Tensor_Scalar_out |
| aclnnReciprocal | reciprocal.out、reciprocal_（reciprocal functional DVM 卡核对） |
| aclnnRound | round、round.out（主线 integral guard）、round_（主线委托/发布 aclnnInplaceRound） |
| aclnnRsqrt | rsqrt、rsqrt.out、rsqrt_ |
| aclnnSign | sign、sign.out（dtype=self）、sign_（均经 sign.out 配置/委托）；sgn/sgn.out 手写卡核对 |
| aclnnSin / aclnnSinc / aclnnSinh / aclnnSqrt | sin、sin.out、sin_；sinc、sinc.out、sinc_；sinh、sinh.out、sinh_；sqrt.out、sqrt_（sqrt functional DVM 卡核对） |
| aclnnTan | tan、tan.out、tan_ |
| aclnnTrunc | trunc、trunc.out（主线 integral guard）、trunc_（主线委托/发布 aclnnInplaceTrunc） |
| aclnnXLogYTensor | xlogy.Tensor、xlogy.OutTensor、xlogy_.Tensor（委托 OutTensor） |
| aclnnXLogYScalarOther | xlogy.Scalar_Other、xlogy.OutScalar_Other、xlogy_.Scalar_Other（直发 aclnnInplaceXLogYScalarOther） |
| aclnnXLogYScalarSelf | xlogy.Scalar_Self（显式全参数 exec）、xlogy.OutScalar_Self |
| mul.out | 见手写卡 |

## 优化与验收边界

- 迁移/性能定位先确认实际派发：`angle`/`angle.out` 无 acl_op 回退（CANN 无 aclnnAngleV2 时直接抬错）；`polar`/`polar.out` 回退是 CPU 往返（WARN_ONCE 提示）；clamp 族 dtype 随 CANN ≥8.2.RC1 改变，混合版本部署的精度回归点。
- 整型输入的 round/trunc：主线按 PyTorch 恒等语义走 copy；发布走 ACE Round/Trunc——跨版本数值一致性验证时必须按 pin 分别核对。
- 本卡静态口径，未运行任何分发/导入/数值验证；不把任一路径写成推荐配置。

## Evidence

- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（primary）：121 名条目逐名行段（787–827 acos 族、1103–1115 angle、1471–1492 bitwise_not、1640–1737 clamp 族、1835–1856 cos、2122–2132 exp 族、2806–2814 isfinite、2340–2356 fmod、3959–3994 pow、4016–4022 polar、4403–4419 round 族、5200–5222 trunc 族、5458–5523 xlogy 族等）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（primary）：同 121 名发布侧行段（761–801、1065–1077、1447–1468、1572–1669、1776–1797、…、4271–4294、4295–4300 round_、5034–5055 trunc 族、5320–5385 xlogy 族；cos 1776–1785 resutl 拼写按原文记录）。
- [struct_codegen.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py)（implementation）：43–503 全文（模板 43–115、integral guard 75–80/338–344、cpu_scalar 189–257、展开 295–476、分片 479–503）。
- [struct_codegen.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py)（implementation）：296 行全文；无 integral guard/cpu_scalar 模板段。
- [model.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/model.py)（implementation）：1–249 全文（ResInfo.parse 46–99、structured_inherit 168–185、缺省 dtype/size 63–92）。
- [KernelNpuOutputDtype.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputDtype.cpp)（implementation）：1–146 全文；发布侧同文件全文（主线与发布两版本 逐 helper 语义等价，发布多 npu_moe_distribute_dispatch_setup_out_dtype、格式差）。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：119–129（broadcast→at::infer_size）、1787–1799（clamp_npu_output_size）。
- [OpUtils.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）：主线 468–473、发布 424–429（is_gte_cann_version_820rc1）。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：95–119（DO_COMPATIBILITY）、485–515（EXEC_NPU_CMD/V1 符号抬错）。
- [RoundKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RoundKernelNpu.cpp)（implementation）：16–79 全文（round_integral_identity/copy 路径）；[发布版](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RoundKernelNpu.cpp)全文（无恒等分支）。
- [TruncKernelNpu.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TruncKernelNpu.cpp)（implementation）：两版全文（主线 28–34 trunc_integral_identity、发布无）。
- [AcosKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AcosKernelNpu.cpp)（implementation）：19–52（uninary aclops 回退代表模式；主线文件共 52 行）。
- [PolarKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PolarKernelNpu.cpp)（implementation）：polar/polar_out CPU 往返段。
- [OpPreparation.cpp 主线与发布两版本](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）：主线 122–220（IsCPUScalar/is_scalar_wrapped/check_tensor 族）、390–417（apply_tensor_without_format）；发布 128、517–523 定向段。

## 关联

- [lerp/rsub cpu_scalar 生成分支（已核对）](torch_npu_dynamic_selection_sync_and_where_scalar_execution.md)
- [maximum.out/minimum.out（已核对）](../apis/torch_npu/legacy_min_max_and_sort.md)
- [二元数学手写包装 45 名](torch_npu_native_binary_math_scalar_overload_routes.md)
- [logsumexp/logaddexp/gcd 归约族](torch_npu_logsumexp_logaddexp_gcd_routes.md)（DO_COMPATIBILITY 机制同源）
- 设备侧不同层：[asin_950](../../../ops/ascendc/operators/aclnn/math/math/asin_950.md)、[atan2_950](../../../ops/ascendc/operators/aclnn/math/math/atan2_950.md)、[bitwise_not_950](../../../ops/ascendc/operators/aclnn/math/math/bitwise_not_950.md)、[ceil_950](../../../ops/ascendc/operators/aclnn/math/math/ceil_950.md)、[div_950](../../../ops/ascendc/operators/aclnn/math/math/div_950.md)、[exp_950（Direct 层参考）](../../../ops/ascendc/operators/direct/math/math/exp_950.md)、[expm1_950](../../../ops/ascendc/operators/aclnn/math/math/expm1_950.md)、[inplace_exp2_950](../../../ops/ascendc/operators/aclnn/math/math/inplace_exp2_950.md)、[log_950](../../../ops/ascendc/operators/aclnn/math/math/log_950.md)、[log2_950](../../../ops/ascendc/operators/aclnn/math/math/log2_950.md)、[inplace_log10_950](../../../ops/ascendc/operators/aclnn/math/math/inplace_log10_950.md)、[nan_to_num_950](../../../ops/ascendc/operators/aclnn/math/math/nan_to_num_950.md)、[polar_950](../../../ops/ascendc/operators/aclnn/math/math/polar_950.md)、[pow_tensor_tensor_950](../../../ops/ascendc/operators/aclnn/math/math/pow_tensor_tensor_950.md)、[angle_v2](../../../ops/ascendc/operators/aclnn/math/math/angle_v2.md)、[clamp_min_950](../../../ops/ascendc/operators/aclnn/math/conversion/clamp_min_950.md)、[inplace_clamp_max_950](../../../ops/ascendc/operators/aclnn/math/conversion/inplace_clamp_max_950.md)
