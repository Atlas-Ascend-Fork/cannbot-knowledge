---
type: Guide
title: Inductor FlexAttention：回调、BlockMask、GQA与反向
description: 记录950PR/DT与PyTorch2.13文档的掩码复用、辅助输出及梯度边界。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/flex_attention/overview.md
  role: primary
created_at: '2026-11-09T15:23:53Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# Inductor FlexAttention：回调、BlockMask、GQA与反向

## 固定版本与计算

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的FlexAttention长说明，明确对应master及配套PyTorch2.13接口，产品950PR/DT；不由分支名推定当前安装包相同，也不回推其他版本。此处为Inductor的Triton-Ascend路线，未执行前向、梯度或性能实验。

默认softmax(Q@K.T*scale)@V，scale为Query尾维平方根的倒数。score_mod(score,b,h,q_idx,kv_idx)接收已缩放分数并返回标量；mask_mod(b,h,q_idx,kv_idx)返回BOOL，True参与注意力。create_block_mask构造区分全可见、部分可见与不可见块的元数据，完全不可见块可跳过，部分可见仍需逐元素处理。

## 形状与掩码复用

Q/K/V四维且同一NPU；K/V序列长度和head数一致，Q/K尾维一致，head维至少16。示例用相同FP16、(1,4,256,64)，不把示例dtype当穷举支持表。head数和head维按静态处理，动态batch/序列或mask布局可触发重编译和路径变化。

掩码与batch/head无关时B/H可为None；依赖它们时须给真实维度。只有规则、捕获Tensor内容及适用shape均一致时才复用BlockMask，变化后重建；序列范围须匹配，任意全掩码行应明确输出/梯度预期，不由因果样例每行有可见项推导自定义掩码也如此。

回调用Dynamo可捕获及NPU lowering支持的张量运算，组合条件用&/|，不使用依赖Tensor值的Python and/or/if。示例在编译区域外创建掩码，再fullgraph编译flex_attention、forward和backward。区域外且正整数序列长度、_compile=False的NPU create_block_mask可按Query分段以降低构造峰值；分段构造不等于无掩码内存开销。

## GQA、辅助输出和梯度

Q=(B,Hq,M,D)、K=(B,Hkv,N,D)、V=(B,Hkv,N,Dv)，Hq为Hkv整数倍时enable_gqa=True，输出(B,Hq,M,Dv)。return_aux=AuxRequest(lse=True)返回(out,aux)，从aux.lse访问；max_scores=True请求最大分数，不同时设置return_lse=True与return_aux。辅助输出可能改变可用kernel，按真实形状验证。

Autograd生成dQ/dK/dV，自定义可学习score偏置还受上游和NPU lowering限制；mask_mod捕获Tensor不支持梯度。kernel_options是底层调优，不能照搬CUDA值；关闭单项优化不等于退出torch.compile或回Eager。dK/dV任务列表的更窄batch/head/静态条件见[独立开关API](../../../../training/guides/flex_attention_backward_tasklist.md)。

首次编译、mask构造和稳态分别计时，预热并在测量边界同步NPU；块稀疏度、序列与head维及硬件决定性能，示例预期形状不是本次运行证据。环境在导入torch_npu和编译前设置，变更使用新进程。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/flex_attention/overview.md)（primary）
