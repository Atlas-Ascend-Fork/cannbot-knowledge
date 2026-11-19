---
type: Guide
title: 二元与杂项数学手写包装：标量过载分支、div 舍入模式及主线与发布两版本差异
description: 汇总 g18 元素数学 45 个手写 opapi 登记名的包装行为：add/sub/mul 的 CPU 标量过载与 AddV3 运行时探测、div 六过载的 floor/trunc 模式映射与整型提升不对称、fmod 的 950 标量折叠、remainder 主线独有标量分支、log 的 dtype 协商、addcdiv/addcmul canCast 检查、atan2 主线与发布两版本 H2D 差异、complex 的 CPU 回退、nan_to_num 默认值表、pow/round.decimals/sgn 边界。并含npu_stride_add 内核合同与 ldexp_stub 覆盖。
tags:
- task.implementation
- topic.precision
- topic.compute.elementwise.arithmetic
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SubKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SubKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MulKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MulKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DivKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DivKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FmodKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FmodKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RemainderKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RemainderKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddcdivKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddcdivKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddcmulKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddcmulKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/Atan2KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/Atan2KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ComplexKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ComplexKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NanToNumKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NanToNumKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PowKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/PowKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RoundDecimalsKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RoundDecimalsKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SignKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SignKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SubKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DivKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FmodKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RemainderKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddcdivKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddcmulKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Atan2KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/NanToNumKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PowKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MulKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SignKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ComplexKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/StrideAddKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/StrideAddKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LdexpKernelNpuOpApi.cpp
  role: implementation
created_at: '2026-11-12T17:35:29Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 二元与杂项数学手写包装：标量过载分支、div 舍入模式与主线与发布两版本 差异

## 固定来源与实际边界

本卡聚合 `op_v2_partition` zone1（g18_elementwise_math）中 **45 个手写 opapi 名**（add/div/fmod/remainder/log/atan2/complex/nan_to_num/pow.Tensor_Tensor_out/round.decimals/sgn/addcdiv/addcmul/sub/mul.out 家族；生成路 121 名见[生成路线卡](torch_npu_native_elementwise_math_gen_routes.md)；lerp/rsub/maximum.out/minimum.out 已核对）。OpPlugin 主线 `d84e9b1d`、发布 `dedc3167`。静态阅读：15 个 opapi 手写文件主线与发布两版本 全文（发布侧逐文件 token 级对比：sub/fmod/log/addcdiv/addcmul/complex/nan_to_num/pow/round.decimals/sign 逻辑相同，add/mul/remainder/atan2 有真实语义差，div 字节相同）；aclops 回退侧 15 文件主线定向已读（add/sub/mul/div/fmod/remainder/log/nan_to_num/pow 全文或主函数段，addcdiv/addcmul/atan2/round.decimals/sign/complex 命令段）。未导入上游、执行算子或测试；平台未知，保持 draft 与空平台。

CPU 标量谓词：手写文件混用 `npu_preparation::IsCPUScalar`（主线）与 `dim()==0 && !is_npu`（主线与发布两版本 等价，pytorch pin OpPreparation.cpp 122–125/517–523）。

## add 家族（add.out、add_.Scalar）

`add_out`（46–74 行分支树）按 other/self 是否 CPU 0 维张量选命令：other 标量→`EXEC_NPU_CMD(aclnnAdds, self, other.item(), alpha, result)`；否则 self 标量→**运行时探测** `check_aclnn_kernel_available("aclnnAddV3")`（op_api_common.cpp 767–775：dlsym 查 aclnnAddV3 与其 GetWorkspaceSize 双符号，静态缓存一次）成立且 dtype 允许→`aclnnAddV3(selfs, other, alpha, result)`（**self 是标量、other 是张量**的镜像命令），否则 `self_tensor_to_device` H2D 复制后 `aclnnAdd(self_cp, other, alpha, result)`；双张量→`aclnnAdd`。**主线与发布两版本 差**：主线 60 行守卫 `self.dtype() != kBool && self.dtype() != kLong`，发布仅排除 Bool——发布在 Long CPU 标量 self 时也走 AddV3。`add(Tensor,Tensor,Scalar)` functional 同分支树 + `alpha_check_npu`（布尔 alpha 仅允许 Bool 结果；整型结果必须整型 alpha，原文两条报错）+ `compute_names_npu` 名字传播 + 结果按 `result_type(self, other)` 申请（dest 输出取非包装侧张量 options）。`add.out` 的 `check_tensor({self}, result, result, output_size)` 以 **result 自身 dtype** 为期望（不强制 result_type），随后独立 `check_memory({self, other}, {result})`。`add_.Scalar` 直发 `aclnnInplaceAdds(self, other, alpha)`。

acl_op 回退（AddKernelNpu.cpp 148–305）：functional 先做**非连续 5D-5D 匹配特路** `npu_stride_add`（154–173 行，check_5d_5d_match+等尺寸才走）；再 `_npu_dtype_cast` 对齐 result_type 后，标量过载折叠 `other*alpha` 单标量 ACE "Add"、`alpha==1` 走 ACE "Add"（Bool+Bool 提升字节并标 uint8）、否则 ACE "AxpyV2"；910B1+ 用 `format_contiguous_add_copy_optimize`。

## sub 家族（sub.Scalar、sub.out、sub_.Scalar）

`sub_out`：`alpha_check_npu_tensor`（任一侧浮点/复型即可整型 alpha，全整型必须整型 alpha）→ `self_tensor_to_device`（仅 `is_scalar_wrapped_to_tensor` 触发，**不处理裸 CPU 0 维**）→ `check_tensor({self}, result, result, broadcast)` → 分支树：other 标量→`aclnnSubs(self, other.item(), alpha, result)`，否则 `aclnnSub`；`check_memory({self, other}, {result})` 在 check 之后单独调用。`sub.Scalar`：`alpha_check_npu_scalar`（把 other 标量纳入浮点判断）→ `input_same_output_size` + `result_type(self, other)` → `aclnnSubs` 直发。`sub_.Scalar`：alpha 标量检查后 `aclnnInplaceSubs` 直发（无 check_memory）。主线与发布两版本 逻辑相同（token 级）。acl_op 回退（SubKernelNpu.cpp 16–80）：标量侧 `other*alpha` 折叠单标量 ACE "Sub"；CPU 标量 self 先 `mul(other, alpha)` 再 "Sub"；`alpha!=1` 时张量路先 `at::mul(other, alpha)` 组合——**回退路 host 组合数比 aclnn 路多一次 mul**。

## mul.out

`mul_out`（MulKernelNpuOpApi.cpp 70–82）：dest=非包装侧张量；`result_type(self, other)`；**主线独有**：`self_tensor_to_device` 内对标量做 opmath 提升——`scalar.isFloatingPoint() && (result_type==Half||BFloat16)` 时 H2D 复制 dtype 用 **Float**（25–41 行，发布版无该分支、直接 result_type 复制）；`check_tensor({self}, result, result.scalar_type(), broadcast)`（期望=result 自身 dtype）；分支树：other 标量→`aclnnMuls(self, other.item(), result)`，否则 `aclnnMul`。主线 mul.out yaml 另带 `sparse: [v2.1, newest]` 登记（发布无，不影响 opapi 行为）。acl_op 回退（MulKernelNpu.cpp）：`calculate_type==kBool` 时改 **Float** 计算后回写；`other.dim()==0` 走 "Mul" 标量输入型命令，否则张量型；整型 canCast 检查。

## div 家族（div.Scalar_mode、div.Tensor_mode、div.out、div.out_mode、div_.Scalar_mode、div_.Tensor_mode）

DivKernelNpuOpApi.cpp 293 行主线与发布两版本 **字节相同**。核心事实：

| 入口 | 行为要点 |
|---|---|
| div.out（54–75） | 双 DO_COMPATIBILITY（aclnnDivs/aclnnDiv）；`result_type(self, other)` 后**整型/非复型→Float 提升**，但 `result` 本身是浮点/复型时改用 result dtype（协商而非强制）；`check_tensor({self}, result, result_type, broadcast)`；other CPU 0 维→`aclnnDivs(self, others, result)` 否则 `aclnnDiv` |
| div.out_mode（77–112） | DO_COMPATIBILITY(aclnnDivMods/aclnnDivMod)；rounding_mode 非 floor/trunc 直接 TORCH_CHECK false（原文 "div expected rounding_mode to be one of None, 'trunc', or 'floor' but found '…'"）；`check_tensor({self}, result, result.scalar_type(), broadcast)`（**out 自身 dtype**）；mode 映射 `floor=2 / trunc=1 / 其他=0`；other 标量→`aclnnDivMods(self_cp, others, mode, result)` 否则 `aclnnDivMod`；**mode 路不做整型→Float 提升**（high_type 保持 result_type） |
| div.Tensor_mode（139–182） | 同上模式校验；无 rounding_mode 时整型→Float 提升（真除法语义）、**有 floor/trunc 时不提升**（保持 result_type）；self 包装→dest 取 other；apply 后同标量/张量分支 |
| div.Scalar_mode（252–272）/ div_.Scalar_mode（280–291） | 标量 other 版：`aclnnDivMods/aclnnInplaceDivMods` 带 mode；`check_rounding_mode_npu` 校验；无 mode 整型→Float |
| div_.Tensor_mode（219–237） | `check_rounding_mode_npu` + `check_memory` + `aclnnInplaceDivMod(s)`，无输出申请 |

即同一对整型输入：`div(a,b)` 出 Float、`div(a,b,rounding_mode='floor'/'trunc')` 出 result_type（整型保持整型）——与 ATen 语义一致，但 out 变体的 dtype 协商规则不同（div.out 会因提升与整型 out 不匹配而 TORCH_CHECK 报错）。acl_op 回退（DivKernelNpu.cpp 16–234）：floor 模式直接委托 `floor_divide(_out)`，trunc 模式真除后 `acl_op::trunc_(result)` 再按 high_type cast；`get_divide_calculate_type/get_divide_result_type` 决定计算 dtype；标量/张量均 ACE "RealDiv"。

## fmod 家族（fmod.Tensor、fmod.Tensor_out、fmod_.Tensor）

FmodKernelNpuOpApi.cpp（主线与发布两版本 token 级相同）：`wrapped_to_scalar(other)` 谓词 = other 为 0 维 **且 Double/Long** 且 `GetSocVersion() >= Ascend950`（23–27 行，**SoC 版本门控的标量折叠**）→ true 时 `aclnnFmodScalar(self, other.item(), result)`，否则 `aclnnFmodTensor`；`fmod_out` 以 `check_tensor({self}, result, result.scalar_type(), broadcast)`（result 自身 dtype）+ `self_tensor_to_device`；`fmod_` 前置 TORCH_CHECK "Inplace tensor self must be NPU-Tensor."（104 行）。Scalar 过载（fmod.Scalar/fmod.Scalar_out/fmod_.Scalar）在生成路卡。acl_op 回退：ACE "Mod"（binary_op_check Expect；标量过载单标量输入型）。

## remainder 家族（remainder.Scalar、remainder.Scalar_Tensor、remainder.Scalar_out、remainder.Tensor、remainder.Tensor_out、remainder_.Scalar、remainder_.Tensor）

RemainderKernelNpuOpApi.cpp——**主线独有 CPU 标量分支**：tensor+tensor 的 out/functional/remainder_ 都先 `IsCPUScalar` 判 self/other 并 `.item()` 转 `aclnnRemainderScalarTensor/aclnnRemainderTensorScalar`，否则 `aclnnRemainderTensorTensor`；`remainder_(Tensor, Tensor)` 对 CPU 标量 other **委托标量过载** `op_api::remainder_(self, other_scalar)`（100–105 行）；`remainder(Scalar, Tensor)`（54–59）**无 DO_COMPATIBILITY**，无条件 `aclnnRemainderScalarTensor`（符号缺失时 EXEC 抬错，不回退）。发布版本 全部 tensor+tensor 路直发 `aclnnRemainderTensorTensor`（0 处 IsCPUScalar），标量过载保持。`remainder_out(Scalar/Tensor)` 期望 `out.scalar_type()`（out 自身 dtype）；functional 申请 `apply_tensor(output_size, …, output_tensor)`（注意是 apply_tensor 带 src 参形态，非 without_format）。`remainder_out(Tensor, Scalar)`（32–37）check 期望也是 out 自身 dtype、尺寸 self.sizes()。acl_op 回退（RemainderKernelNpu.cpp 16–120）：ACE "FloorMod"；Scalar self 过载先 canCast+`_npu_dtype_cast(other/result, calculate_type)` 再回写——**回退路带 dtype cast 协商**。

## log 家族（log、log.out、log_）

LogKernelNpuOpApi.cpp（主线与发布两版本 token 级相同）：`log_out` 在 `!result.is_same(self)` 时做 dtype 协商——期望=self dtype，但 `isIntegralType(self, true)` 提升 Float、**result 本身浮点/复型时改用 result dtype**；`check_tensor({self}, result, expect_dtype, self.sizes())`；随后独立 `check_memory({self}, {result})`；`aclnnLog(self, result)` 单命令。`log` functional：整型（含 Bool）→Float，其余 self dtype；`apply_tensor_without_format`；`aclnnLog`。`log_` 直发 `aclnnInplaceLog`（无检查）。acl_op 回退：ACE "Log" 带 `Attr base=-1.0, scale=1.0, shift=0.0`（16–30 行——**对数以 e 为底的属性编码**），CheckOut 强制 ND 格式。

## addcdiv（addcdiv、addcdiv.out、addcdiv_）与 addcmul（addcmul、addcmul.out、addcmul_）

两文件结构对称（主线与发布两版本 token 级相同）。`addcdiv_out`/`addcdiv_` 前置 `result_type({self,tensor1,tensor2})` 的 **canCast 到 result/self dtype** TORCH_CHECK（原文 "result type … can't be cast to the desired output type …"）；`addcdiv` functional 对 **tensor1 与 tensor2 均整型**直接 TORCH_CHECK false（60–72 行整段官方原文记录："Integer division with addcdiv is no longer supported, and in a future release addcdiv will perform a true division of tensor1 and tensor2. The historic addcdiv behavior can be implemented as (input + value * torch.trunc(tensor1 / tensor2)).to(input.dtype) for integer inputs and as (input + value * tensor1 / tensor2) for float inputs. The future addcdiv behavior is just the latter implementation: (input + value * tensor1 / tensor2), for all dtypes."）；尺寸为 `broadcast(broadcast(self, tensor1), tensor2.sizes())` **两重嵌套广播**；exec 单命令 `aclnnAddcdiv/aclnnInplaceAddcdiv`；out 变体 `check_tensor({self}, result, high_type, output_size)`（**期望=提升类型 high_type**，与 add/mul 的 result 自身 dtype 协商不同）。addcmul 全部同构但无整型拒绝段。acl_op 回退：ACE "Addcdiv"/"Addcmul"，`value` 以 self.scalar_type() 标量输入。

## atan2 家族（atan2、atan2.out、atan2_）

Atan2KernelNpuOpApi.cpp——**主线独有 CPU 标量 H2D**：三个入口都对 self/other 做 `IsCPUScalar→item→copy_scalar_to_device(scalar, 原dtype, 对侧张量device)`（发布直传原张量，0 处 IsCPUScalar）；functional 输出 `result_type(cp_self, cp_other)` 且整型→Float；out 变体期望 `out.scalar_type()`；`atan2_` 只对 other 复制后 `aclnnInplaceAtan2(self, cp_other)`。主线与发布两版本 共有：`aclnnAtan2` 单命令 + `compute_names_npu`。acl_op 回退：ACE "Atan2"（binary_op_check Expect）。

## complex 家族（complex、complex.out）

ComplexKernelNpuOpApi.cpp（主线与发布两版本 token 级相同）：functional `result_type(real, imag)` 为 Float/Double/Half 时分别提升 **ComplexFloat/ComplexDouble/ComplexHalf**（34–40 行）；`aclnnComplex(real, imag, result)` 单命令。out 变体 `check_tensor({real}, out, out.scalar_type(), broadcast)`。**acl_op 回退是 CPU 往返**（aclops/ComplexKernelNpu.cpp 20–40：`TORCH_NPU_WARN_ONCE("Warning: kernel [complex] is not supported by NPU currently. Now this kernel is running on CPU.")` 后 `.cpu()`→`at::native::complex`→回拷/`out.copy_`；complex_out 还会 `out.resize_(output_size)`）——aclnnComplex 缺符号时整族退 CPU。

## nan_to_num 家族（nan_to_num、nan_to_num.out、nan_to_num_）

NanToNumKernelNpuOpApi.cpp（主线与发布两版本 token 级相同）：`get_posinf_and_neginf`（23–70 行）默认值表——nan 默认 **0.0**；posinf/neginf 缺省按 self dtype：Double=±1.7976931348623157e+308、Float/其他=±3.4028235e+38、Half=±65504.0、BFloat16=±3.3895314e+38；**两个可选参数都显式给出时跳过 dtype 表**（直接取用户值）。`nan_to_num_out` 的 `check_tensor({self}, result, self.scalar_type(), self.sizes())`（期望=self dtype）；functional `apply_tensor_without_format(self)`；inplace 直发。`aclnnNanToNum/aclnnInplaceNanToNum` 单命令，三个标量均以 **float** 形参传入（Double 输入的默认 ±inf 也在 float 精度内截断表示）。acl_op 回退（NanToNumKernelNpu.cpp 93–112）：**整型（含 Bool）输入直接 copy 恒等返回**（不做命令派发），与主路的 dtype 校验行为一致。设备侧另见 [nan_to_num_950](../../../ops/ascendc/operators/aclnn/math/math/nan_to_num_950.md)。

## pow.Tensor_Tensor_out

PowKernelNpuOpApi.cpp（主线与发布两版本 token 级相同）`pow_out`（80–93）：`broadcast(self, exponent)` 尺寸；`self_tensor_to_device`（is_scalar_wrapped 或裸 CPU 0 维都 H2D）；`check_tensor({self, exponent}, out, out.scalar_type(), output_size)`（**src 列表含两个输入**、期望 out 自身 dtype）；分支：exponent CPU 0 维→`aclnnPowTensorScalar(self, exponent.item(), out)`，否则 `aclnnPowTensorTensor`。acl_op 回退（PowKernelNpu.cpp 16–80）：Tensor-Tensor "Pow"；Tensor-Scalar 在 `exp==2.0` 用 "Square"、`exp==0.0` `fill_(1)`、`exp==1.0` `copy_(self)` 的**常数捷径**。设备侧另见 [pow_tensor_tensor_950](../../../ops/ascendc/operators/aclnn/math/math/pow_tensor_tensor_950.md)。

## round.decimals 家族（round.decimals、round.decimals_out、round_.decimals）与 sgn（sgn、sgn.out）

RoundDecimalsKernelNpuOpApi.cpp（主线与发布两版本 token 级相同）：`round_decimals_check` 只放行 **浮点/Int/Long**（原文 `"round_npu" not implemented for '<dtype>'"`）；out 变体 `check_tensor({self}, result, self)`（self 参照，dtype+尺寸全等）；`aclnnRoundDecimals(self, decimals, result)`/inplace 直发。round 无小数位过载（round/round.out/round_）在生成路卡。acl_op 回退：ACE "Round" 带 `Attr("decimals", decimals)`。SignKernelNpuOpApi.cpp（主线与发布两版本 token 级相同）：`sgn_out` 的 `check_tensor({self}, result, self)`；`sgn` functional `input_same_output_size`+`apply_tensor_without_format(self.options())`（dtype=self）→`aclnnSign`；acl_op 回退 **sgn 纯委托 sign**（aclops SignKernelNpu.cpp 44–57：`sgn_out→sign_out`、`sgn→sign`、ACE "Sign"）。

## 优化与验收边界

- 热路径 add/sub/mul 的 CPU 标量张量会触发不同 aclnn 命令（Adds/Subs/Muls/AddV3）；AddV3 可用性是**运行时** dlsym 探测（静态缓存），跨 CANN 版本部署时同一代码路径可能不同——性能测量须确认实际命令而非源码常量。
- add/mul 的 out 变体与 addcdiv/addcmul 的 out 变体 **dtype 期望规则不同**（前者协商 result 自身 dtype、后者强制提升 high_type）——迁移 out= 惯用法时按族分别核对。
- div 的 rounding_mode 族不做整型提升；整型+floor 的输出保持整型，与真除法路径不同。
- 主线与发布两版本 差集中在：add AddV3 的 Long 排除（主线）、mul 标量 opmath Float 提升（主线）、remainder CPU 标量分支（主线独有）、atan2 CPU 标量 H2D（主线独有）、complex 的 CPU 回退（主线与发布两版本 回退侧共有）。按 pin 分别核对，不外推。
- 本卡静态口径，未运行任何分发/导入/数值验证；不把任一路径写成推荐配置。

## npu_stride_add 内核合同与 ldexp_stub 覆盖

上文 add 的 acl_op 回退记录了 5D-5D 匹配特路调用 `npu_stride_add`；本节补其内核本体 `StrideAddKernelNpu.cpp`（55 行，主线与发布两版本 去空白等价）。`npu_stride_add(self, other, offset1, offset2, c1_len)`：输出尺寸取 `op_infer::infersize_stride_add(self.sizes(), other.sizes())` 且**强制 `output_size[1] = c1_len*16`**（C1 通道块语义残留，NC1HWC0 时代契约）；随后 `apply_tensor(self, output_size)` 并发 ACE `StrideAdd`，属性 `x1_c1_offset`/`x2_c1_offset`/`c1_len` 均转 int64。入口由调用方的 `check_5d_5d_match` 门控，5D-5D 匹配之外无独立调用路径；设备侧语义与 C1 偏移的布局含义未核对。

另补 `LdexpKernelNpuOpApi.cpp`（主线独有文件，发布无同路径文件；`VERSION_BETWEEN(V2R11, VERSION_NEWEST)` 门控）：以 `REGISTER_PRIVATEUSE1_DISPATCH(ldexp_stub, &ldexp_kernel_npu)` **覆盖 ATen 的 ldexp 分派 stub**（与 SparseTensorUtils 的 flatten_indices 同一机制）——`at::ldexp` 在 NPU 上不是走 yaml 注册算子，而是 `mul_out(out, self, _pow2(self, exponent))` 的 host 组合；`_pow2` 对整型（含 bool）与 Float 输入用 `at::pow(2.0, exponent)`，其余 dtype 用 `full({}, 2.0, self.options()).pow(exponent)` 以保持标量 dtype。该组合引入一次额外 pow 物化；数值与调度代价未测。

## Evidence

- [AddKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddKernelNpuOpApi.cpp)（primary）：20–180 全文（分支树 46–74、AddV3 探测 58–62、alpha_check 23–32）。发布版全文（60 行守卫差按原文记录）。
- [SubKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SubKernelNpuOpApi.cpp)（primary）：两版全文 20–132。
- [MulKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MulKernelNpuOpApi.cpp)（primary）：两版全文 22–129（主线 opmath 分支 25–41）。
- [DivKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DivKernelNpuOpApi.cpp)（primary）：两版全文 20–293（字节相同）。
- [FmodKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FmodKernelNpuOpApi.cpp)（primary）：两版全文 20–109（wrapped_to_scalar 23–27）。
- [RemainderKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RemainderKernelNpuOpApi.cpp)（primary）：两版全文 20–111（主线 IsCPUScalar 分支 67–75/87–95/102–105；发布 0 处）。
- [LogKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogKernelNpuOpApi.cpp)（primary）：两版全文 20–64。
- [AddcdivKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddcdivKernelNpuOpApi.cpp)（primary）：两版全文 22–117（整型拒绝段 60–72）。
- [AddcmulKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddcmulKernelNpuOpApi.cpp)（primary）：两版全文 22–105。
- [Atan2KernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/Atan2KernelNpuOpApi.cpp)（primary）：两版全文 19–84（主线 H2D 25–34/46–55/72–76）。
- [ComplexKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ComplexKernelNpuOpApi.cpp)（primary）：两版全文 19–48。
- [NanToNumKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NanToNumKernelNpuOpApi.cpp)（primary）：两版全文 21–122（默认值表 23–70）。
- [PowKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PowKernelNpuOpApi.cpp)（primary）：两版全文 22–103。
- [RoundDecimalsKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RoundDecimalsKernelNpuOpApi.cpp)（primary）：两版全文 20–55。
- [SignKernelNpuOpApi.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SignKernelNpuOpApi.cpp)（primary）：两版全文 20–39。
- [op_plugin_functions.yaml 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：45 名条目（逐名 first/last line 锚定主线与发布两版 yaml 对应条目；mul.out 主线 sparse 标记 3645–3649）。
- aclops 回退侧（implementation，均 d84e9b1）：[AddKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddKernelNpu.cpp) 16–305、[SubKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SubKernelNpu.cpp) 16–80、[DivKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DivKernelNpu.cpp) 16–234、[FmodKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FmodKernelNpu.cpp) 16–106、[RemainderKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RemainderKernelNpu.cpp) 16–120、[LogKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogKernelNpu.cpp) 16–61、[NanToNumKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/NanToNumKernelNpu.cpp) 16–147、[PowKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PowKernelNpu.cpp) 16–80、[MulKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MulKernelNpu.cpp) 16–157（Bool→Float 计算段）、[AddcdivKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddcdivKernelNpu.cpp) 25–45、[AddcmulKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddcmulKernelNpu.cpp) 25–45、[Atan2KernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Atan2KernelNpu.cpp) 16–67、[SignKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SignKernelNpu.cpp) 40–62、[ComplexKernelNpu.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ComplexKernelNpu.cpp) 15–45（CPU 往返）。


- [StrideAddKernelNpu.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/StrideAddKernelNpu.cpp)（implementation）：全文 55 行；发布去空白等价。
- [LdexpKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LdexpKernelNpuOpApi.cpp)（implementation）：全文；发布无同路径文件（负向）。
## 关联

- [一元与逐元素数学生成包装路线卡](torch_npu_native_elementwise_math_gen_routes.md)（121 gen 名；round/trunc 整数恒等守卫与本卡 decimals 族的边界互补）
- [maximum.out/minimum.out（已核对）](../apis/torch_npu/legacy_min_max_and_sort.md)、[lerp/rsub cpu_scalar（已核对）](torch_npu_dynamic_selection_sync_and_where_scalar_execution.md)
- [logsumexp/logaddexp/gcd 归约族](torch_npu_logsumexp_logaddexp_gcd_routes.md)（DO_COMPATIBILITY/static 双符号探测同源）
- 设备侧不同层：[div_950](../../../ops/ascendc/operators/aclnn/math/math/div_950.md)、[inplace_divs_950](../../../ops/ascendc/operators/aclnn/math/math/inplace_divs_950.md)、[atan2_950](../../../ops/ascendc/operators/aclnn/math/math/atan2_950.md)、[log_950](../../../ops/ascendc/operators/aclnn/math/math/log_950.md)、[nan_to_num_950](../../../ops/ascendc/operators/aclnn/math/math/nan_to_num_950.md)、[pow_tensor_tensor_950](../../../ops/ascendc/operators/aclnn/math/math/pow_tensor_tensor_950.md)、[inplace_pow_tensor_scalar_950](../../../ops/ascendc/operators/aclnn/math/math/inplace_pow_tensor_scalar_950.md)
