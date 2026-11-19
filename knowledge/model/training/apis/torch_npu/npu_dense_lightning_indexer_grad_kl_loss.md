---
type: API
title: npu_dense_lightning_indexer_grad_kl_loss：稠密warmup与三路梯度
description: 说明teacher与Indexer两套统计、仅返回Indexer梯度及FP32单元素loss，限制主头数和D。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_grad_kl_loss.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DenseLightningIndexerGradKLLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_grad_kl_loss.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_grad_kl_loss.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_dense_lightning_indexer_grad_kl_loss.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DenseLightningIndexerGradKLLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_dense_lightning_indexer_grad_kl_loss.py
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

# npu_dense_lightning_indexer_grad_kl_loss：稠密warmup与三路梯度

## 固定版本与范围

前面的主线契约依据OpPlugin d84e9b1d6a558e5f27973cd4329f62968e46fdda产品页及同提交实现；后文另补固定发布差异、统计接线和完整测试缺口。未执行上游实现、训练、图编译或设备实验。

## 接口

```text
npu_dense_lightning_indexer_grad_kl_loss(query, key, query_index,
    key_index, weights, softmax_max, softmax_sum,
    softmax_max_index, softmax_sum_index, scale_value, *,
    query_rope=None, key_rope=None, actual_seq_qlen=None,
    actual_seq_klen=None, layout='BSND', sparse_mode=3,
    pre_tokens=9223372036854775807,
    next_tokens=9223372036854775807)
    -> (d_query_index, d_key_index, d_weights, loss)
```

用于Indexer的稠密warmup训练，不需要稀疏化teacher key/key_index。主Attention概率经跨头聚合和上下文归一化作为teacher，计算其与Softmax(Indexer score)的KL及Indexer梯度；不是直接计算所有主Attention输入的反向。

Q/K/Qindex/Kindex同FP16或BF16，weights可FP32，非FP32时与其余匹配。两套统计均FP32且不能交换：主Attentionmax/sum形状(B,Nk,Sq,G)或(Nk,Tq,G)，G=Nq/Nk；Indexer统计来自[稠密预处理](npu_dense_lightning_indexer_softmax_lse.md)，为(B,1,Sq)或(1,Tq)。scale_value必填，不把默认的其他算子scale混入teacher计算。

## 规格与返回

产品页A2/A3训练系列与950DT：B=1..256，Sq/Sk=1..128K，可不等长；主Attention Nq/Nk均为32/64/128且**Nk=Nq**，不能依据G定义推导任意GQA。Indexer Nqi=8/16/32/64，Nki=1。四份Q/K尾维均128，可选RoPE尾维64，不能与稀疏KL路径的teacher D=512直接交换。

layout为BSND/TND，TND需SymInt[]累计长度列表；sparse_mode只3，pre/next按默认最大INT64。三份梯度的shape/dtype分别随Qindex、Kindex、weights；C++/Meta将loss分配为FP32[1]，不是未归约的逐token损失或0维标量。

## 集成验证

参考必须统一teacher/Indexer两套Softmax的mask、RoPE、长度和scale，并验收三份梯度及loss；仅loss数值合理不证明梯度接线正确。本文未补造自动反向注册、图支持或训练显存数字，集成步骤见[训练统计与阶段契约](../../guides/torch_npu_lightning_indexer_training_contract.md)。

## 发布约束与两套概率统计

本节另核对发布OpPlugin dedc316708372c9a8bfde4527abd2a94b74840f5，属于ascend_26_0_pt28组合；发布只列A2/A3训练系列，主线d84e9b1d6a558e5f27973cd4329f62968e46fdda新增950DT。主要算法、Schema、输出分配没有因产品页扩展而变成任意新平台/主头数配方，主线配套未知，950PR不由DT推导。

teacher概率需从主Attention的同次Q/K、可选RoPE、scale、mask和长度对应的max/sum重建；Indexer概率需从ReLU(Qindex@Kindex^T)、weights跨头求和及同样可见位置对应的另一套max/sum重建。两者统计有不同轴结构，不能交换，也不能直接拿其他FA返回的尾轴8统计不经确认就接入。当前主头Nq=Nk，因此G=Nq/Nk实际为1，不因公式含G就开放任意主Attention GQA。

文档将跨头求和后的处理称L1正则化，测试参考实际是逐头概率相加后乘1/Nq；在每个head概率已正确归一化时，这得到按head平均的目标分布。它不是新增一个权重L1惩罚项。若输入max/sum不对应真实分数，则重建结果未必归一化，不能据softmax(Indexer)-teacher就断言是真实KL梯度。

公式段称Top-k value，但该接口是稠密warmup：输入全量key/key_index，输出三个Indexer梯度及loss，没有返回TopK索引，也不要求调用者先按推理Indexer选token。与统计预计算接口组合时，还须满足它的每batch Sq<=Sk和累计Q/K边界相容要求，不能只用本页“可不等长”的一句忽略前置接口范围。

## 显式梯度返回与实现分工

两版Schema均以SymInt[]?接收TND累计边界，scale_value为必填float，pre/next默认最大INT64；原型中的2^63-1不可照抄为Python异或运算。C++将缺省layout恢复BSND、缺省sparse_mode恢复3，只额外检查teacher Q/K以及存在的RoPE各为3或4维，随后调用aclnnDenseLightningIndexerGradKLLoss；没有完整检查Index Q/K、两套统计的shape/dtype、长度递增、RoPE配对或头数约束。

Meta甚至只按Qindex/Kindex/weights分别分配同形同dtype的三个梯度、FP32[1] loss，不验证teacher或统计量。通过Meta不意味着统计量正确，随机max和全1 sum也不会因此获得合法概率语义。可选RoPE的尾维64与输入同类型，应与teacher前向一致；测试里总是拼接有值的RoPE，不能证明None或单边RoPE路径已验证。

这里直接返回d_query_index、d_key_index、d_weights。不能把返回的loss当成已自动接回原网络各参数的证明；主Attention Q/K、RoPE和两个统计输入的梯度也不在返回值中。训练集成需要核验这些显式梯度如何接回Indexer分支，以及外层loss权重/缩放如何对应。loss为单元素FP32 Tensor，既不是逐token loss，也不因设备上有值就代表完整autograd链路已验证。

## 测试参考和示例的限制

两固定测试文件各213行、完整71行发布差异仅空白和末尾换行。唯一Eager方法无条件skip，提示旧CANN但没有可核验的最低CANN版本；它只使用BSND、B1、FP16、主头64、Indexer头64/1、Sq128/Sk256、D128/Dr64、scale1。没有TND变长、BF16、FP32 weights、None RoPE、950DT、图、模型训练或性能实测，本卡未执行。

测试把teacher及Indexer的max随机生成、sum全设1，Indexer统计也没有调用真实预计算生成；文档调用示例仅Indexer那一套来自预计算，teacher仍随机max/sum1。这些例子可展示参数接线意图，不能作真实归一化分布的数值或显存验收。随机很大的max还可能让重建exp下溢、梯度接近零，单凭小误差不能排除统计量接错。

CPU参考先将RoPE拼接到teacher Q/K再乘显式scale，采用右对齐因果mask；Indexer侧则ReLU后乘weights并跨头相加，不额外复用teacher scale。KL参考对log输入做1e-8下限裁剪、乘的仍是原teacher概率并全量求和；这与未裁剪的符号公式有数值边界差别，不能把参考的裁剪阈值宣布成所有后端保证。

参考以sy-p求评分梯度，ReLU<=0处梯度为0，再计算dW/dQindex及跨共享head累计的dKindex。它把dW也转成query dtype、把中间ReLU梯度先转FP16再做矩阵乘，因此当前样例没有验证允许的FP32 weights/dW精度，也不能拿纯FP32数学参考要求逐位一致。

复核应先用真实teacher和Indexer统计重建两个归一化分布，按相同mask/RoPE/scale验证loss与三梯度；加入非均匀累计长度、不同weights类型和目标产品，再检查模型训练参数更新及峰值显存。C++/Meta分配和被跳过测试不算运行验收，本卡无新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_grad_kl_loss.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DenseLightningIndexerGradKLLossKernelNpuOpApi.cpp)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_grad_kl_loss.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_grad_kl_loss.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_dense_lightning_indexer_grad_kl_loss.py)（example）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DenseLightningIndexerGradKLLossKernelNpuOpApi.cpp)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_dense_lightning_indexer_grad_kl_loss.py)（example）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
