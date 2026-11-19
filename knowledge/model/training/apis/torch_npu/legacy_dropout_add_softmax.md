---
type: API
title: 旧加法Softmax-Dropout：概率、掩码和反向限制
description: 纠正1/prob公式和四维mask描述，保留融合形状门槛与不维护状态。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_dropout_with_add_softmax.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_dropout_with_add_softmax.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_dropout_with_add_softmax.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DropoutWithAddSoftmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DropoutWithAddSoftmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T20:42:31Z'
updated_at: '2026-11-09T20:42:31Z'
platforms:
- a2
- a3
---

# 旧加法Softmax-Dropout：概率、掩码和反向限制

## 固定版本与产品边界

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文、独立主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文及各自实现。发布归ascend_26_0_pt28，main不是与其他仓main自动配套的发行。

平台只按实际产品页；950新增项严格另列主线PR/DT，旧Atlas不自动映射新型号。计划废弃、不维护、schema注册及实际运行能力分别判断；stable不表示推荐新模型采用或运行verified。这里只静态阅读，未导入上游、运行设备、反向、数值或性能实验，底层Kernel算法不由框架包装引用视为全覆盖。


## 入口及形状

npu_dropout_with_add_softmax(self,x1,alpha,prob,dim)返回(mask,result_softmax,result_dropout)。两输入同shape(N,C,H,W)，H/W各取128/256/384/512，N*C被32整除，dim仅-1，alpha正负浮点均可。计划废弃且底层不维护，不能泛化到任意4D注意力或推导训练/eval自动状态。

逻辑加法为x1+alpha*self，再末维softmax和dropout。prob是丢弃概率，包装明确计算retain=1-prob并作为input_keep_prob；文档留下1/prob及“对self先掩码再加权”的文字相互冲突，不用它替代常规1/(1-prob)概率解释。文档prob>=1非法、0不丢弃，但局部包装没有完整概率检查，不扩为任意负值可用。

## 实际mask和生命周期

mask实际一维UINT8，长度round_up(numel,128)，不是文档同(N,C,H,W)的逐元素BOOL；与其他私有dropout的ceil(numel/128)*16分配也不同，不能混用。两版此helper固定seed=2、seed2=0并走secondary stream，recordStream绑定原流；这些源码常量不等于已验证跨版本随机序列或与其他NPU生成器状态完全相同。

## 反向与上层回退

实际backward对softmax_out与mask运行DropoutWithMulsAndSoftmaxGrad，第二份返回直接是传入grad。不能据名字或原生组合公式承诺任意输入的两路梯度相同。上层[contrib组合](contrib_add_softmax_dropout.md)还会根据形状和training决定融合或普通dropout回退，需分别核对状态、概率、内存及梯度，不能只比较forward某个随机输出。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_dropout_with_add_softmax.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_dropout_with_add_softmax.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_dropout_with_add_softmax.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DropoutWithAddSoftmaxKernelNpu.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DropoutWithAddSoftmaxKernelNpu.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
