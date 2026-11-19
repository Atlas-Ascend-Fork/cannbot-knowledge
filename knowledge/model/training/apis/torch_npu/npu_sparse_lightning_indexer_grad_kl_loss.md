---
type: API
title: npu_sparse_lightning_indexer_grad_kl_loss：稀疏KL与sinks入口
description: 说明teacher D=512、稀疏索引和独立Indexer梯度，明确不支持图及950额外头数组合。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sparse_lightning_indexer_grad_kl_loss.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SparseLightningIndexerGradKLLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_sparse_lightning_indexer_grad_kl_loss.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sparse_lightning_indexer_grad_kl_loss.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/test_fake_tensor.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SparseLightningIndexerGradKLLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/core_tests/test_fake_tensor.py
  role: example
created_at: '2026-11-09T07:18:58Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# npu_sparse_lightning_indexer_grad_kl_loss：稀疏KL与sinks入口

## 固定版本与范围

前面的主线契约依据OpPlugin d84e9b1d6a558e5f27973cd4329f62968e46fdda产品页及同提交实现；后文另补固定发布差异、sinks分支和完整Fake范围。未执行上游实现、训练、图编译或设备实验。

## 接口与返回

```text
npu_sparse_lightning_indexer_grad_kl_loss(query, key, query_index,
    key_index, weights, sparse_indices, softmax_max, softmax_sum,
    scale_value, *, query_rope=None, key_rope=None,
    actual_seq_qlen=None, actual_seq_klen=None, layout='BSND',
    sparse_mode=3, pre_tokens=9223372036854775807,
    next_tokens=9223372036854775807, sinks=None)
    -> (d_query_index, d_key_index, d_weights, loss)
```

使用所选稀疏位置计算teacher与Indexer分布的KL，融合Indexer的Q/K及weights梯度。三份梯度shape/dtype随对应输入，loss是FP32[1]；文档返回段把loss对应到dI属于符号混写，不能把它当成每个评分的梯度矩阵。

## 两类头维与长度

teacher Q/K尾维512，Indexer Qindex/Kindex尾维128，可选teacher RoPE尾维64；Q/K/Qindex/Kindex同FP16或BF16，weights可FP32或同dtype。teacher Nk与Indexer Nki都1；Nq=32/64/128，Nqi=8/16/32/64。950另允许(Nq,Nqi)=(48,24)，这两个扩展数不与其他值任意配对。

稀疏索引INT32，形状(B,Sq,1,K)或(Tq,1,K)，需符合所选位置排序和teacher统计。主Attention max为FP16/BF16/FP32、sum为FP32，shape(B,1,Sq,Nq)或(1,Tq,Nq)。不能拿稠密Indexer预处理的两份统计代替teacher max/sum。

B=1..256，Sq最多8K、Sk最多128K，可不等长；layout为BSND/TND，TND需SymInt[]累计长度列表。产品表K列含1024/2048/4096/5120/6144/7168/8192及异常的3081；本卡不自行改成3072，使用明确无该歧义的范围，其他值另核对。950的泛化描述也不直接扩成任意shape已验证。

## 产品、模式和sinks

A2/A3训练系列及950支持，产品页明确**当前不支持图模式**；Meta注册不提升此范围。sinks为连续FP32(Nq,)，A2/A3不支持，950若提供则C++直接调用V2并传内部deterministic=True，没有同样的旧入口能力探测回退。

包装传确定性标志不等于所有反向实现均具有运行验证，也不把推理Indexer页“反向非确定性”的结论直接覆盖到本融合KL入口。对照目标版本确认实际语义、所选位置、teacher归一化及三份梯度，再比较峰值显存和步耗时。

## 发布歧义与主线新增范围

本节另核对发布OpPlugin dedc316708372c9a8bfde4527abd2a94b74840f5；它属于ascend_26_0_pt28组合，产品页仅列A2/A3训练系列，原型/Schema/Meta均没有sinks。主线d84e9b1d6a558e5f27973cd4329f62968e46fdda明确列950PR和950DT，不与只列DT的稠密KL接口混为同一产品范围。主线仍明确不支持图模式，B/S泛化文字不推翻这一限制。

发布参数表把sparse_indices和max/sum写为FP16/BF16，但同页调用示例的索引是INT32、max/sum是FP32；主线修正索引为INT32、sum为FP32，max保留FP16/BF16并新增FP32。发布规格表还把teacher Nk列32/64/128，调用示例却Nk=1，主线明确改为1。因此不把发布旧表的矛盾组合当成可靠的类型或GQA配方；部署应按对应固定版本的明确实现/调用验证。

主线将teacher D512与Indexer D128分别写清，旧表只写D512却说query和query_index不同；示例本来也用512/128。K表中的3081在两版均如此，不自行修成3072。950额外头数严格成对(48,24)，不能只选其中一个扩展值与原集合交叉组合。

## 稀疏位置和teacher统计的一致性

该入口消费上游选中的token索引，自己直接返回Indexer三梯度和单元素loss；不能把它当作会重算正确TopK索引的函数，也没有返回teacher Q/K、RoPE、sinks或统计量的梯度。loss返回段引用dI是符号混写，不能把FP32[1]当成逐评分dI矩阵或据此认证完整autograd链。

sparse_indices、teacher max/sum必须与同一前向的Q/K、RoPE、scale、长度和可见位置相符。两版示例将无效尾位置填-1；这不意味着可以任意负数、越界值或把重复token当作合法TopK。示例随机抽取索引而不是调用真实Indexer选择，可能无序或重复，不能据该示例推导排序、去重和选取正确性已验证。

文档以sinks修正后的目标分布与Softmax(Indexer评分)做KL，不能将sinks简单当作额外返回token、普通bias或补零项；实际归一化应与对应Attention前向一致。它与稠密KL的两套外部统计协议不同，本入口只收teacher max/sum，不能塞入稠密Indexer预计算的max/sum代替。

TND公开Schema要求SymInt[]累计边界。文档示例和Fake helper都固定B1并squeeze batch，循环中却直接把列表元素当每batch长度、分配也只用S1；这只展示单batch，不能作为多batch累计边界的实现模板。复核应分开总token数、相邻累计边界差分与每batch有效索引范围。

## sinks分支与检查的边界

两版C++都将缺失长度转换为空IntArrayRef、将缺失layout等恢复默认值，deterministic固定true。它仅检查teacher Q/K和存在的RoPE各为3/4维；主线有sinks时再查rank1，直接调用aclnnSparseLightningIndexerGradKLLossV2，无sinks仍走旧入口。发布只有旧入口，没有同等sinks参数，不能把None与有值跨版本互换。

主线包装没有完整验证sinks为连续FP32[Nq]或产品范围，文档这些条件仍必须满足，A2/A3仍传None。没有V2能力探测或回退逻辑，也没有“设置全局确定性即可补齐V2”的证据。固定true是调用参数，不是运行测得的确定性保证；同时本入口也不能直接继承另一个Indexer文档的反向非确定性描述。

两版Meta只分配与Qindex/Kindex/weights同形同dtype的三个梯度和FP32[1] loss；主线虽新增sinks形参，未验证sinks、索引类型/内容、统计量、长度或shape组合。Meta能返回期望shape不足以证明设备可执行或数值合理。

## Fake测试能证明的范围

在两个固定快照中检索本API，找到core_tests里的FakeTensor helper与测试，没有独立同名Eager数值测试。主线helper/方法完整范围为5373～5457/5459～5484，发布为4754～4834/4836～4860；只按这些范围审阅，不把整份core_tests视为已覆盖。

两版Fake方法都只跑TND、B1、FP16、主头64/Indexer头64、teacher D512/Indexer D128、K2048，断言四个输出的shape和dtype；主线另传sinks=True所构造的FP32向量。它没有比较梯度或loss数值，也不验证真实硬件是否支持sinks、48/24头、BF16、FP32 weights、BSND、非均匀batch或确定性。

helper和文档示例的teacher max/sum由随机正态数生成，sum可能非正，不能作为有效Softmax归一化分母；稀疏索引也为随机选择并填-1。Fake模式忽略这些数值，shape断言因此不能证明统计接线、稀疏选取或KL公式正确。weights的仿射正态缩放也不是严格限制在注释的[-0.05,0.05]区间。

实际验收应使用真实Indexer的有效索引和Attention的对应统计，分别验证稀疏位置、sinks归一化、三份梯度、loss和多batch边界，再测完整训练步的显存/耗时。本卡未执行上游、Fake测试、NPU或图，没有新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sparse_lightning_indexer_grad_kl_loss.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SparseLightningIndexerGradKLLossKernelNpuOpApi.cpp)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_sparse_lightning_indexer_grad_kl_loss.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sparse_lightning_indexer_grad_kl_loss.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/test_fake_tensor.py)（example）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SparseLightningIndexerGradKLLossKernelNpuOpApi.cpp)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/core_tests/test_fake_tensor.py)（example）
