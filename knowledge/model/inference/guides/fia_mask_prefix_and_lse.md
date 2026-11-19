---
type: Guide
title: FIA mask、共享前缀与 LSE：窗口语义和占位边界
description: 区分sparse模式、行无效修正、v1前缀/左padding、950差异及主线真实输出占位，避免错误复用示例。
tags:
- task.optimization
- topic.attention
- topic.precision
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-09T09:42:58Z'
updated_at: '2026-11-14T01:59:28Z'
platforms:
- a2
- a3
- '950'
---

# FIA mask、共享前缀与 LSE：窗口语义和占位边界

## 固定版本与模式选择

依据OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 主线v1/v2。A2/A3与950PR/950DT只按具体段落消费，不回推发布配套；没有执行设备或性能实验。先确定每请求Q_S、RoPE、实际Q/KV长度与所需注意力范围，再配mode与mask。

| sparse_mode | 含义及pre/next作用 | mask |
| --- | --- | --- |
| 0 | mask=None时忽略pre_tokens/next_tokens，不自动因果；v1左padding亦有忽略窗口条件 | 有mask时为完整S1×S2区域 |
| 1 | 完整mask决定相关性，忽略pre/next | 必传完整mask |
| 2 | 左上对齐因果，忽略pre/next | 受支持的2048×2048压缩mask |
| 3 | 右下对齐因果，忽略pre/next | 同上；不等价于所有长短Q/K下的左上因果 |
| 4 | band，窗口与Q/K对齐共同决定有效区 | 同上，按pre/next配置 |
| 9 | v2 A2/A3的tree mask | 见后文产品及冲突限制 |

5..8尚未实现。Q_S=1且不带RoPE时sparse_mode无效，pre/next也不是普适的decode裁窗开关；模型示例传4不独自证明窗口真正生效。65535只可能覆盖示例的小序列，主线S上限达20M，不能称其为普适无限窗口。

## mask shape、dtype 与极性问题

mask为连续ND，BOOL/INT8/UINT8。A2/A3普通0/1模式列(1,Q_S,KV_S)、(B,1,Q_S,KV_S)、(1,1,Q_S,KV_S)；指定布局且无RoPE等条件下允许二维(Q_S,KV_S)，decode可(B,KV_S)。2/3/4的压缩shape为(2048,2048)及带前导1的变体，并非按长序列直接申请完整平方mask。

950建议prefill用(B或1,Q_S,KV_S)或相应4D，decode用(B,1,KV_S)/(B,1,1,KV_S)，S可向16/32对齐。PA时KV轴需覆盖页容量；prefix时还需覆盖有效prefix+KV。

文档一方面以参与区域“整行全1”定义行无效，另一方面v1因果示例使用tril(bool ones)，并附有双向注意力措辞，v2压缩mask段也称下三角。源码包装只转发，未在框架中实现mask极性，所读测试的有效长度mask不是直接传给本参数的mask，不能用它消除冲突。因此本页不复制该tril示例作为正确因果配方；应在目标CANN契约下用小Q/K参考验证极性、左上/右下对齐、窗口及全屏蔽行。

## inner_precise 与 PSE

inner_precise的bit0选择高精度0/高性能1，bit1开启行无效修正：0/1不修正、2/3修正；BF16/INT8不区分bit0，decode仅0/1。自定义mask可能出现整行无有效Key，应核对修正；来源也会对部分可推断无效行自动处理，不能把修正当成所有稀疏/量化组合均可运行的保证。修正可能降低性能。

PSE一般为与浮点Q对应的FP16/BF16，shape(B或1,Q_N,Q_S,KV_S)；全浮点FP16且带PSE强制高精度。A2/A3 decode要求D能被16整除，950浮点有不同对齐条目。950建议KV轴padding至32以改善性能；这是来源建议，并非本次测量。TND/MLA等路径有独立PSE互斥，不能将普通PSE支持平移。

## v1 共享前缀与左 padding

v1 key_shared_prefix/value_shared_prefix成对传入，batch固定1，N/D或H与KV匹配，K/V prefix长度相同；actual_shared_prefix_len为单元素长度，不能超过物理prefix S，prefix有效S+KV仍受原总长度上限约束。mask/PSE需覆盖拼接后的Key轴。不与PA、左padding、TensorList或QKV全INT8组合。v2没有共享前缀数据参数，签名中的prefix_dtype提示不意味着支持共享前缀。

左padding也只在v1有数据参数。Query路径Q_S>1且有实际Q长度，起点Q_S-padding-actualQ≥0，终点Q_S-padding≤Q_S；KV按对应公式定位，decode负的有效起点返回零，负KV padding按0处理。PA不支持左padding，A2/A3浮点Q+INT4 KV亦有互斥。不能用右padding的长度语义代替这些起终点计算。

## v2 tree mask 与冲突边界

mode9仅A2/A3，参数段要求MLA且Q/K RoPE均非空，每请求Q_S≤KV_S，无左padding/PSE/sharedPrefix，输出不为INT8。普通BSH/BSND/BNSD的mask为(B,Q_S,Q_S)，TND为各请求Q_S²拼成1D，而不是统一B×最大S²。

GQA NZ段又列mode9但同时禁止RoPE，与上述条件不相容。本页保留该差异，不把两段拼成GQA NZ+tree mask配方；950只列0..4，不能消费mode9。

## LSE 与稳定合并

请求LSE时主线Meta/C++对TND、NTD、TND_NTD、NTD_TND统一分配(T,Q_N,1) FP32，其余普通布局为(B,Q_N,Q_S,1)；输出为NTD并不意味着LSE也转成(N,T,1)。关闭LSE时主线标准v1/v2的Meta与C++均分配[0] FP32，文档却写[1]零占位；不能把它当有效LSE；发布实现已另核相同，具体复核依据见文末。

对具有有效LSE的块，稳定合并为m=max(lse_i)、w_i=exp(lse_i-m)、O=Σ(w_i O_i)/Σw_i，而非直接平均各块output。空块输出、全无效行与中性LSE需由实际分块协议明确，关闭LSE的占位绝不是中性权重。v1 A2/A3 D512 MLA不支持LSE，后量化也有Ring组合限制，不能只开flag跳过这些约束。

NPUGraph示例通过copy_更新捕获输入的内容、保留地址；改变窗口等标量配置重新捕获。示例存在不代表任意动态layout/shape/量化路径能重放，GQA FP8另有Eager限定。

- [MLA与packed布局](fia_mla_and_packed_layouts.md)
- [量化路径](fia_quantized_attention_paths.md)

## 发布v1后量化无效行的精确边界

以下仅绑定发布OpPlugin dedc316708372c9a8bfde4527abd2a94b74840f5。输出INT8、quant_offset2非None且非空时，文档逐batch列出拦截条件：mode0且mask非None，actualQ-actualKV-pre_tokens>0或next_tokens<0；mode3且actualKV-actualQ<0；mode4且pre_tokens<0或next_tokens+actualKV-actualQ<0。mode1/2没有该项条件。这里的长度是对应batch实际长度，不能直接将TND累计边界代入这些差值。

这些条件解释为何某些位置无参与计算的Key、带offset后量化会发生误差；inner_precise行无效修正不能当成绕过所有拦截的方案。来源建议在外部后量化，仍需核模型数值合同。主线将该段概括为“存在不参与计算的行时拦截”，没有列出以上全部公式；保留精确发布范围，不把简写当成已取消限制。

发布decode左padding段误用actual_seq_lengths描述KV，而同页KV参数、prefill公式与主线更完整说明使用actual_seq_lengths_kv；应按匹配版本KV实际长度及搬运起终点核对，不按这处变量名笔误生成调用配方。主线prefill的950 KV长度中英文也有差异：英文加入PA独立长度说明，中文只写TND前缀；分页时沿用专门约束，不能对真实KV长度重复cumsum。

完整复核两版相同C++/Meta后，关闭LSE均为FP32[0]，推翻文档[1]零Tensor的概述；有效LSE的shape与合并仍按本卡前节。框架包装不解释mask位极性，文档tril示例、2048压缩mask以及单行全1定义之间的冲突仍需对应CANN核验，未运行源码或增加verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
