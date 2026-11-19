---
type: API
title: npu_fused_linear_online_max_sum：词表分片的局部统计
description: 说明 MatMul 与损失前处理的六输出、bit mask 和性能/显存分支，不把局部量直接当全局结果。
tags:
- task.lookup
- topic.compute.composite
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_linear_online_max_sum.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_linear_online_max_sum.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedLinearCrossEntropyLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_linear_online_max_sum.py
  role: example
created_at: '2026-11-09T06:21:37Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# npu_fused_linear_online_max_sum：词表分片的局部统计

## 固定来源

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口页和同提交 Schema。产品、模式和参数范围以本卡明确限定为准，不回推发布快照或推定主线软件栈配套；未执行算子或NPU实验。

## 接口与六输出

```text
npu_fused_linear_online_max_sum(input, weight, target,
    vocab_start_index, vocab_end_index, return_logits=False)
    -> (logits_max, sum_exp_logits, predicted_logits,
        target_mask, masked_target, vocab_parallel_logits)
```

input=(B,H)、weight=(V_local,H)，同FP16/BF16、ND，H≤65534；target=(B,)、INT32/INT64，文档支持空Tensor。先input@weight.T，再生成**本分片**的行最大值、相对局部最大值的exp和与目标logit，三者均FP32、shape=(B,)。

target_mask为UINT8 packed bits，长度ceil(B/8)，每bit表示本行目标不在当前词表区间，补齐位置置1；不是每token一字节。masked_target与target同dtype、长度B，域内转局部索引，域外为0。

return_logits默认False走省显存分支，最后一槽为None；True走文档的高性能分支，返回(B,V_local)且dtype同input，换取更大中间量占用。不能把空logits槽用于后续softmax输出。

## 区间与通信边界

文档公式以target>end作为域外条件，end是包含端点；start≥0、end≥start。但参数段还把边界与max(target)-1关联，示例也未提供完整分片通信，不能据它生成适用于任意标签分布的集成代码。实际分片边界与weight行映射须按相应实现核实，不能把惯用的半开区间无条件照搬。

这是通信前的局部计算；全局最大值、分母及目标logit需以一致参考点合并后再交损失接口，见[词表并行集成检查](../../guides/torch_npu_vocab_parallel_loss_contract.md)。本接口950产品表不意味着下游所有配套接口也在950列明支持。


## 验证

在相同输入和计算口径下比较参考输出，核对每个中间量的shape/dtype、原地关系及有效性；训练覆盖梯度与多步调用，再测稳态时间和内存。单次导入或构造成功不代表该模式已验证。

## 局部参考点和区间例子的限度

本地三份FP32统计分别为m=max(z)、s=sum(exp(z-m))和目标所在分片上的p=z_target-m；域外p按公开公式为0。它们必须经同一全局参考点修正后才能进入损失阶段。打包mask的尾部补1有公开说明，但bit顺序未在公式中确定，不自行生成一套可移植的位布局。

两种语言的参数段均把词表边界与max(target)-1关联，而公式又把end作为包含端点；示例weight有256行却使用end=64，未形成完整词表所有权映射。这些材料不足以导出通用分片代码，不能用示例范围代替真实的weight行到全局token的对应关系。

主线C++在return_logits=False时返回未定义的第六槽，测试明确检查为None；True才分配同input类型的(N,V_local)矩阵。其余输出按input首维分配，masked_target类型随target。包装没有独立检查所有形状、区间或空输入，公开支持空Tensor不等于所有错误组合都由包装提前诊断。

## 产品和测试证据

主线公开A2/A3及950PR/DT，本卡没有将主线配到发布软件栈。测试只检查六项shape、dtype及None，并未校验统计数值、packed mask、分片边界或真实通信。测试文件中的词表区间也不能充当完整分布式交叉熵的黄金参考。

没有在本卡固定Meta及自动求导声明文件中找到本接口同名条目；显式调用包装存在，不表示状态保存、HCCL和整个训练框架集成均已交付。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_linear_online_max_sum.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_linear_online_max_sum.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedLinearCrossEntropyLossKernelNpuOpApi.cpp)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_linear_online_max_sum.py)（example）
