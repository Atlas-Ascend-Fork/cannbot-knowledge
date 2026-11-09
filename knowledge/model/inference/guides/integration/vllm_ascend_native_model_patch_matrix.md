---
type: Guide
title: vLLM Ascend 模型补丁差异：MoE工厂、草稿中继与视觉输入
description: 接新模型时按DeepSeek/Eagle3、Qwen3-VL/DFlash、Kimi、MiniMax、Step3.5和GLM模板核对Native类覆盖、权重/rope/FP32路由、PP辅助状态及实际工厂映射。
aliases:
- _ascend_FusedMoE
- _adapt_eplb_router
- RoutedExpertsCapturer.capture
- _patched_eagle3_llama_init
- precompute_and_store_context_kv
- patch_eagle3_pp_aux_propagation
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.speculative_decoding
- topic.multimodal
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_fused_moe.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_glm53_reasoning.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_minimax_m2_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_mla_prefill_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_deepseek_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_eagle3_init.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_eagle3_pp_aux.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_fused_moe.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_kimi_k25.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_minimax_m2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_qwen3_dflash.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_qwen3vl.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_routed_experts_capture.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_step3p5.py
  role: implementation
created_at: '2026-11-03T05:21:15Z'
updated_at: '2026-11-03T05:21:15Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 模型补丁差异：MoE工厂、草稿中继与视觉输入

## 阅读方式与适配入口

固定 Main ceac1a2 的14个补丁经整文件AST投影读取全部程序语句，保留分支/调用/赋值，未逐字审阅注释/docstring，未导入/执行上游。它们多在模块导入时全局覆盖Native类，单个checkpoint在模型表出现不证明这些补丁与任意Native release兼容；要保存实际配对提交、加载后的符号identity、模型配置与选路。

## MoE Factory与EPLB不能只替换runner类

platform补丁缓存原FusedMoEFactory并包装：dynamic_eplb或expert_map_path可强制启用EPLB，配置与Native非零冗余专家数冲突会拒绝；逻辑/物理专家数分开。自定义routed_experts_cls经缓存的动态多继承适配，已是AscendRoutedExperts子类则保留，MRO与构造协议仍需检查。

没有自定义router时由Ascend factory按top-k、grouped路由、score correction、hash/tid2eid及vision bias等构造；apply_routed_scale_to_output为真时router scale设1避免重复缩放，最终runner仍接原routed_scaling_factor。MRv2才将router EPLB state转Ascend类型，并严格检查_apply_eplb_mapping签名为(self,topk_ids)，物理映射表未初始化拒绝。不能把一个enable_eplb布尔推广为所有runner有同一映射阶段。

文件替换fused_moe package与layer模块的工厂，并扫描已加载vllm.model_executor.models中仍等于原工厂的引用；worker/patch_fused_moe仅导入该平台模块以触发共享接线，无另一套工厂。参数hash接收但局部未消费，不按签名推可用；tid2eid兼容值与hash_indices_table实际传递要各核。

RoutedExpertsCapturer另按DP布局区分全拼接、当前DP、max-token padding或TP分片，TP-sharded通信类型仅ALLTOALL/MC2/FUSED_MC2。无DP metadata时必须有dispatch num_tokens/padded_num_tokens才能重建总行，拒绝从本rank shard长度反推偶数split；ALLTOALL很小batch至少TP行。最终只写当前DP真实token前缀，超buffer层号跳过。捕获路由统计不执行专家映射正确性或负载均衡收益验证，collective仍需全组同序。

## 模型族必须保留的差异

| 来源族 | 已读代码的适配合同 | 不能从局部补丁推出的结论 |
| --- | --- | --- |
| GLM-5.3 reasoning | 通过chat_template中[gMASK]<sop>、Reasoning Effort和tool/arg标记且无enable_thinking识别always-thinks；显式thinking=False时改为None，保留reasoning抽取。 | 模板字符串启发式不是所有GLM版本永久规则；不是修改模型生成能力或支持任意parser。 |
| MiniMax-M2 config | 仅npu+model_type=minimax_m2+fp8将quantization清None，交默认dequantized BF16加载；临时platform验证hook在finally恢复，图模式未设HCCL_OP_EXPANSION_MODE时补AIV，已有其他值只警告。 | checkpoint标FP8不代表此路径以FP8推理；清字段也不证明权重dequantization数值和内存已验。 |
| MiniMax-M2 attention | qkv后用缓存cos/sin与TP Q/K RMSNorm+RoPE融合，再attn/o_proj；rotary_dim可小于head_dim。 | forward签名仍有positions，但该体未直接按它索引cos/sin，需核缓存由正确caller更新。 |
| Kimi K2.5 vision | 按t/h/w插值2D位置，t<=num_frames，多帧叠time_weight；grid Tensor转tolist。FP8_ATTENTION能力下MoonViT.to会剔除所有位置dtype和dtype kwarg。 | 保留原vision dtype不等于模型所有子模块自动FP8；tolist也可能有同步成本。 |
| Qwen3-VL | AscendMRotaryEmbedding走QKV RMSNorm+M-RoPE融合，cos/sin先对齐device/dtype；其他rotary分支按head形状归一化再RoPE。DeepStack在SP时按TP chunk，vision位置插值用Native helper。 | chunk正确需要行分区与padding匹配；不能只因tuple/tensor shape合适把M-RoPE当普通RoPE。 |
| Qwen3 DFlash | fused KV线性投影后分层K norm、重复positions做RoPE，再按每层/共享slots写KV；slots=None仍做前面计算但不写。mask embedding读取任意异常返回None。 | 异常被吞不证明mask embedding存在；每层slot列表长度/缓存生命周期需独立检查。 |
| Step3.5 | GQA限定，Q/K权重+1匹配GemmaRMSNorm；可选head-wise sigmoid gate。router bias与FP32 gate必须开启，非零SwiGLU limit只接受7并选swiglustep。 | 不能用普通RMS权重、SiLU或低精度gate无条件替代；该补丁并非任意Step架构模板。 |

Qwen3VL补丁同时覆盖Qwen3Attention与Qwen3MoeAttention.forward，并在类缺start_layer/end_layer时补PP属性；视觉文件名不意味着只影响视觉塔。MiniMax平台验证hook是全局短时替换，finally恢复不提供并发锁；Kimi.to wrapper重复导入也未在此提供通用去重。

Step3.5的sequence-parallel MoE仅PP1、TP>1、EP且本层为MoE，attention o_proj不先reduce；forward先需要时all-gather，attention后pad到TP倍数并reduce-scatter，residual按相同SP布局，再FFN。Dense层先恢复全tokens，最终model输出若仍shard会all-gather/crop；TP fused all-reduce门禁另要求DP1，不能把这两条混为一个开关。层配置可按layer_types选不同heads/head_dim/partial_rotary，checkpoint和分层参数不可全层复用。

## DeepSeek MLA与PP辅助状态

DeepSeek补丁按q_lora_rank分fused QKV-A或独立Q/KV投影，num_heads必须整除TP；保留KV rank、NoPE/RoPE、V head维度。非default rope参数会被原地改为deepseek_yarn或llama_scaling，yarn mscale平方修softmax scale。index_topk决定稀疏家族；只有skip_topk且对应indexer_type=shared、非MTP才跳indexer初始化，MTP不会继承target的top-k复用捷径。

MRv2辅助hidden用Native EagleModelMixin relay，旧路径用Ascend PP transport；TOPK_INDICES另有传输类型与真实buffer。forward在首stage取embedding或inputs_embeds，后stage取中间hidden/residual；捕获aux在层边界，SP行数不等positions时先all-gather/crop。非末stage打包aux/topk，末stage恢复完整hidden/residual再norm；top-k buffer非空不证明本步已经被正确刷新。

Eagle3初始化的target_layer_count来自目标总隐层数，并以此作为draft起始layer id；draft_vocab_size缺失回vocab_size，draft_id_to_target_id是待加载Parameter，零初始化不代表映射已经可用。Llama分支给LM head传draft quant config，DeepSeek分支没有同样显式参数，不能由相似构造统一推量化。

另一Eagle3 PP helper按aux_layer_数字后缀排序中间状态，仅对DeepseekV2Model或EagleModelMixin选实例forward，明确跳MiniMaxM3。其DeepSeek closure与新版全局DeepSeek补丁签名不同，是否实际调用该helper与选哪套实现必须追真实caller；定义存在不构成两套都能同时覆盖的证据。make_empty按incoming taps分配aux槽，起点/层号/宽度必须与训练draft tap对应。

## 验收与性能归因

固定模型revision与Native版本，记录最终工厂/类/MRO、quant dtype、rope/gate/scale、每层配置、target/draft vocab映射、PP tap和输入输出行分区。分别验证有/无融合、SP padding、PP辅助状态、视觉帧网格、mask缺失、路由统计与EPLB物理映射。静态全局替换、能力位或反量化fallback不等于模型支持、精度或优化收益；先与来源支持的基线路径对齐，再测projection/通信/vision/draft各段和端到端时延。


## MLA Prefill注册桩的执行边界

patch_mla_prefill_backend.py 将上游 selector 替换为 AscendMLAPrefillBackend，get_name=ASCEND 且 is_available=True，目的是绕过Native初始化时错误选择FlashAttention。run_prefill_new_tokens 与 run_prefill_context_chunk 都抛 NotImplementedError，实际完整forward由AscendSFAImpl/AscendMLAImpl负责；不得把 is_available 或完成构造当这两个桩方法可以执行，也不能让新模型绕过真实attention实现调用桩。
