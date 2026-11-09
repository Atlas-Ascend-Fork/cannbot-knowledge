---
type: Guide
title: vLLM Ascend Encoder-Decoder 状态：AscendEncoderDecoderModelState 与编码长度
description: 沿 AscendEncoderDecoderModelState 和 EncoderDecoderModelState 核对请求顺序、encoder_outputs 交付与清理、跨注意力组长度及 actual/padded 元数据，对照图模式回退、DBO 拒绝与 capture 参数接口。 正常执行的encoder_seq_lens按mm_features嵌入数量求和，capture使用max_encoder_len并只供CrossAttentionSpec组。
aliases:
- AscendEncoderDecoderModelState
- EncoderDecoderModelState
- EncoderDecoderAttnMetadata
- _get_encoder_seq_lens
- prepare_inputs_embeds
- EncoderDecoderModelState.prepare_inputs
- EncoderDecoderModelState._get_encoder_seq_lens
- EncoderDecoderAttnMetadata.get_extra_common_attn_kwargs
- AscendEncoderDecoderModelState.prepare_attn
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.multimodal
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/encoder_decoder.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_states/encoder_decoder.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_model_runner_v2_encoder_decoder.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/attn_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T03:15:06Z'
updated_at: '2026-11-03T03:12:13Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Encoder-Decoder 状态：AscendEncoderDecoderModelState 与编码长度

## 消费任务与证据边界

为CrossAttention编码器—解码器模型接入MRv2，或排查编码输出串请求、decode重复encode、编码长度与图填充行错位时，先核对模型状态类、输入交付和每个cross-attention组的元数据。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：状态97行、UT188行、状态工厂84行全文；platform仅1323–1362，attn_utils仅521–568，Runner仅601–649，pin同SHA复用。

独立Native5df63a7203cdb9328d824a27b682e77c7b9928be的encoder-decoder状态197行全文，用于区分继承接口与Ascend覆盖。Main实际pin为544f182d9f0c9bfe8bd7645525951d5e3692a542，不能用独立快照直接证明配对ABI。全部源码与测试只作数据，没有运行encoder、音频/图像处理、模型、图或NPU；保持draft/空平台。

[V4.1视觉接入](vllm_ascend_v41_vision_adapter.md)的有效embedding行和MM merge是另一条模型协议；[Score Encoder Cache](../optimization/vllm_ascend_score_encoder_cache_policy.md)管缓存策略，[ECCPU搬运](vllm_ascend_eccpu_transfer_pipeline.md)有自己的模型/connector门禁。不能因为都叫encoder cache，就把输出生命周期、缓存容量和传输路径混为同一合同。

## 确认实际选中的model state

工厂init_asecnd_model_state先尊重模型get_model_state_cls覆盖。没有覆盖时先判断hybrid，再判断STANDARD_WORKER_PATCHES能力；非标准worker会先进入_310p状态分支。只有继续落到标准非hybrid分支，且model.modules()中存在CrossAttention，才选择AscendEncoderDecoderModelState。

因此不能仅依据model_config.is_encoder_decoder或模型名称断言实际状态类。Native类注释列Whisper、CohereASR、NemotronParse等用途，也不是这些模型在所有Ascend硬件上的支持表。先记录实际类、profile、构造路径和匹配版本，再进入当前接口验收。

## 编码输出走encoder_outputs

独立Native构造要求encoder_cache非None；enable_prompt_embeds为真时明确ValueError。max_encoder_len取hf_config.max_source_positions，属性缺省才用max_model_len。这里只读本类，没有补造所有config值、容量或自定义encoder的额外校验。

prepare_inputs_embeds按input_batch.req_ids顺序筛选scheduled_encoder_inputs中的非空列表，再调用encoder_runner.prepare_mm_inputs。mm_kwargs非空时，在timed_encoder_operation内执行encoder，把execute_mm_encoder的返回值直接保存为self.encoder_outputs；没有mm_kwargs时清成空列表。返回None，模型输入通过encoder_outputs，而不是inputs_embeds。

该Native路径不把这里的encoder输出另存embedding cache；来源设计是首步cross-attention K/V写入KV cache，decode后续使用该缓存。真实writer/reader及完整EncoderRunner不在本卡已读范围，不能由这个注释认定首步写入或跨步数值已经通过。

EncoderDecoderModelState.prepare_inputs把当前列表放进返回字典，再将状态自身encoder_outputs重新绑定为空列表；已经交给模型的原列表仍保留。它不是原地clear返回列表，也不是每层重复交付。prepare_dummy_inputs返回空encoder_outputs。编码器异常时的全链路清理没有在本类用统一finally覆盖，接入方不能只看正常清空分支就宣称事务安全。

## 编码长度按请求和cache group生成

_get_encoder_seq_lens分配num_reqs长的CPU int32长度，正常运行按req_ids查询encoder_cache.mm_features，累加每个feature.mm_position.get_num_embeds()；不是文本input_ids长度，也不是任意像素或音频帧数量。capture阶段整段填max_encoder_len。

随后把这些长度non_blocking复制到持久encoder_seq_lens_gpu的前num_reqs行，并将GPU缓冲尾部置0，返回该前缀view与CPU NumPy别名。没有独立CPU完成等待；数据生命周期、当前流依赖和图复用应由实际调用链保证。容量和req_ids与num_reqs的一致性仍是调用方前提，不能把这个helper当通用输入schema。

按attn_groups逐个KV cache group检查，只给含CrossAttentionSpec的组记录这对长度。EncoderDecoderAttnMetadata.get_extra_common_attn_kwargs对不存在的组返回空字典，对存在的组返回按num_reqs切片的encoder_seq_lens与encoder_seq_lens_cpu；这些是视图，不是每组新拷贝。

所读Ascend attn_utils在各组构造common metadata时调用该扩展入口，并透传其余kwargs；is_prefilling可由扩展覆盖，否则使用调用方phase。不能把编码长度广播给所有self-attention组，或把共有Tensor引用解释为跨组状态完全相同。

## actual、padded与Native差异分别保存

AscendEncoderDecoderModelState.prepare_attn先assert ubatch_idx==0。这个拒绝发生在其他输入读取前；修改输入shape不能绕过DBO限制。

| 字段 | NONE/PIECEWISE分支 | FULL分支的局部元数据语义 |
| --- | --- | --- |
| num_reqs | input_batch.num_reqs | num_reqs_after_padding |
| num_tokens/num_input_tokens | input_batch.num_tokens | num_tokens_after_padding |
| num_actual_reqs/tokens | 真实请求数与真实token数 | 仍为真实请求数与真实token数 |
| 编码长度行数 | 使用num_reqs传给_get_encoder_seq_lens | 使用padding后的num_reqs |

Ascend同时转发query边界的CPU/device视图、is_prefilling、positions、seq_lens_cpu_upper_bound、dcp_local_seq_lens和parallel_config。它给build_attn_metadata的max_seq_len始终是max_model_len；独立Native在非capture时用当前upper-bound前num_reqs的最大值，capture才用模型上限。不能无差别复用两边的max长度计算。

独立Native的prepare_attn还转发rswa_prefix_lens；所读Ascend覆盖没有该参数，是否由其他层补齐需实际版本核对。两边均对num_scheduled_tokens做max，未在这里提供任意空数组的专用路径。UT主要是2真实请求、5token与4/8图容量，不据此宣称所有0请求、空stage和padding组合都安全。

## FULL代码分支不等于当前可部署模式

Ascend源码明确保留FULL语义用于未来支持。已读platform配置选段针对is_encoder_decoder，把NONE/PIECEWISE之外的cudagraph_mode回退：compilation.mode为VLLM_COMPILE时选PIECEWISE，否则选NONE。前面的不支持编译模式也会归NONE；这是具体配置选段，不是本卡已验证全部初始化调用链。

因此直接调用prepare_attn(FULL)或CPU单测走到其padding分支，不能证明服务配置能保留FULL，更不能证明NPU capture/replay支持。接入Agent要记录用户请求模式、配置归一化后的有效模式及实际捕获/回放证据，不能删掉平台回退来满足一个fixture。

Runner.capture_model在model_state.supports_mm_inputs且encoder graph manager存在、update_stream非None时，给encoder manager设置更新流；随后在torch_cuda_wrapper和communicator_switch上下文中委托父capture。它检查父方法是否含profile_only：不含时，profile_only=True会因图内存profiling不可用而抛出未实现异常，报文为Graph memory profiling is unavailable in this vLLM version.；否则按对应签名调用。上下文实现、Native父capture和真实graph资源仍需另核，不由这个局部适配证明全图可用。

## 已读测试与适配验收

188行UT以fake CrossAttention和支持标准worker的profile验证工厂选择；用mock EncoderRunner验证None返回、encoder_outputs交付后清空；按NONE的2请求/5token和FULL的4请求/8token检查actual计数、编码长度扩展、positions、DCP及parallel config，并检查ubatch_idx=1拒绝。prepare_inputs_embeds与旧get_mm_embeddings的fixture兼容分支不是生产代码自动兼容所有Native版本的证明。本次没有执行这些测试。

Agent记录实际状态类与版本、encoder_cache身份、req_ids与scheduled输入顺序、每请求embedding数、编码输出列表、各cross group长度视图、CPU/GPU容量及actual/padded计数。先检查重排、多请求、纯decode、无MM输入、连续两步与输出消费，再按有效图模式验证padding、DBO拒绝、caption/ASR等实际任务质量及失败恢复。最后分解预处理、encoder、cross-attention与decode时延；不能用缓存命中或metadata构造成功替代数值和性能验收。
