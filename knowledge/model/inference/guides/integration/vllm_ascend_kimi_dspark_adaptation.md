---
type: Guide
title: vLLM Ascend Kimi K3 MLA DSpark：辅助流、逐层KV与独立head适配
description: 区分Kimi K3 MLA草稿与Qwen/GLM协议，核对raw-prefix-sum的layer边界、可配置因果性、逐层cache视图、PP本地embedding及checkpoint
  LM-head所有权。
tags:
- task.implementation
- topic.model_adaptation
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/kimi_k3_dspark.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_kimi_k3_dspark_weights.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_kimi_k3_adapter.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/kimi_k3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/qwen3_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/models/kimi_k3/nvidia/dspark_mla.py
  role: implementation
created_at: '2026-10-29T14:55:50Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T14:59:59Z'
---

# vLLM Ascend Kimi K3 MLA DSpark：辅助流、逐层KV与独立head适配


## 替换构造而保留哪些协议

固定Ascend ceac1a2b的AscendK3DSparkForCausalLM、AscendK3DSparkModel及decoder继承native K3DSpark类的方法合同，但只初始化nn.Module并重建Ascend组件，避免父构造硬编码NVIDIA Attention/decoder。来源代码和CPU断言不能证明所有Kimi部署、硬件或quant组合已适配，保持draft；部署范围仍按[Kimi K3模型指南](../models/vllm_ascend_kimi_k3_kda_mla.md)核对。

草稿用AscendKimiMLAAttention、KimiMLP和RMSNorm；Attention禁output gate、使用RoPE并disable_mlapo，quant来自draft配置而非无条件继承target。context_proj把target_hidden_size×num_target_layers投影到draft hidden，ColumnParallelLinear gather_output=True后context_norm。不得将GLM草稿的quant_config=None或Qwen GQA骨干套过来。

## 辅助状态格式必须和训练边界相同

Kimi MLA hook要求target提供set_dspark_aux_capture_materialized，检查配置tap id加1后的boundary列表与target.model.aux_hidden_state_layers逐项一致，且target hidden size匹配，然后setter(False)请求raw-prefix-sum。Qwen/GLM hook请求materialized=True且可容忍没有setter，不能共享其容错策略。

target的materialized流在层消费输入前捕获；raw流在前一层结束的layer_idx+1边界捕获hidden及prefix delta，PP切分的起始boundary也有不同归属。只验证拼接宽度不够，必须验证tap顺序、+1边界与capture模式。此处仅读相关调用段，不宣称AttnRes算子或完整PP/SP状态闭包完成。

## 因果性与Context KV写入

dflash_config字典存在causal键时优先取其值，否则取full_attention_causal，缺省False；每层get_draft_attn_causal与non_causal_multi_token_decode的反向配置必须配对。它不同于GLM MLA草稿一律返回False的协议。

context_slot_mapping=None或context为空时不写；列表/元组按层取slot，某层None跳过。融合Tensor cache先按kv_lora_rank拆出NoPE/RoPE逻辑视图，tuple保持原样。需要prolog_v3 writer的视图走对应入口，否则逐层fused QKV A投影取KV部分并调用exec_kv_prefill；RoPE按context_positions准备。不能假设分层writer会自动消费native跨层打包context_kv_proj。

Ascend load_weights没有复制native额外context_kv_proj权重，保留量化感知的逐层投影。父类仍暴露process_weights_after_loading等hook；实际版本的loader调用与可用Attention属性必须继续核对，不能仅看重写load_weights就宣称所有父类后处理均已绕过。

## PP、LM-head和加载失败边界

真实PP group>1时创建草稿自己的冻结embedding，按真实group判断，不能只看为draft重建的PP1 config。loader只在这条路径局部调整继承mapper以保留embed_tokens，原mapper对象与其余stacked/prefix规则不变。target stage0 embedding不能被末stage直接别名。

checkpoint的lm_head.weight在mapper丢弃之前截获，兼容带前缀的同名key；出现多个head或shape不是(config.vocab_size,config.hidden_size)时拒绝。成功时在context_proj设备上创建ParallelLMHead，调用其weight_loader处理本rank分片，再赋值head和has_own_lm_head。head缺失则保留target共享/对齐后备路径；不是将空head当作加载成功。

自有head已经接受draft hidden，不在QuaRot后处理中再次替换或旋转；投影和非自有词表副本的方向见[草稿权重对齐](vllm_ascend_draft_quarot_alignment.md)。临时head加载失败时原head和own标志保持，不代表AutoWeightsLoader此前更新的其他模型权重具有整模型事务回滚保证。

继承的draft_id_to_target_id=None及map_draft_to_target为恒等；不能把Qwen任意裁剪词表的d2t偏移格式自动套到这里。本地构造未建立confidence_head，继承mapper仍丢该权重；不能依据native父构造或enable_confidence_head字段宣称该Ascend Kimi路径已支持训练head/adaptive。需先补齐实际模块、加载和Runner合同并验证，不能用随机head代替。

## 多模态与验收

embed_input_ids收到已计算的多模态embedding时，先将placeholder位置id置0做安全词表lookup，再按is_multimodal合并；没有多模态数据或mask时走普通embedding。它复用target特征而不新建vision tower，不能据此扩大模型的视频支持范围。

按构造→tap捕获→逐层KV视图/slot→因果mask→head加载/共享→后处理→草稿采样验收，覆盖PP1/PP>1、head缺失/重复/错误shape、两类cache writer、placeholder越界及因果开关。失败关闭草稿，恢复完整匹配checkpoint/配置。所引测试为来源CPU/mock断言，本次未执行NPU、PP/PD或模型质量验证。
