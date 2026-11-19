---
type: API
title: npu_add_rms_norm：残差相加与三输出语义
description: 说明残差 Add 与 RMSNorm 的融合顺序、FP32 rstd、残差输出和形状约束。
tags:
- task.lookup
- topic.compute.normalization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AddRmsNormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddRmsNormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AutogradErrorFallback.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_autograd_error_fallback.py
  role: example
created_at: '2026-11-09T01:52:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npu_add_rms_norm：残差相加与三输出语义

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_add_rms_norm(x1, x2, gamma, epsilon=1e-06) -> (Tensor, Tensor, Tensor)
```

先计算 z=x1+x2，再输出 RMSNorm(z)。返回顺序是 (yOut, rstdOut, xOut)，xOut 是相加后的残差 z，不是原始 x1 或第二份 y。yOut、xOut 与 x1 的 shape 和 dtype 相同。

## 参数与组合限制

- x1/x2 为 1–8 维 ND Tensor，支持 FP16、BF16、FP32；gamma 类型与 x1 一致，形状匹配参与归一化的末尾维度。
- 此接口不支持空 Tensor，支持非连续 Tensor；不要沿用 npu_rms_norm 对空输入的说明。
- rstdOut 为 FP32，并保留被归一化维度为 1：如 x1=(2,3,4,8)、gamma=(4,8) 时，rstdOut=(2,3,1,1)。
- 来源对旧 Atlas 推理系列另有限制；本卡只覆盖 A2/A3，不将 BF16 或 rstd 结论扩展到其他产品。

## 验证与模型关联

分别比对 xOut 与显式残差相加、yOut 与参考 RMSNorm，单独检查 rstd dtype/shape；覆盖非连续输入和不同归一化尾维。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L184)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 固定主线的空输入说明与原地变体

主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的参数页改为支持空Tensor，与本卡发布来源“不支持空”的说明分别适用；本文未运行以确认两个版本实现差异。主线单算子仍要求x2/gamma与x1同dtype，三输出顺序和rstd的FP32含义不变，文档列单算子及TorchAir模式。

同主线[950原地v2接口](npu_add_rms_norm_v2.md)会覆盖x1/x2且只返回rstd，不能因函数名接近而按本卡三输出替换；也不能把v2的无空Tensor约束反向套到主线非原地接口。

## 完整双语页面与分配路径复核

发布中文与主线中英文全文/完整差异确认：发布拒绝空Tensor，主线允许空Tensor；主线明确x2同x1 shape、Eager三输入同dtype，新增950PR及950DT，不能回推发布。旧Atlas推理系列不支持BF16且rstd参数无效，不能以现代产品统计量规则外推旧产品。默认epsilon为1e-6，归一化尾轴由gamma形状确定。

两个固定ACL实现都以gamma.dtype分配y/x，FP32分配保留尾轴为1的rstd；生成式ACLNN包装则以x1.dtype分配y/x，Meta也取x1。公开同dtype共同子集下吻合，内部允许进入某分支不构成混合dtype公开支持。Inf/NaN文字仅是文档边界描述，本次未运行极值。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AddRmsNormKernelNpu.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddRmsNormKernelNpu.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

## 主线无反向实现的抛错边界

主线 [d84e9b1d6a558e5f27973cd4329f62968e46fdda 的 AutogradErrorFallback.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AutogradErrorFallback.cpp)（全 17 行读毕）为 `npu_add_rms_norm` 注册 PyTorch 内置 `autogradNotImplementedFallback`（`AutogradPrivateUse1` dispatch key 上的 boxed 内核；源注释自述对任意算子 schema 通用、无需匹配各自签名）。实际门槛与动作：前向照常执行；仅当对依赖本算子输出的张量调用 `.backward()` 时抛 `RuntimeError`，源注释给出的文案模式是 `derivative for 'npu::xxx' is not implemented`，主线[官方用例](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_autograd_error_fallback.py)只断言 "not implemented" 子串，完整文案未运行核对。用例以 `requires_grad` 叶子张量进入前向构造依赖，且仅声明在 A5 / Ascend950 验证、其它机型自动跳过。

失败与版本边界：该注册只覆盖 `npu_add_rms_norm` 单 schema，[950 原地 v2 接口](npu_add_rms_norm_v2.md) 不在注册列表，不能据本节推断 v2 的反向状态。
发布 dedc316708372c9a8bfde4527abd2a94b74840f5 没有该文件，且全仓不含任何 `autogradNotImplementedFallback` 注册（rg 负向核实），发布组合下反向缺失的行为未由本节建立。本节为静态阅读，未运行反向。
