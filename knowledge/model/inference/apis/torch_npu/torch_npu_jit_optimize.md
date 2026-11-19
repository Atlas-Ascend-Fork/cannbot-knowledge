---
type: API
title: torch_npu.jit.optimize：Script对象与FastGELU改写
description: 保存单参数对象合同和静态图改写，区分无返回值、推理优化与数值等价。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-jit/（beta）torch_npu-jit-optimize.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-jit/（beta）torch_npu-jit-optimize.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-jit/(beta)torch_npu-jit-optimize.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/jit/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/jit/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/jit/register_fusion_pattern.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/jit/register_fusion_pattern.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/jit/fusion_pass/fast_gelu.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/jit/fusion_pass/fast_gelu.py
  role: implementation
created_at: '2026-11-09T19:09:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# torch_npu.jit.optimize：Script对象与FastGELU改写

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文页及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页。A2/A3在本卡指训练系列，主线新增950DT确认不回推到发布版，不扩到950PR。旧Atlas产品只保留来源条目，不自动映射其他新型号。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf时单独指出，两个main不构成自动配套。以下为静态合同，没有编译、导入、加载模型、设备运行或性能测量。


## 输入与入口

`torch_npu.jit.optimize(jit_mod)`接收必填ScriptFunction或ScriptModule，文档用于性能优化。它不是torch.compile backend选择器，也不是任意Python nn.Module可直接传入的承诺。示例把简单加法/ReLU模型eval并trace，然后调用；没有NPU计时或数值断言。

## 两固定PyTorch实现

jit/__init__.py导出register_fusion_pattern.optimize，发布全文及独立主线完整差异均已读。对ScriptModule先调用torch.jit.optimize_for_inference，但不接住其返回对象；随后fast_gelu_pass直接改写jit_mod.graph，函数没有return，返回None。不能把调用返回值赋给模型后继续使用，也不承诺未接住的推理优化返回产物已被当前对象消费。

FastGELU模式只匹配aten::gelu且approximate常量为'none'的图形，替换为npu::fast_gelu；不是任意激活、所有GELU或所有分支都会融合。FastGELU替换不由名称证明与原精确GELU逐位相等，需要具体模型误差验收。

两版本实现差异主要排版，文档主线新增950DT确认不回推发布；不能据此把已弃用的存量TorchScript支持范围扩为当前所有编译路线。迁移与方法级限制见[存量TorchScript指南](../../guides/optimization/torch_npu/torch_npu_native_torchscript_legacy_scope.md)，本次没有trace、导出、改图或运行模型。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-jit/（beta）torch_npu-jit-optimize.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-jit/（beta）torch_npu-jit-optimize.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-jit/(beta)torch_npu-jit-optimize.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/jit/__init__.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/jit/__init__.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/jit/register_fusion_pattern.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/jit/register_fusion_pattern.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/jit/fusion_pass/fast_gelu.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/jit/fusion_pass/fast_gelu.py)（implementation）
