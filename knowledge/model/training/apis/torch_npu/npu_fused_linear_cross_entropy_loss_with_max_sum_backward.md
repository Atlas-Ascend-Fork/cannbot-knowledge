---
type: API
title: npu_fused_linear_cross_entropy_loss_with_max_sum_backward：两种反向路线
description: 说明 packed mask、词表分片大小及 softmax 缓存与重计算的互斥输入关系。
tags:
- task.lookup
- topic.compute.composite
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedLinearCrossEntropyLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_linear_cross_entropy_loss_with_max_sum_backward.py
  role: example
created_at: '2026-11-09T06:21:37Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# npu_fused_linear_cross_entropy_loss_with_max_sum_backward：两种反向路线

## 固定来源

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口页和同提交 Schema。产品、模式和参数范围以本卡明确限定为准，不回推发布快照或推定主线软件栈配套；未执行算子或NPU实验。

## 接口和维度

```text
npu_fused_linear_cross_entropy_loss_with_max_sum_backward(grad,
    input, weight, target_mask, masked_target, label_smoothing=0.0,
    logits_max=None, sum_exp_logits=None, softmax=None)
    -> (input_grad, weight_grad)
```

grad为一维FP32、长度B；input=(B,H)、weight=(V_local,H)，同FP16/BF16/ND，V_local≥128。target_mask是UINT8的一维packed bit数组，长度*8≥B；masked_target为INT32/INT64、长度B。label_smoothing仅0。

softmax给定时为二维FP32，走高性能分支，logits_max/sum_exp_logits不生效；softmax=None走省显存重计算分支，必须同时提供一维FP32的全局logits_max和sum_exp_logits。不能把一个局部统计配上全局另一项，或把空Tensor占位当有效softmax。

返回input_grad=(B,H)、weight_grad=(V_local,H)，dtype同input。文档某公式将weight转置方向写得与shape不符，卡片按接口维度关系描述，不复制有冲突的矩阵公式。input_grad仍可能需要训练框架在词表并行组进行归约，显式梯度算子返回不等于已完成所有分布式反向通信。

- [前向通信前统计](npu_fused_linear_online_max_sum.md)
- [消费全局量的损失阶段](npu_fused_cross_entropy_loss_with_max_sum.md)


## 验证

在相同输入和计算口径下比较参考输出，核对每个中间量的shape/dtype、原地关系及有效性；训练覆盖梯度与多步调用，再测稳态时间和内存。单次导入或构造成功不代表该模式已验证。

## 两条反向路线的实现边界

主线包装按input、weight分别分配相同shape及input dtype的两份梯度，并把softmax、max/sum等可选项原样交底层；没有在C++中验证所有配对、形状及统计一致性。公开高性能路线的softmax为FP32(N,V_local)，重计算路线的max/sum为FP32(N,)，两条路线不能靠存在一个未定义或占位槽来混合。

公开高性能公式中的grad_softmax乘weight.T与weight=(V_local,H)不相容；按维度应由(N,V_local)梯度与(V_local,H)权重形成(N,H)。公式把softmax写成赋值更新，也不足以证明输入有原地别名契约。target_mask是packed bits，公式中的view(-1)是逻辑描述，不能直接当作可执行的长度N布尔展开。

主线公开A2/A3及950PR/DT，整条流水仍受损失阶段只列A2/A3约束。三份测试中的反向用例以随机softmax或max/sum调用，只检查两份梯度的shape/dtype，没有与真实交叉熵梯度比较，也没有多rank input_grad归约。固定derivatives中未找到这组三接口的同名声明，不把显式backward等同普通loss.backward已自动串联。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedLinearCrossEntropyLossKernelNpuOpApi.cpp)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_linear_cross_entropy_loss_with_max_sum_backward.py)（example）
