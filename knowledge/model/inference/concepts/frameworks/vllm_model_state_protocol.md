---
type: Concept
title: vLLM 模型状态协议：ModelState、专有元数据与采样扩展
description: 沿 ModelState、ModelSpecificAttnMetadata 和 DefaultModelState 核对MRv2抽象入口、请求状态、任务列表、自定义采样器与bonus
  token；ModelSpecificAttnMetadata通过get_extra_common_attn_kwargs按cache group和num_reqs扩展公共attention参数，通过get_extra_attn_kwargs按builder扩展后端参数，结合prompt/MM有效行、填充视图及Ascend消费入口确认适配边界。
aliases:
- ModelState
- ModelSpecificAttnMetadata
- DefaultModelState
- custom_sampler
- get_additional_cg_support
- num_new_sampled_tokens_per_step
- vllm.v1.worker.gpu.model_states.interface.ModelSpecificAttnMetadata
- ModelSpecificAttnMetadata.get_extra_common_attn_kwargs
- ModelSpecificAttnMetadata.get_extra_attn_kwargs
tags:
- task.design
- task.implementation
- topic.model_adaptation
- topic.multimodal
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_states/interface.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_states/default.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/default.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/attn_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T04:15:23Z'
updated_at: '2026-11-03T02:54:05Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM 模型状态协议：ModelState、专有元数据与采样扩展

## 机制与固定范围

ModelState承载MRv2中模型特有的输入准备、持久请求状态和注意力扩展。新模型完成架构注册后，还要明确实际状态类及其与Runner的合同；注册成功不能替代状态适配。普通输入的请求、token与块索引量纲见[输入元数据](vllm_ascend_input_attention_metadata.md)，完整任务步骤见[新模型接入](../../guides/bringup/vllm_ascend_new_model_onboarding.md)。

固定Native vLLM 5df63a7203cdb9328d824a27b682e77c7b9928be：interface.py 256行、default.py 238行全文；Runner仅354–382、455–514。对照Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的default.py 579行、工厂84行全文，以及attn_utils.py 521–568。Main pin为544f182d9f0c9bfe8bd7645525951d5e3692a542，与独立Native快照分开，不据继承名字认定私有ABI已配对。

全部源码只作数据，没有导入模型、执行上游测试、采样、图或NPU。本文解释接口机制；整项硬件和模型范围未知，保持draft/空平台。Native中的CUDA/GPU类型名与ALWAYS枚举均不构成Ascend实机支持证明。

## 抽象入口与默认hook

ModelState是抽象基类，要求子类实现四个入口：

| 入口 | 需要闭合的职责 |
| --- | --- |
| prepare_inputs_embeds | 准备本轮嵌入或模型专用编码输入；具体子类可返回Tensor或None。 |
| prepare_inputs | 返回交给模型forward的额外参数，并定义其中状态的消费方式。 |
| prepare_dummy_inputs | 为dummy/capture准备相应输入；不能用dummy成功替代真实请求。 |
| prepare_attn | 按本轮请求、token、cache group和运行模式构造注意力元数据。 |

add_request、remove_request、apply_staged_writes、initialize_kv_cache、capture_inner_cudagraphs、preprocess_state和postprocess_state在此基类默认不做操作。源码注释说明initialize位于KV分配绑定之后、preprocess位于block gather之后；本文所读Runner选段没有闭合这些hook的全部调用顺序。覆写时同时检查实际调用方，不能凭存在方法名就假定状态已保存、清理或设备已同步。

基类supports_prompt_embeds为False；supports_mm_inputs仅由构造时encoder_cache是否非None决定。后者是这个对象的接线条件，不是按模型名判断的全平台能力表。存在encoder cache才创建EncoderRunner；其encoder图manager还要求非enforce_eager、cudagraph_mm_encoder开启，以及模型满足supports_encoder_cudagraph接口判断。

max_num_reqs、max_num_tokens、嵌入宽度和dtype来自构造配置。max_model_len则是动态读取model_config.max_model_len的只读property，以反映长度调整；该property本身不重新分配已构造的buffer。不能把配置上限变化当作所有持久容量已一起扩容。

## 任务列表与采样器的实际消费条件

get_supported_generation_tasks按模型接口判断生成、转写和实时任务。若模型满足转写接口且supports_transcription_only为真，会提前只返回transcription，跳过此前累积的生成项及后续实时项。接口helper的全部实现没有在本卡展开，不能只由模型家族名补齐任务列表。

custom_sampler默认返回None，保留默认采样器；覆写合同是返回sampler与可为空的rejection_sampler二元组。已读Native Runner仅在最后PP stage且模型不是pooling时进入采样器初始化：先构造普通或watermark采样器，再调用model_state.custom_sampler。返回值为真时先检查watermark兼容性，再替换二元组；否则有投机配置时构造默认rejection sampler。因此不能推成所有rank都调用此hook，或返回任意对象都会自动适配。

num_new_sampled_tokens_per_step默认1，指每步新产生的bonus token数量，不包含已接受的draft tokens。草稿长度、接受长度与新token数是不同量；改变该值还需核对实际采样、提交与请求记账消费者。本卡没有运行这些消费者或证明采样分布。

## 专有注意力元数据有两个扩展口

ModelSpecificAttnMetadata提供get_extra_common_attn_kwargs，按cache group与请求数返回公共元数据附加参数；另有get_extra_attn_kwargs，按builder与请求数返回后端附加参数。默认均为空字典，不等于所有模型额外字段都可省略。

已读Ascend attn_utils选段在逐组构造common metadata时调用第一个入口，并透传附加字段；没有由这个选段证明第二个入口在所有backend上的实际调用。传入的num_reqs、group身份、Tensor引用和padding范围由具体状态类与builder共同约定，不能把一个组的encoder长度无条件广播到所有组。具体实例见[Encoder-Decoder状态](../../guides/integration/vllm_ascend_encoder_decoder_state_contract.md)。

get_additional_cg_support默认返回AttentionCGSupport.ALWAYS与None，含义是该模型状态没有提出额外的图限制；它不是整个Attention后端、设备、编译器或模型都支持任意图模式的结论。

## 默认实现的prompt与多模态嵌入

DefaultModelState声明supports_prompt_embeds=True，但仅在配置enable_prompt_embeds时创建PromptEmbedsState；非MM且启用prompt embeds时，才额外分配按最大token容量组织的持久零初始化嵌入buffer。未满足这些前提时，不应独立调用依赖该buffer的helper。

有RoPE状态时，add_request要求prefill_token_ids，并从传给位置初始化的MM特征中滤去prompt_embeds模态；它也向prompt状态转发请求。remove_request在这个默认实现中只委托prompt状态清理，不能据此宣称encoder cache、所有外部引用和设备资源都已释放。apply_staged_writes显式提交RoPE与prompt状态的分阶段写入。

prepare_inputs_embeds只用前num_tokens个有效input_ids生成或合并嵌入。MM路径先执行编码，再gather相应媒体嵌入；启用EVS且有媒体时可重算位置并刷新staged RoPE，gather覆盖还会去掉EVS位置通道。非MM路径把模型文本嵌入写入有效前缀；随后prompt状态按请求已计算位置覆盖用户提供的嵌入。

返回值是前num_tokens_after_padding行的view。这里没有每步无条件清空整个padding尾部；构造时为零、dummy返回持久buffer切片，都不能证明下一步尾部仍为零。有效行、图容量和需要初始化的尾部必须沿实际消费者核对。[V4.1视觉接入](../../guides/integration/vllm_ascend_v41_vision_adapter.md)的模型专用有效行协议继续独立维护。

基类execute_mm_encoder在prepare得到非空kwargs时执行encoder，再以zip(mm_hashes, encoder_outputs)更新encoder_cache.encoder_outputs；这里没有单独的等长断言，不能把zip当完整输出数量校验。gather_mm_embeddings转交请求顺序、调度token数、CPU query边界、prefill/computed长度与draft lookahead等信息。完整EncoderRunner、缓存容量与搬运语义另见[缓存策略](../../guides/optimization/vllm_ascend_score_encoder_cache_policy.md)和[EC搬运](../../guides/integration/vllm_ascend_eccpu_transfer_pipeline.md)。

## 默认attention与Ascend扩展分别核对

Native DefaultModelState的prepare_inputs在有RoPE时准备位置；prepare_dummy_inputs仅在MM/prompt或RoPE需要时附加相应参数。prepare_attn在FULL时使用padded请求与token数，其他模式使用实际数，并取N+1个CPU/GPU query边界。capture的max_seq_len取模型上限，非capture取当前请求upper bound最大值；还转交RSWA、DCP、MM prefix和模型专有元数据。外部builder与空batch保护不由这个本地分支全部证明。

Main AscendModelState增加device_metadata.run_build与finish_execution、模型嵌入补齐数量通知、Engram钩子及回放/offload接线；prepare_attn先拒绝ubatch_idx非0，并有自己的PCP/PIECEWISE dummy token宽度。finish_execution不是所读Native ModelState抽象接口中的方法，不能让任意新状态类仅继承Native基类就假定具备这个清理合同。

工厂还可能采用模型自己的get_model_state_cls。实际类选择与[加载后Mamba复制](../../guides/integration/vllm_ascend_mamba_kv_load_copy_contract.md)、[SWA回放](../../guides/integration/vllm_ascend_swa_bounded_replay_contract.md)、[310P状态接入](../../guides/integration/vllm_ascend_310p_model_state_contract.md)分开验收，不把具体子类行为提升成所有ModelState的保证。

## Agent的适配检查

保存实际状态类/MRO、框架与配对版本、四个抽象入口的返回合同、请求slot和分阶段写入时点、MM/prompt开关与buffer容量、actual/padded计数、group扩展字段、实际任务列表，以及last PP采样器/验证器身份。依次验证请求重排与slot复用、真实输入与dummy、连续步状态、padding、失败清理，再验证目标模型质量、图和并行组合。性能分析分别量输入准备、encoder、metadata、采样及forward；本次没有实机性能或Agent A/B结果。
