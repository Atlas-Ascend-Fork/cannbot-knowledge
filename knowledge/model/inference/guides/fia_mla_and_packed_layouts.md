---
type: Guide
title: FIA MLA 与 packed 布局：RoPE、累计长度和输出轴
description: 按主线产品及D=128/512分开核对TND/NTD、分页长度、独立RoPE、Sink与布局文档冲突。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.long_context
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
created_at: '2026-11-09T09:42:58Z'
updated_at: '2026-11-09T09:42:58Z'
platforms:
- a2
- a3
- '950'
---

# FIA MLA 与 packed 布局：RoPE、累计长度和输出轴

## 版本与布局解释

本文依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的v1/v2页面和静态shape实现，范围为A2/A3与950PR/950DT的对应分支，不回推发布版或其他软件组合。目标是减少错误reshape和冗余拼接，不据layout名称宣称固定性能收益。

input_layout下划线前为Query逻辑输入、后为输出，不能把后缀当作KV物理存储。TND的T是请求Token总和，NTD为(N,T,D)；TND_NTD返回(N,T,D)，NTD_TND返回(T,N,D)，无需再套旧布局的view。NBSD输出在主线Meta/C++中明确为(N,B,S,D)；v1某些表行写成(B,N,S,D)，不能照抄。代码还识别NSD/BSH_BNSD等字符串，不等于所有产品公开支持。

## 长度与分页例外

非PA的packed Query/KV长度是非负、非递减的累计边界，必须提供Q/KV两组并按元素个数解释batch；A2/A3相关TND约束要求batch≤4096。例如请求长[3,5]对应累计[3,8]，不能直接传[3,5]。有PA时，Query仍按packed累计边界切请求，KV长度则是每个batch的独立实际长度，不能再次cumsum。

普通非packed布局中，长度列表为1时广播、长度≥B时取前B项，实际值不能越过对应S。A2/A3普通decode非TND时Query长度参数无效；950在无RoPE时无效，带RoPE和packed路径另按对应规则核对。不能用T=1或上层“decode”名字替代每请求Q_S的分支条件。

## 分离 RoPE 与 D=512 MLA

query_rope/key_rope成对出现，各自RoPE D=64，其余轴与相应Q/K一致；K/V physical KV cache还需与页表匹配。量化MLA有明确RoPE dtype特例，不能把普通浮点的“与Q/K同dtype”套到INT8+BF16 RoPE。

| 路径 | 明确条件 | 布局/分页与互斥 |
| --- | --- | --- |
| A2/A3 v1 D512 | Q heads∈{1,2,4,8,16,32,64,128}，KV head=1，sparse0/3/4 | 普通BSH/BSND/BNSD及NBSD输出、TND/TND_NTD；PA块16倍数≤1024；不带LSE、左padding、TensorList、PSE、prefix或量化 |
| A2/A3 v2 D512 | 同一Q/KV head集合，稀疏段增加9 | 不支持左padding/TensorList/PSE/prefix/空Tensor；INT8特化及其TND矛盾见全量化卡 |
| 950 v1 D512 | 普通浮点KV为ND | BSH/BSND/BNSD/TND；单Token sparse0无mask，多Token sparse0无mask或3有mask；普通布局仅用KV实际长度，TND两组必传 |
| 950 v2 D512 | 主线段Q_S为1..16，FP8全量化Q heads仅32/64/128，INT8列上述2幂集合，KV head=1 | FP8列BSH/BSND/BNSD/TND；INT8仅PA NZ并列BSH/BSND/TND及相应NBSD/NTD输出，不把两组layout取并集 |

A2/A3浮点NZ为(blocknum,KV_N,D/16,blocksize,16)，INT8为D/32与末维32；950 v1 ND范围和v2的INT8 PA NZ是不同约束。v2 950 D512稀疏段对Q_S>1明确只列mode3有mask，后面又泛列0/3；按前者保守限制，不能借泛述扩大多Token支持。

## D=128 与其他 packed 尺寸

A2/A3普通分离RoPE D128路径不支持左padding、TensorList、PSE、prefix和各类量化。无RoPE的TND常见Q/K/V D128，或Q/K D192而V D128/192；NTD及GQA/PA等分支对V D192另有限制，不能只看到“D≤512”就套用。v2还明确MHA同D64或128、Q/K192而V128，FP16 inner_precise0/1、BF16仅0，sparse0不带mask或3/4配压缩mask；该MHA PA仅BnBsH，block_size为16倍数≤1024。

950 D128 RoPE只列相应普通/TND布局（v2另列NTD/NTD_TND），不带PSE、prefix及量化。该产品段提到KV TensorList并要求key_rope的B等于列表长度、N/S与每项一致，不能由总表“禁止TensorList”外推否定特化，也不能把底层TensorList说明当作Python公共Schema接受list的证据：标准Python v1/v2 Schema均为Tensor Q/K/V。

## learnable_sink

v2 learnable_sink为BF16 ND、shape(Q_N,)，仅非量化，不与PSE、左padding、共享前缀或后量化组合。A2/A3仅TND/NTD_TND且V_D≤128；950仅列V_D为64或128。v1没有该输入；文档把sink能力列在v2，不表示v1可以仅改keyword使用。

## 图与验证边界

分页物理KV形状、RoPE类型、packed边界、scale轴、实际输出轴要成组核对；TND不自动意味着免除所有padding或KV页对齐。来源中的特定NTD吞吐观测不构成通用收益。本次只审阅文档与shape/分派代码，未运行NPU；GQA FP8的Eager限制、全量化产品矛盾与模式缺项见独立卡。

- [全量化路线](fia_quantized_attention_paths.md)
- [KV伪量化](fia_kv_antiquant_modes.md)
- [mask与LSE](fia_mask_prefix_and_lse.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（header）
