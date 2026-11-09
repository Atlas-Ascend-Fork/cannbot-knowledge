---
type: Guide
title: vLLM Ascend DSpark 草稿接入：块布局、Markov 反馈与模型接口
description: 按sample_from_anchor区分K与K+1 query，核对DSpark并行骨干后的顺序Markov采样、目标token反馈、confidence
  head及MRv1/MRv2图和LM-head调用差异。
tags:
- task.implementation
- topic.model_adaptation
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/dspark/speculator.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/dspark_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/llm_base_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/qwen3_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/qwen3_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/dspark/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dspark_speculator.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/speculative.py
  role: constraint
created_at: '2026-10-29T14:55:50Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T14:57:49Z'
---

# vLLM Ascend DSpark 草稿接入：块布局、Markov 反馈与模型接口


## 范围和基本执行链

固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2与参照vLLM v0.32.0的5df63a7203cdb9328d824a27b682e77c7b9928be，按实际Runner分别核对。这里只闭合已读Host模型/采样接口，不证明全模型、NPU kernel或任意硬件组合可运行，保持draft/空平台。DSpark不是每个token都重跑完整骨干：target辅助特征先组合并预计算draft Context KV，骨干一次输出整块hidden，随后每个草稿位置执行轻量顺序Markov head。

## K个预测不总是K+1个query

| sample_from_anchor | 每请求query数Q | 采样位置含义 |
| --- | --- | --- |
| True（缺省） | K；anchor加K-1个填充token | 每个query位置都预测下一token，sample_pos=query_pos+1 |
| False | K+1；anchor加K个填充token | anchor为bonus，采样填充位置，sample_pos=query_pos |

两种布局都返回K个draft token。CPU/device query_start_loc、sample_indices、positions、KV长度和graph容量都必须用同一Q；不能把通用batch×(K+1)配方套到全部DSpark checkpoint。MRv1构造按draft hidden size重建context buffers；target hidden宽度不一定等于draft hidden宽度。MRv1类头仍有“使用mtp”旧注释，但实际proposer分派与教程使用method=dspark，不能凭注释改CLI。

原生SpeculativeConfig会将dspark的parallel_drafting设True；未显式K时优先读取block_size，再读dspark_block_size，不按MTP n_predict推块宽。仍须记录实际归一化结果，不能依赖类头旧注释。

## 模型必须提供的协议

- combine_hidden_states、precompute_and_store_context_kv和get_draft_kv_cache_layer_names承接target特征、位置和真实draft缓存层；tap次序、materialized/raw格式与投影维度由训练协议决定。
- forward返回可按sample_indices选取的head hidden；compute_draft_logits返回draft词表轴的base logits，不能提前scatter成target词表后再加draft轴Markov bias。
- markov_embed接受的是前一枚target token，markov_bias输出draft词表bias。第一步来自本请求seed/anchor，之后必须反馈映射后的采样token。Markov矩阵一侧是target vocab、一侧是draft vocab，两者可能不同。
- map_draft_to_target、draft_id_to_target_id、真实LM-head/embedding所有权必须与loader一致；模块存在不能代替真实权重加载。缩表、扩展输入及confidence缺权重的拒绝条件见[词表概率空间诊断](../../runbooks/precision/vllm_ascend_dspark_vocab_probability_space.md)。

顺序采样先对B×K个hidden一次计算base logits，再对i=0..K-1计算prev的Markov embedding、加bias、采样并更新prev。它不是K个独立argmax，也不是把同一个anchor用于所有位置。原生Qwen Markov w1和w2复制到各rank，w2 disable_tp=True，避免每个顺序步另加词表collective；这是该head的实现理由，不推导所有head或整个draft均不分片。

## Runner、概率缓存和图的差异

MRv1在LLMBaseProposer的DSpark分支使用[B,K+1] token buffer，首列seed，返回[:,1:]；有d2t时明确退回greedy，不导出draft概率。MRv2沿native _sample_sequential，概率路径在target词表空间采样并保存每请求/每step logits；随机抽样以sample_pos-1作为位置输入。该接口配对不等于本卡已证明完整拒绝采样统计分布或跨实现同seed逐token一致。

Ascend MRv1 DSpark本路径强制use_cuda_graph=False；不能因target开图就认定draft也捕获。MRv2将Ascend graph manager绑定speculator/update_stream，enforce_eager只关闭draft图；实际NPU capture/update仍需按[query与KV长度诊断](../../runbooks/precision/vllm_ascend_dspark_query_kv_length_mismatch.md)核对。上游类说整步CUDA图覆盖采样，不是Ascend任意图/量化组合已支持的证据。

MRv2 DSpark直接调用compute_draft_logits，不走mixin.sample_draft。LM-head TP启用时Ascend包装前者，把输入行补到组内约定max_num_reqs×K，再裁回实际logit行；超过容量显式拒绝。不能把这一行容量误用成query容量B×Q，或在Markov每一步加入另一套不匹配的padding。

## Confidence和验证顺序

MRv2只有adaptive已启用且实际confidence_head存在时使用训练head，并关闭acceptance estimator；Qwen loader可因缺权重移除head，开关为真不证明head可用。confidence输入为对应位置的head hidden和前驱token的Markov embedding，输出是sigmoid概率。MRv1探索性[动态verify预算](../optimization/vllm_ascend_dynamic_verify_budget.md)与MRv2 adaptive是两套配置，不能互换。

先检查K/Q、tap格式、真实加载、词表轴和每一步prev，再对齐greedy输出与采样参数/位置缓存。覆盖两种anchor布局、零/部分接受、混batch、缩表、PP本地词表及图padding；性能分解成骨干、Markov顺序head、LM-head collectives、confidence与target verify。失败关闭DSpark并恢复整组匹配配置，本次未执行这些模型/硬件测试。
