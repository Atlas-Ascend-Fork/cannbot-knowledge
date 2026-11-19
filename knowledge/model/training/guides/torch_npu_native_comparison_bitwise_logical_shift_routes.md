---
type: Guide
title: 比较、位运算、逻辑与移位算子：双派发路包装与Bool/标量不对称
description: 汇总eq/ne/gt/ge/le/lt、equal、bitwise与/或/异或、dunder移位、logical族、isneginf/isposinf、signbit的op_api与acl_op双路实现：CPU标量翻转、计算类型提升不对称、Bool输出与Long提升规则、950分支主线独有、生成spec与手写文件边界。
tags:
- task.implementation
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EqKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GtKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LeKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LtKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NeKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EqualKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BitwiseAndKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BitwiseOrKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BitwiseXorKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BitwiseLeftShiftKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BitwiseRightShiftKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/__Lshift__KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/__Rshift__KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/__iLshift__KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/__iRshift__KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/__Ior__KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogicalOrKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EqKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GtKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LtKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/NeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EqualKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BitwiseAndKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BitwiseOrKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BitwiseXorKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogicalAndKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogicalNotKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogicalXorkernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogicalOrKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/IsNegInfKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/IsPosInfKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/__Lshift__KernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/__Rshift__KernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/__iLshift__KernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/__iRshift__KernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/__Ior__KernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/EqKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GtKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LtKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/EqualKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BitwiseAndKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BitwiseOrKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BitwiseXorKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/__Lshift__KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/__Rshift__KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/__iLshift__KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/__iRshift__KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/__Ior__KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogicalOrKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EqKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GtKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LtKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/NeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EqualKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BitwiseAndKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BitwiseOrKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BitwiseXorKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogicalAndKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogicalNotKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogicalXorkernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogicalOrKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/IsNegInfKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/IsPosInfKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/__Lshift__KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/__Rshift__KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/__iLshift__KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/__iRshift__KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/__Ior__KernelNpu.cpp
  role: implementation
created_at: '2026-11-12T17:05:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 比较、位运算、逻辑与移位算子：双派发路包装与Bool/标量不对称

## 固定来源与范围

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布 `dedc316708372c9a8bfde4527abd2a94b74840f5`。本卡覆盖比较（eq/ne/gt/ge/le/lt 的 `.Scalar_out`/`.Tensor_out`/`eq_` 等inplace与 `equal`）、位运算（bitwise_and/or/xor ±out 与 and_/xor_ inplace、`__ior__`）、dunder移位（`__lshift__`/`__rshift__`/`__ilshift__`/`__irshift__`）、`bitwise_left_shift`/`bitwise_right_shift` 九名、逻辑族（logical_and/not/or/xor ±out/inplace）、`isneginf.out`/`isposinf.out`、`signbit.out` 共75个登记名的双派发路（op_api 手写包装与 acl_op 旧ACE路）实现事实；functional `eq.Scalar`/`eq.Tensor` 等带 dvm 标记的12个入口已由[DVM逐入口准入卡](../../inference/guides/optimization/torch_npu/torch_npu_eager_dvm_elementwise_precision_and_fallback.md)按yaml标记核对，本卡不重复。主线与发布两版本除下文明示差异（950分支、`cpu_scalar_h2d`、dvm标记、bitwise_left/right_shift登记面）外，所读文件语义一致：主线经clang-format、发布为旧排版，整文件 `diff -wB` 过滤排版后仅剩下文明示的实质差异。本卡仅静态阅读，未运行任何算子、设备或性能实验，不新增verified或平台承诺。

## 比较算子：op_api手写包装

六文件（Eq/Gt/Ge/Le/Lt/Ne KernelNpuOpApi.cpp）共享一个模板，每个入口先 `DO_COMPATIBILITY(aclnnXxx, acl_op::同名)` 再走aclnn直发。差异逐项按原文记录：

| 入口门槛→动作 | 失败/版本边界 |
| --- | --- |
| functional/out Tensor：`broadcast_ops_npu_output_size` 后 functional 以 `apply_tensor_without_format(..., at::kBool)` 申请、out 以 `check_tensor` 校验，单次 `EXEC_NPU_CMD(aclnnXxxTensor, ...)` 并 `propagate_names_if_nonempty`（Eq 23–48/50–81，Gt 53–79/81–111 同构） | 输出强制Bool是包装约定；check_tensor的dtype参照各文件不一致（Eq用`{self,other}`四参、Le/Lt用`result.scalar_type()`五参），按原文记录不判断意图 |
| CPU 0维标量翻转：self为CPU标量时 gt→`aclnnLtScalar(other,self_scalar)`、lt→`aclnnGtScalar`、le→`aclnnGeScalar`、ne/eq→本op标量命令（交换实参）；other为CPU标量时走本op Scalar命令（Gt 69–77、Lt 37–44、Le 39–47、Ne 38–45） | Ge的functional例外：用 `other.dim()==0 && !is_npu(other)` 判定而非IsCPUScalar，且self侧翻转命令字面为 `aclnnLessScalar`（Ge 75–86）——与lt的`aclnnLtScalar`命名不同，按原文记录 |
| inplace Tensor：gt_/ge_/le_ 用 `other.dim()==0 && !is_npu(other)` 先转标量inplace、否则TORCH_CHECK同设备+`CheckMemory`；lt_ 用IsCPUScalar转标量、无CheckMemory；ne_ 先`check_memory`再IsCPUScalar转标量；eq_ 无任何CPU标量转派，总是check_memory后直发（Eq 112–132、Gt 113–136、Lt 103–122、Ne 92–107） | 五种inplace前置检查互不相同，均为字面按原文记录；标量inplace变体一律无检查直发 `aclnnInplaceXxxScalar` |
| **主线独有950分支**：`is_ascend950_path()` 为真时 `prepare_binary_tensors` 预处理、functional/out/inplace均换走device张量；inplace先TORCH_CHECK `is_npu(self)`（原文"inplace eq_ requires self to be NPU tensor"）再把非NPU other `other.to(self.device())`，CheckMemory后执行 | 发布版本六文件 `is_ascend950_path` 零命中（rg核实）；发布无此分支即CPU标量路径按上文通用规则处理 |
| equal op_api（主线与发布两版本逐字节相同）：namedinference names不同直接return false；`apply_tensor_without_format({1}, Bool)` 后单次 `EXEC_NPU_CMD(aclnnEqual)`，`result.item().to<bool>()` 返回（Equal 23–31） | `.item()` 是host同步点；names比较在内核外短路，与下文aclops的sizes短路不同层 |

## 比较算子：acl_op旧ACE路与计算类型提升不对称

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| ACE命令名：eq→"Equal"、gt→"Greater"、ge→"GreaterEqual"、le→"LessEqual"、lt→"Less"、ne→"NotEqual"；Tensor/Scalar两nocheck同命令名（Eq 27/33，Gt 29/41，Ge 28/39，Le 27/39，Lt 29/35，Ne 34/46） | 命令名是ACE图描述符，与aclnn符号名（aclnnEqTensor等）两套体系，不互推内核行为 |
| **计算类型提升不对称**（get_xx_calculate_type）：eq仅Int→Float；gt仅Bool→Float；ge Int或Bool→Float；lt `isIntegralType(...,true)` 全部整型→Float；le与ne不做任何提升（直接`at::native::result_type`）（Eq 37–51、Gt 50–63、Ge 47–60、Lt 40–53、Le 51/95、Ne 69/92） | 同为比较族，Int64输入在lt路被转Float计算、在le/ne路保持Long进入ACE命令；语义差异未运行验证，只声明包装事实 |
| CPU标量self翻转：eq/ne交换实参转本op标量；gt→`lt_out(other,self.item())`、lt→`gt_out`、ge→`le_out`、le→`ge_out`（Gt 70–71、Lt 60–61、Ge 67–68、Le 80–81） | 翻转发生在**包装层互相调用**，最终仍走被调op的命令与提升规则 |
| ne的Long告警：self为kLong时两nocheck先 `TORCH_NPU_WARN_ONCE("The oprator of ne is executed, Currently High Accuracy but Low Performance OP with 64-bit has been used, Please Do Some Cast at Python Functions with 32-bit for Better Performance!")`（Ne 28–33/41–44，主线与发布两版本同） | 仅ne族有此告警（其余五文件rg零命中）；告警不改变执行 |
| out非Bool：result非Bool时先 `_npu_dtype_cast(result, kBool)` 计算，再cast回result dtype并 `result.copy_(result_cast)`（Eq 75–89等六文件同构） | out可以为非Bool整型并得到0/1回填；两次cast是额外host开销，未量化 |
| inplace：六文件的 `xx_(self, other, self)` 一律转调本op `xx_out(self, other, self)`（Eq 151–157、Gt 168–174等） | inplace即out(self)复用，继承上文out路径全部cast行为 |
| equal acl_ops：sizes不等直接false；dtype不等TORCH_CHECK（原文"...for argument #2 'other' in call to equal_npu"）；`apply_tensor_with_format({1}, Bool, ACL_FORMAT_ND)` 后ACE "TensorEqual"，`result.item().to<bool>()`（Equal 23–42） | 与op_api路三处不同：sizes短路在names短路之外、dtype是硬检查（op_api路无dtype检查）、命令用"TensorEqual"而非aclnnEqual；`.item()` 同为host同步 |

## 位运算 and/or/xor 与 __ior__

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| op_api Scalar变体：self为Bool且Scalar非布尔时，and/or/xor三文件同规则——输出按 `at::kLong` 申请（BitwiseAnd 97–101、BitwiseOr 49–54、BitwiseXor 45–53）；否则 `apply_tensor_without_format(self)` | Bool张量与非布尔标量运算被提升到Long输出，三族一致；out的Scalar变体不重算dtype，仅 `check_tensor({self}, out, self.sizes())` |
| op_api Tensor变体：and/or/xor functional/out均**双DO_COMPATIBILITY**（先Scalar后Tensor符号各查一次）；输出dtype `at::native::result_type(self, other)`；CPU标量any侧转Scalar变体（BitwiseAnd 46–88、BitwiseOr 60–81、BitwiseXor 55–83） | 双符号缺失才整体回退acl_op；`result_type` 是ATen类型提升，非本层约定 |
| op_api inplace不对称：`bitwise_and_(Tensor)` 直接进nocheck执行（无CheckMemory，BitwiseAnd 108–123）；`bitwise_xor_(Tensor)` 先 `check_memory({self,other},{self})`（BitwiseXor 87–91） | and_无内存重叠检查、xor_有，字面按原文记录；Scalar inplace两者均直发 `aclnnInplaceXxxScalar` |
| **bitwise_or_ 无op_api实现**：BitwiseOrKernelNpuOpApi.cpp（82行）只含out/functional四个入口；主线与发布两版本 yaml无 `bitwise_or_.Scalar/.Tensor` 条目（rg零命中） | `bitwise_or_` 本名不在登记面；但 `__ior__` 见下文经它转派 |
| `__ior__` op_api（主线与发布两版本同）：`__ior__(Tensor/Scalar)` 仅一行 `return self.bitwise_or_(other);`，无DO_COMPATIBILITY、无任何检查（__Ior__ 23–29） | 转派的 `bitwise_or_` 在六个固定版本内无注册（op-plugin主线与发布两版本 yaml与torch_npu rg均零命中，AOTI shim仅声明functional `bitwise_or`），最终落点在上游ATen派发（六个固定版本外），静态不可核对——不能断言成功、报错或回退CPU |
| `__ior__` acl_op（主线与发布两版本同）：CheckMemory({self,other},{self})（Scalar变体无）+check_match/format_contiguous自刷新后按dtype切命令：Bool→"LogicalOr"、否则"BitwiseOr"（__Ior__ 23–72） | 旧路是真实实现，与op_api路的纯转派形成可观察差异；format刷新见[整备卡](../../inference/guides/optimization/torch_npu/torch_npu_out_preparation_resize_and_overlap.md)已核对语义 |
| acl_op and/or：Bool输入切"LogicalAnd"/"LogicalOr"命令，否则"BitwiseAnd"/"BitwiseOr"；CheckOut+check_match/format_contiguous+format_fresh_view（BitwiseAnd 24–98、BitwiseOr 24–89） | 命令切换按self dtype，不检查other |
| acl_op xor例外：Bool的self/result（Tensor路连other）先 `_npu_dtype_cast` 到 **Int** 计算，结果cast回Bool（BitwiseXor 45–58/69–84/95–105/112–116） | 三族Bool策略分化：and/or换命令名、xor换计算dtype、op_api层则统一Long提升——同一Bool语义在两层三路做法不同，未验证数值等价 |

## 移位族

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| op_api `__lshift__(Tensor)`：broadcast size + `at::native::result_type` 提升dtype申请，`aclnnLeftShift`；`__lshift__(Scalar)`：先 `apply_tensor(self)`（不提升）再DO_COMPATIBILITY后 `aclnnLeftShifts`（__Lshift__ 22–35） | Scalar变体的申请发生在DO_COMPATIBILITY之前，符号缺失回退acl_op时该申请成为无用开销，顺序按原文记录；输出跟随self dtype（无result_type）与Tensor变体不一致 |
| op_api `__rshift__`：Scalar变体 `copy_scalar_to_device(other, self.scalar_type(), self.device())` 物化0维张量后走 `aclnnRightShift`（无LeftShifts式标量命令，不对称）；Tensor变体直发（__Rshift__ 23–37） | 左移有专用标量aclnn（LeftShifts）、右移没有，字面按原文记录 |
| op_api inplace：`__ilshift__` 两变体直发 `aclnnLeftShift/LeftShifts` 写self，无CheckMemory（__iLshift__ 23–31）；`__irshift__(Tensor)` 有CheckMemory、Scalar变体同上物化（__iRshift__ 23–36） | ilshift/irshift的inplace检查不对称，与bitwise and_/xor_的同型不对称并列按原文记录 |
| acl_op `__lshift__`：Scalar变体 `at::empty(self.sizes())` + `acl_op::fill_` **全尺寸物化**移位量张量后才发ACE "LeftShift"；Tensor变体 `other.expand(self.sizes())`——以self形状为准，无通用广播；输出 `apply_tensor(self)`（__Lshift__ 22–54） | scalar fill_ 物化多一次整尺寸写；expand要求other可广播到self形状，self≠广播结果的组合未定义于本层 |
| acl_op `__rshift__`：Scalar变体 OpCommand 标量直传（`.Input(other, self.scalar_type())`，无物化——与lshift不对称）；ACE "RightShift"（__Rshift__ 23–50） | 左物化右直传，按原文记录 |
| acl_op inplace：ilshift/irshift均先check_match自刷新（format_contiguous+format_fresh_view）；irshift的Tensor变体另有CheckMemory、ilshift无（__iLshift__ 24–65、__iRshift__ 24–66） | 与op_api层的同名不对称方向一致 |
| `bitwise_left_shift`/`bitwise_right_shift` 九名：**主线独有**，op_api `[v2.7, newest]`（yaml 5598–5645），发布版本该族rg零登记、亦无BitwiseLeftShift/RightShiftKernelNpuOpApi.cpp文件（负向核实） | 生成/手写混合：left_shift Tensor_out/Tensor_Scalar(±out)/left_shift_ 由gen_opapi生成（exec aclnnLeftShift/LeftShifts，left_shift_ 继承Tensor_Scalar_out）；left_shift.Scalar_Tensor 与 right_shift 全部四名手写——`copy_scalar_to_device` 物化 + `aclnnRightShift`，right_shift的out/inplace变体不重算dtype直接写out/self（BitwiseLeftShift 23–31、BitwiseRightShift 23–51） |

## 逻辑族、isneginf/isposinf 与 signbit

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| logical_or 手写双层 op_api：out/functional `aclnnLogicalOr` + CPU 0维other `copy_scalar_to_device` 物化；inplace `aclnnInplaceLogicalOr` + check_memory（LogicalOr opapi 23–65）；functional输出Bool申请+names传播 | 唯一手写opapi的逻辑族成员（yaml无gen_opapi条目，主线与发布两版本同） |
| logical_or acl_op：ACE "LogicalOr"；functional先 `apply_tensor(self, output_size)`（**self dtype**）计算后再 `_npu_dtype_cast(result, kBool)`；out变体CheckOut按 `out.scalar_type()` 保留out dtype、仅check_match刷新（LogicalOr aclops 24–70） | functional输出经过一次后置cast，out变体不强制Bool——同op_api路（强制Bool）不同；按原文记录 |
| logical_and/not/xor op_api路为**生成代码**：gen_opapi登记 exec aclnnLogicalAnd/aclnnInplaceLogicalAnd、aclnnLogicalNot/aclnnInplaceLogicalNot、aclnnLogicalXor；logical_and三schema带 `cpu_scalar_h2d: [other]`（**主线独有**，发布同族无该标记，yaml 3209–3237 vs 发布3110–3135）；生成体不随仓提交 | 生成spec即登记面实现事实；生成wrapper的实际host检查未运行gencode验证；cpu_scalar_h2d语义已由[动态选择卡](torch_npu_dynamic_selection_sync_and_where_scalar_execution.md)按struct_codegen核对，本卡不重复 |
| logical_and acl_op：非Bool输入两侧各自 `_npu_dtype_cast` 到Bool后ACE "LogicalAnd"；out为非Bool或格式不匹配时按Bool算完cast回 **self.scalar_type()**（logical_and_ TORCH_CHECK self/other dtype相同后转 `logical_and_out(self, other, self)`）（LogicalAnd 24–82） | out路径回填dtype参照self而非out声明，与out实参dtype不同时行为未核对；TORCH_CHECK原文"Expected object of scalar type ..." |
| logical_not acl_op：self/result任一非Bool均cast Bool 计算，result非Bool再cast回result dtype+copy_；`logical_not_` 转 `logical_not_out(self, self)`；ACE "LogicalNot"（LogicalNot 24–67） | 与logical_and的回填参照（self）不同，not参照result——按原文记录 |
| logical_xor acl_op：非Bool两侧cast Bool后发 **"NotEqual"** 命令（复用不等命令实现异或）；0维任一侧转Scalar路径；out非Bool时Bool算完cast回 **result.scalar_type()**（LogicalXor 24–73） | 第三种Bool策略（bitwise_xor是Int、logical_and是self参照、此处NotEqual命令+result参照）；文件名 `LogicalXorkernelNpu.cpp` 小写k，路径按原文记录 |
| isneginf.out/isposinf.out：op_api路生成（out size=self，exec aclnnIsNegInf/aclnnIsPosInf，主线与发布两版本同spec）；**acl_op路CPU回退**：`TORCH_NPU_WARN_ONCE("Warning: kernel [isneginf] is not supported by NPU currently. Now this kernel is running on CPU.")` 后 `self.cpu()` → `at::isneginf` → `.to(self.device())`；out变体连out一起cpu往返+copy_（IsNegInf 19–34、IsPosInf 19–34） | 整算子级CPU往返（含device↔host拷贝）；`at::isneginf` 是上游ATen（六个固定版本外）实现；aclnnIsNegInf设备语义未核对，两路数值等价性未验证 |
| signbit.out：**仅op_api登记**（`op_api: all_version`，无acl_op条目——与isneginf双登记不对称，yaml 4644–4650主线与发布两版本同）；gen_opapi生成 out size=self dtype=out，exec aclnnSignbit；主线与发布两版本无手写实现文件（opapi/aclops rg零命中） | 无acl_op回退路：DO_COMPATIBILITY类回退不存在，aclnnSignbit符号缺失时的行为在生成体/SDK侧，未核对 |

## 跨族边界

- DO_COMPATIBILITY 宏语义（AclnnOnly抛错/否则LOGW回退acl_op）引用[sort/topk卡](torch_npu_sort_topk_routing_and_legacy_output_costs.md)已核对结论，本卡不重复展开。
- 主线独有差异汇总：比较六文件opapi的 `is_ascend950_path` 分支（functional/out/inplace全套）；`logical_and` 族的 `cpu_scalar_h2d` 生成标记；`bitwise_left_shift`/`bitwise_right_shift` 全族登记；`eq/ge/gt/le/lt/ne` functional的 `dvm: all_version` 标记（发布yaml无，见[DVM卡](../../inference/guides/optimization/torch_npu/torch_npu_eager_dvm_elementwise_precision_and_fallback.md)）。
- 未核对边界：所有aclnn*/ACE命令的设备内核语义；生成wrapper实际host检查（gen_opapi生成体不随仓提交，按登记面记录）；`__ior__` op_api路转派的 `bitwise_or_` 上游ATen落点（六个固定版本外）；`at::isneginf`/`at::native::result_type`/`at::native::quantize_*` 等ATen组合内部。本卡不据此宣称任何设备数值行为或性能结论。

### 证据（主线与发布两版本整文件比对与行锚）

以下主线行锚为primary读；发布文件经整文件 `diff -wB` 排版过滤比对，实质差异仅上文明示项（950分支/cpu_scalar_h2d/dvm/left_shift族），其余语义一致。

- [EqKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EqKernelNpuOpApi.cpp)（primary）：20–140。
- [GtKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GtKernelNpuOpApi.cpp)（primary）：20–137。
- [GeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeKernelNpuOpApi.cpp)（primary）：20–119。
- [LeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LeKernelNpuOpApi.cpp)（primary）：20–130。
- [LtKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LtKernelNpuOpApi.cpp)（primary）：20–130。
- [NeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NeKernelNpuOpApi.cpp)（primary）：20–120。
- [EqualKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EqualKernelNpuOpApi.cpp)（primary）：20–32。
- [BitwiseAndKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BitwiseAndKernelNpuOpApi.cpp)（primary）：20–130。
- [BitwiseOrKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BitwiseOrKernelNpuOpApi.cpp)（primary）：20–82。
- [BitwiseXorKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BitwiseXorKernelNpuOpApi.cpp)（primary）：20–95。
- [BitwiseLeftShiftKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BitwiseLeftShiftKernelNpuOpApi.cpp)（primary）：20–31；主线独有文件。
- [BitwiseRightShiftKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BitwiseRightShiftKernelNpuOpApi.cpp)（primary）：20–53；主线独有文件。
- [__Lshift__KernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/__Lshift__KernelNpuOpApi.cpp)（primary）：20–36。
- [__Rshift__KernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/__Rshift__KernelNpuOpApi.cpp)（primary）：20–38。
- [__iLshift__KernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/__iLshift__KernelNpuOpApi.cpp)（primary）：20–32。
- [__iRshift__KernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/__iRshift__KernelNpuOpApi.cpp)（primary）：20–36。
- [__Ior__KernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/__Ior__KernelNpuOpApi.cpp)（primary）：20–30。
- [LogicalOrKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogicalOrKernelNpuOpApi.cpp)（primary）：20–67。
- [EqKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EqKernelNpu.cpp)（primary）：19–158。
- [GtKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GtKernelNpu.cpp)（primary）：19–175。
- [GeKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GeKernelNpu.cpp)（primary）：19–169。
- [LeKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LeKernelNpu.cpp)（primary）：19–155。
- [LtKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LtKernelNpu.cpp)（primary）：19–161。
- [NeKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/NeKernelNpu.cpp)（primary）：19–153。
- [EqualKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EqualKernelNpu.cpp)（primary）：19–42。
- [BitwiseAndKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BitwiseAndKernelNpu.cpp)（primary）：19–98。
- [BitwiseOrKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BitwiseOrKernelNpu.cpp)（primary）：19–89。
- [BitwiseXorKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BitwiseXorKernelNpu.cpp)（primary）：19–128。
- [LogicalAndKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogicalAndKernelNpu.cpp)（primary）：19–82。
- [LogicalNotKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogicalNotKernelNpu.cpp)（primary）：19–67。
- [LogicalXorkernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogicalXorkernelNpu.cpp)（primary）：19–73。
- [LogicalOrKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogicalOrKernelNpu.cpp)（primary）：19–70。
- [IsNegInfKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/IsNegInfKernelNpu.cpp)（primary）：15–43。
- [IsPosInfKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/IsPosInfKernelNpu.cpp)（primary）：15–43。
- [__Lshift__KernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/__Lshift__KernelNpu.cpp)（primary）：19–54。
- [__Rshift__KernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/__Rshift__KernelNpu.cpp)（primary）：19–50。
- [__iLshift__KernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/__iLshift__KernelNpu.cpp)（primary）：19–65。
- [__iRshift__KernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/__iRshift__KernelNpu.cpp)（primary）：19–66。
- [__Ior__KernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/__Ior__KernelNpu.cpp)（primary）：19–72。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（primary）：3–43（dunder移位十名）、1447–1531（bitwise and/or/xor 全部18名）、2052–2080（eq族+equal）、2421–2445、2542–2566、2839–2854（isneginf/isposinf）、2899–2923、3209–3294（logical族九名+logical_or_）、3334–3358、3786–3810、4644–4650（signbit.out）、5598–5645（bitwise_left/right_shift 九名）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3–43、1397–1481、1989–2015、2350–2368、2462–2480、2753–2767、2817–2835、3110–3191、3235–3253、3685–3703、4492–4498；同名条目与主线登记一致（除正文明示的dvm/cpu_scalar_h2d/left_shift族差异）；`bitwise_left_shift`/`bitwise_right_shift` 全族rg零命中。
