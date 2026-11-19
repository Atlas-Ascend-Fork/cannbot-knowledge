---
type: API
title: matmul_transpose：末两维转置与定制反向
description: 区分Q乘KT和普通matmul，纠正文档动态限制误植并保留broadcast边界。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-matmul_transpose.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-matmul_transpose.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-matmul_transpose.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/matmul_transpose.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/matmul_transpose.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/_matmul_transpose.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/_matmul_transpose.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# matmul_transpose：末两维转置与定制反向

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 接口与梯度

`contrib.function.matmul_transpose(tensor1,tensor2)`实际为MatmulApply.apply，前向torch.matmul(tensor1,tensor2.transpose(-2,-1))并detach结果，由自定义Function建立反向；不是直接相乘，也不能把detach解释为整个接口没有梯度。

反向对tensor1用npu_bmmV2(grad,tensor2,[])，对tensor2用npu_bmmV2(grad.transpose(-2,-1),tensor1,[])。文档例两输入[68,5,75,16]、输出[68,5,75,75]，只展示sum.backward，无原生数值/梯度对照。

## 动态形状与性能

独立页面写动态场景“不支持Box transformation deltas”，是与本运算不符的措辞；固定实际源码注释明确动态shape下不支持**broadcast场景**。保留两份证据并按实际广播/梯度维度核对，不把疑似误植扩成任意动态shape均不支持，也不按torch.matmul通用能力推定本包装所有广播反向正确。

源码“比原生更快”没有实测依据，仍需按形状、dtype、转置、广播与前反向分别比较。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-matmul_transpose.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-matmul_transpose.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-matmul_transpose.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/matmul_transpose.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/matmul_transpose.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/_matmul_transpose.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/_matmul_transpose.py)（implementation）
