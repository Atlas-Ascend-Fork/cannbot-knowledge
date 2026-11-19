---
type: API
title: npu_dense_lightning_indexer_softmax_lse：稠密评分的max/sum预计算
description: 说明训练Indexer稠密KL的前置统计、FP32输出和累计长度列表，区分max值与索引。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_softmax_lse.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DenseLightningIndexerSoftmaxLseKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_softmax_lse.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_softmax_lse.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_dense_lightning_indexer_softmax_lse.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DenseLightningIndexerSoftmaxLseKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_dense_lightning_indexer_softmax_lse.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-09T07:18:58Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# npu_dense_lightning_indexer_softmax_lse：稠密评分的max/sum预计算

## 固定版本与范围

前面的主线契约依据OpPlugin d84e9b1d6a558e5f27973cd4329f62968e46fdda产品页及同提交实现；后文另补固定发布差异、完整测试和统计重建。未执行上游实现、训练、图编译或设备实验。

## 接口与统计含义

```text
npu_dense_lightning_indexer_softmax_lse(query_index, key_index,
    weights, *, actual_seq_qlen=None, actual_seq_klen=None,
    layout='BSND', sparse_mode=3,
    pre_tokens=9223372036854775807,
    next_tokens=9223372036854775807) -> (max_index, sum_index)
```

先计算Indexer的QK、ReLU与权重跨头求和及mask；返回每query评分的最大值m及sum(exp(score-m))。max_index中的index指Indexer分支，不是argmax位置；它与sum_index一起供[npu_dense_lightning_indexer_grad_kl_loss](npu_dense_lightning_indexer_grad_kl_loss.md)使用，不能把两者当完整概率矩阵。

## 类型、形状与长度

Qindex/Kindex为同FP16或BF16 ND，weights为FP32或与二者同dtype。BSND下Qindex=(B,Sq,Nqi,128)、Kindex=(B,Sk,1,128)，weights=(B,Sq,Nqi)；TND下去掉batch轴并使用累计token维。B=1..256，Sq/Sk=1..128K，Nqi仅8/16/32/64，Kindex头数1。

C++和Meta确认两输出均FP32：BSND为(B,1,Sq)，TND为(1,Tq)。最后没有额外G轴，不可直接套主Attention统计shape。

actual_seq_qlen/klen在TND必传，为SymInt[]/Python整数列表的累计边界，**不是**推理Indexer的INT32 Tensor长度入参。每batch Q长度不超过K长度，累计边界也须相容。sparse_mode只3，pre/next按文档默认最大INT64使用。

## 显存优化边界与验证

产品页确认A2/A3训练系列、950DT，目标是与稠密KL接口拆分统计以优化显存，不从“只有两个统计输出”推定底层没有任何临时空间或必然降低特定模型峰值。没有依据Meta注册新增全部图后端支持保证。

用相同mask、长度、精度和weights建立稳定Softmax参考，比较m、归一化分母和后续KL。统计必须来自同一次Indexer评分；换输入、mask或位置编码后不能沿用旧值。

## 发布来源和统计量重建

本节另核对发布OpPlugin dedc316708372c9a8bfde4527abd2a94b74840f5；它属于ascend_26_0_pt28组合，产品页仅A2/A3训练系列，主线d84e9b1d6a558e5f27973cd4329f62968e46fdda另列950DT。主线配套未知，不由发布实现同名推导950PR或发布950训练支持。

两版公式与统计输出一致：先逐Indexer头计算ReLU(Qindex@Kindex^T)，乘该query/头的weights，再跨头相加并施加AttentionMask，最后沿key token取max与稳定exp求和；weights为FP32时也不把ReLU移到加权求和之后。接口没有额外scale_value参数，不能自行套主Attention的1/sqrt(D)并仍复用原统计量。

这些输出是最大分数m和归一化分母s，不是概率、argmax或已经取log的LSE。重建每项概率为exp(score-m)/s，合并成log归一化值才是m+log(s)；后续稠密KL接口仍分别消费原m/s。更改Q/K、weights、mask、布局或长度后应重算，不能只因shape相同就复用旧统计。拆分统计的显存优化是来源给出的意图，实际峰值、工作空间和训练吞吐仍须整链测量。

## 累计边界与包装代码

两固定Schema都将actual_seq_qlen/klen声明为SymInt[]?，layout/sparse_mode/pre/next为可选标量；重复的同名声明也保持该类型，不构成Tensor长度重载。TND示例使用[S1,2*S1,...]和[S2,2*S2,...]，不含起始0；每batch长度由相邻边界相减，最后一项对应总token数。文档同时要求各位置累计Q<=累计K、各batch实际Sq<=Sk，仅比较最后总长度不够。

发布文档原型的2^63-1是数学写法，不能在Python中照抄成异或表达式；实际Schema/C++缺省为9223372036854775807，主线示例改为2**63-1。这里不由pre/next参数的存在推导任意稀疏模式，公开sparse_mode仍仅3。

两版C++仅额外检查query/key各为3或4维，然后按layout=TND分配[Kindex头数,Tq]，其他字符串分支按[B,Kindex头数,Sq]分配，最终调用aclnnDenseLightningIndexerSoftmaxLse；没有完整检查layout枚举、Q/K/weights dtype组合、128维、head数、长度必填/递增和mask。Meta更只分配两个FP32张量。由于合法Kindex头数为1，输出才简化为[1,Tq]或[B,1,Sq]；不能从较宽分配代码推广多KV head支持或非法layout可用。

## 被跳过测试的覆盖限度

主线测试156行，发布同长，完整52行差异仅空白和文件末尾换行；BSND与TND两个方法都被无条件skip，提示CANN版本过旧，但没有给出已验证最小CANN版本。BSND为BF16、B20/Sq512/Sk2048/Nqi32/Nki1/D128；TND为BF16、B2同长度。未执行FP16、FP32 weights、950DT、各head数、窗口、图、显存或性能测试，无新增verified。

CPU参考将模式3设为右对齐因果边界：第i个query屏蔽key位置大于Sk-Sq+i的分数；稳定max和exp求和沿key轴得到。它先按累计边界切片，但输出预分配用第一个batch的Sq，最后reshape又用最后batch的Sq，只对当前各batch等长样例成立，不能拿它验证一般变长输入。

TND测试还创建INT32 Tensor累计边界并搬到NPU后传入，和SymInt列表的公开Schema不一致；未执行的skip源码不能证明设备Tensor长度重载有效。测试最终把输出全部flatten后比较，不能独立检查布局轴顺序。因此模型复核应使用Schema要求的累计整数列表，按每batch不同长度和不同weights逐项核对原输出shape、m与s，再接稠密KL及梯度，不能只比较flatten后的统计。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_softmax_lse.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DenseLightningIndexerSoftmaxLseKernelNpuOpApi.cpp)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_softmax_lse.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_softmax_lse.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_dense_lightning_indexer_softmax_lse.py)（example）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DenseLightningIndexerSoftmaxLseKernelNpuOpApi.cpp)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_dense_lightning_indexer_softmax_lse.py)（example）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
