---
type: API
title: contrib MultiheadAttention：融合开关、特殊forward与未消费参数
description: 保存默认返回空元组、私有融合配置及缓存Dropout依赖，避免按原生MHA直接替换。
tags:
- task.lookup
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-MultiheadAttention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-MultiheadAttention.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-module-MultiheadAttention.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/multihead_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/multihead_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_multi_head_attention.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_multi_head_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_multi_head_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MultiHeadAttentionKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MultiHeadAttentionKernelNpu.cpp
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# contrib MultiheadAttention：融合开关、特殊forward与未消费参数

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 构造与前向协议

构造为`MultiheadAttention(embed_dim,num_heads,kdim=None,vdim=None,dropout=0.,bias=True,add_bias_kv=False,add_zero_attn=False,self_attention=False,encoder_decoder_attention=False,q_noise=0.,qn_block_size=8)`。kdim/vdim未配取embed_dim；embed_dim必须被num_heads整除，self_attention要求三维相同。源码明确无动态shape支持，独立页没重复不表示解除限制。

forward除query/key/value，还必需bsz、tgt_len、s_len，另收key_padding_mask等；**不是torch.nn.MultiheadAttention的原样调用签名**。两固定410行实现逐字节相同：私有_MHAConfig.use_fussion_mha默认False，未先set_fussion时forward直接返回(None,None)。开启后返回(attn[0],None)，与页面笼统Tensor返回不同。

## 融合路线实际使用的内容

实际src_len由key.size(0)//bsz推算，调用npu_multi_head_attention传四个投影权重/偏置、key_padding_mask、缓存dropout mask、head数/head_dim、src/tgt长和dropout概率。s_len、attn_mask、incremental_state、need_weights、static_kv、before_softmax、need_head_weights等虽在签名中却未在这段forward消费；不能据接参成功承诺因果mask、增量缓存或返回注意力权重。

dropout用NpuCachedDropout，缺掩码/训练状态见[缓存API](contrib_cached_dropout.md)，仅构造模型并不完成Hook/预热。示例私有set_fussion拼写是当前实现身份，不升格跨版本公共接口。

## 量化噪声及辅助路径

_quant_noise对Linear/Embedding/Conv注册训练前Hook，要求相应输入或卷积块维度整除qn_block_size，并按1/(1-p)更新weight.data；但融合路线直接传投影weight，没有调用投影Module.forward，不据q_noise参数保存在对象上认定该Hook已触发。它也不提供完整量化/检查点恢复流程。

辅助transpose_for_scores引用未在本类初始化的属性，buffer方法依赖未定义的get/set_incremental_state，forward又未调用这些路径，不当作完整增量推理能力。私有开关、输入layout、数值、梯度与运行时能力需独立验收，未运行设备。

## 融合底层返回与概率核对

[低层19参数API](legacy_multi_head_attention.md)实际把dropout_prob转为1-p，八输出里mask为UINT8、启用softmax_use_float后scores为FP32，不能按旧页面“所有输出FP16”传递给后续模块。融合开关、缓存mask准备和底层dtype/shape分别验收。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-MultiheadAttention.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-MultiheadAttention.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-module-MultiheadAttention.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/multihead_attention.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/multihead_attention.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/__init__.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/__init__.py)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_multi_head_attention.md)（primary）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_multi_head_attention.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_multi_head_attention.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MultiHeadAttentionKernelNpu.cpp)（implementation）

- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MultiHeadAttentionKernelNpu.cpp)（implementation）
