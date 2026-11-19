---
type: API
title: npu_scaled_masked_softmax：缩放、广播掩码与形状限制
description: 记录预留上三角开关只支持 False、H/W 对齐范围和 950 与旧产品的执行路径。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scaled_masked_softmax.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scaled_masked_softmax.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledMaskedSoftmaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ScaledMaskedSoftmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_scaled_masked_softmax.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ScaledMaskedSoftmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScaledMaskedSoftmaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-09T07:57:02Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npu_scaled_masked_softmax：缩放、广播掩码与形状限制

## 版本与范围

本卡依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`；发布子模块 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的对应页另作版本约束。主线候选与ascend_26_0_pt28组合分别管理，不能只因接口同名推断可混用。 本卡选A2/A3训练产品及主线新增950；不把950支持回推发布页。

## 接口与约束

```text
torch_npu.npu_scaled_masked_softmax(x, mask, scale=1.0, fixed_triu_mask=False) -> Tensor
```

对scale*x施加BOOL mask，再沿最后一轴Softmax；返回与x同shape/dtype/格式的Tensor。x支持FP16/BF16/FP32，页面格式列ND/FRACTAL_NZ，mask必须可广播到x。按页面转换为NCHW后的H/W均需在[32,4096]且32整除，不把任意长序列或任意rank都视为合法。

fixed_triu_mask是未完成的预留功能，当前仅False。不能传True来替代显式因果mask；实现将参数继续下传不表示产品约束已放开。页面没有完整定义全mask行的数值结果，不能从其他Softmax接口推断该行为。

## 实现与反向

主线小于950的产品走acl_op::ScaledMaskedSoftmax；950优先aclnnScaledMaskedSoftmax，缺接口时兼容回退旧路径。950包装接受浮点或整数Scalar scale并转double传入，不能据包装类型扩大硬件支持。两条路径的内部格式处理不同，不由公开“格式同输入”推断每条低层分配都保留相同私有格式。

autograd对x调用npu_scaled_masked_softmax_backward，传入前向输出、mask、scale和fixed_triu_mask；mask与scale不因此成为可微Tensor输入。Meta只分配同规格输出，不能验证mask广播、对齐或数值正确性。


## 验证边界

按实际软件栈验证目标shape、dtype、mask语义和输出，再比较稳态性能。本卡只做固定文档与实现的静态审阅，未执行上游代码或NPU数值/性能测试。

- [软件栈版本与来源身份](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## 双语全页与两固定路径核对

发布中文及主线中英文完整页保持H/W为32..4096且32整除、BOOL可广播mask、fixed_triu_mask仅False；主线新增950PR及950DT，不回推发布。两提交的ACL和OpAPI都保留前后向、产品分支与兼容回退，注册仍只对x接反向。

BOOL mask的保留/遮蔽极性和全遮蔽行数值没有被页面的全零mask例子完整定义；包装只是传入mask，Meta只empty_like。不能把例子、内部接受True或整型scale解释为扩展公开参数合同，也不能因名字相似就套用fusion_attention的mask极性。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scaled_masked_softmax.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scaled_masked_softmax.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledMaskedSoftmaxKernelNpuOpApi.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ScaledMaskedSoftmaxKernelNpu.cpp)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_scaled_masked_softmax.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ScaledMaskedSoftmaxKernelNpu.cpp)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScaledMaskedSoftmaxKernelNpuOpApi.cpp)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）
