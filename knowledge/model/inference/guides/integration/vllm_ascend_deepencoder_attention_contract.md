---
type: Guide
title: vLLM Ascend DeepEncoder注意力：Qwen2图文mask与相对位置FIA
description: 核对视觉CustomQwen2Decoder的inputs_embeds、图文可见性、HF cache与Attention接口，以及RelPosAttention的BNSD/PSE偏置；区分该局部decoder与普通vLLM请求调度/KV图。
aliases:
- AscendCustomQwen2Decoder
- AscendQwen2Model
- AscendQwen2Attention
- AscendRelPosAttention
- optimized_apply_rotary_pos_emb
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.parallelism
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/qwen2_decoder.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/rel_pos_attention.py
  role: implementation
created_at: '2026-11-03T06:23:41Z'
updated_at: '2026-11-03T06:23:41Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend DeepEncoder注意力：Qwen2图文mask与相对位置FIA

## 这是视觉模块局部decoder，不是普通serve的整模型替代

固定Main ceac1a2，完整静态阅读qwen2_decoder356行和rel_pos_attention48行。前者继承Native deepencoder2 CustomQwen2Decoder并重建HF Qwen2Model，后者继承deepencoder RelPosAttention。没有闭合Transformers/Native父类、模型注册或TorchNPU设备算子，没有执行上游/视觉模型/NPU/图/数值实验，保持draft/空平台。

Custom decoder构造参数重建Qwen2Config与Ascend层，随后删除self.model.embed_tokens。因此实际forward应从正确inputs_embeds进入，不能仅见input_ids参数仍在签名就推断删embedding后仍可查词表。普通AscendQwen2Model检查input_ids/inputs_embeds二选一；内部包装还在进入父forward前用inputs_embeds shape建立mask，实际调用更需满足embedding输入合同。

## 图文mask按token类型表达可见性

无token_type_ids时建标准下三角causal additive mask；类型0为image、1为text时，用矩阵乘构造：image看所有image，text看所有image，text到text只看causal下三角，image到text不可见。它是按类型建的全序列可见性，不按image item ID隔离不同图片，也不从padding mask推图像边界。

不可见位置用torch.finfo(dtype).min而非布尔mask；若提供二维attention_mask，再把其0 padding列转min加上。多个min相加可能形成更低值/非有限值，dtype、完全masked行和实际Attention接口需数值核验。其它维attention_mask在这个局部helper没有统一合并，不把任意4D输入mask当已消费。

包装只提供full_attention一项dict，内部HF model若有sliding层却需要sliding_attention键，不能仅由父支持sliding就判该包装组合已接通。mask的S来自当前inputs_embeds，不从past cache长度重建任意cross/prefix可见性；带历史KV的尺寸匹配需按真实调用验证。

## Q/K/V、RoPE与HF cache沿独立生命周期推进

AscendQwen2Model有use_cache且没有past时新建DynamicCache，缺cache_position时从已存长度起建立当前范围，缺position_ids再用其unsqueeze。若attention_mask不是dict才用Transformers create_causal_mask，并按has_sliding_layers补sliding mask；dict被原样视为已准备好，不验证所有layer key。

每层为norm→attention→residual add→norm→MLP→residual add，最后全局norm。Attention用各自q/k/v projection后view/transposed为head布局，cos/sin unsqueeze后分别npu_rotary_mul；position_ids参数不在这个旋转helper内重建cos/sin。HF cache.update接收sin/cos/cache_position返回扩展K/V，不是普通vLLM block table/slot mapping。

Attention接口缺省eager，否则按config._attn_implementation从ALL_ATTENTION_FUNCTIONS查，传当前mask、scaling、sliding_window与训练时dropout；不是这里强制所有配置走同一NPU FlashAttention。输出reshape/contiguous后o_proj，模型只在use_cache时返回past对象。RMSNorm的本地权重初始为ones，最终必须由模型加载覆盖正确权重，不以创建成功当checkpoint已接通。

## RelPosAttention使用另一套PSE语义

输入[B,H,W,C]经qkv变为[B,heads,H*W,D]。启用relative position时，Native add_decomposed_rel_pos得到H/W两部分，分别view成head布局后相加并展平成[B,heads,S,S] attn_bias；调用npu_prompt_flash_attention时作为pse_shift，input_layout=BNSD、scale_value=self.scale。不启用时省略pse_shift而保持同一接口。

这里没有另建causal mask、cache或block table，不应把前面的Qwen2图文causal规则塞到这一视觉Attention。输出按[B,heads,H,W,D]重排回[B,H,W,C]再proj；head整除、PSE实际形状/dtype和外部函数返回协议均需和加载模型核验。

新视觉适配优先记录真实类与HF/TorchNPU版本、inputs_embeds/token类型、image多item隔离预期、padding/完全mask行、past cache与位置、最终选中的Attention函数以及PSE布局。先比较有效token输出与cache推进，再讨论图/融合收益，本次没有执行这些验证。
