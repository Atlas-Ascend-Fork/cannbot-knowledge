---
type: API
title: 旧MultiHeadAttention融合接口：八输出和压缩掩码
description: 区分nn模块与19参数低层入口，纠正keep概率及输出dtype描述。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T20:42:31Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# 旧MultiHeadAttention融合接口：八输出和压缩掩码

## 固定版本与产品边界

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文、独立主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文及各自实现。发布归ascend_26_0_pt28，main不是与其他仓main自动配套的发行。

平台只按实际产品页；950新增项严格另列主线PR/DT，旧Atlas不自动映射新型号。计划废弃、不维护、schema注册及实际运行能力分别判断；stable不表示推荐新模型采用或运行verified。这里只静态阅读，未导入上游、运行设备、反向、数值或性能实验，底层Kernel算法不由框架包装引用视为全覆盖。


## 参数和形状协议

npu_multi_head_attention接Q/K/V、三个投影weight、attn_mask、out_proj_weight、四个bias、可选dropout_mask、head数/head_dim、src_len/tgt_len、dropout_prob和softmax_use_float。bias/mask在两个schema可空但必传，其他Tensor文档列FP16。head数、head_dim、src_len、tgt_len都必须正且16倍数。

样例使用二维Q为(B*tgt_len,H*D)、K为(B*src_len,H*D)，value样例用tgt_len但实际value_res按src_len分配；src/tgt相同的示例不能证明交叉注意力中任意V长度都合法。局部batch=Q.rows//tgt_len，没有完整整除/全张量形状校验，不能把检查通过当全协议有效。

## 八输出和概率

返回y、dropout_mask、query_res、key_res、value_res、attn_scores、attn_res、context。y/context为(Q.rows,H*D)，Q_res为(B,H,tgt,D)，K/V_res为(B,H,src,D)，scores/attn_res为(B,H,tgt,src)。实际dropout_mask为UINT8一维长度B*H*tgt*src/8，不是页面说的FP16；softmax_use_float=True时scores实际FP32，其余按Q的options/format分配，不是全部FP16。

文档dropout_prob误称keep probability，forward/backward实际均传keep_prob=1-dropout_prob，与p0样例一致。反向只在p>0时消费mask，并返回四投影权重、Q/K/V及四bias的11份梯度，bias_grad_mask由是否传bias生成；不能从19参数入口名推断普通nn.MHA二元组或任意缓存/因果mask能力。

接口计划废弃且底层不维护，和[contrib类](contrib_multihead_attention.md)的融合开关/Hook、[原生模块范围](../../guides/torch_npu_native_attention_modules.md)分别核验。本卡未执行梯度或精度实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_multi_head_attention.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_multi_head_attention.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_multi_head_attention.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MultiHeadAttentionKernelNpu.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MultiHeadAttentionKernelNpu.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
