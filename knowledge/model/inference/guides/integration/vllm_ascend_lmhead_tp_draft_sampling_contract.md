---
type: Guide
title: vLLM Ascend LM-head TP草稿接入：行补齐、词表重排与能力门禁
description: "沿 LmheadTPDraftSamplingMixin、lmhead_tp_pad_rows、lmhead_all_to_all 与 AscendLogitsProcessor._get_logits_lmheadtp 核对target索引补行、draft hidden补零、DSpark独立容量、DP轴组与采样门禁；区分num_steps版本接口、paired544和独立5df、idle加入及skip_gather边界。 draft_logits在运行时非None仍明确拒绝，不能只依赖构造配置检查。"
aliases:
- LmheadTPDraftSamplingMixin
- _lmhead_tp_validate_draft_sampling
- lmhead_tp_pad_rows
- lmhead_tp_max_num_logits
- lmhead_all_to_all
- AscendLogitsProcessor._get_logits_lmheadtp
tags:
- task.implementation
- task.debugging
- topic.parallelism
- topic.speculative_decoding
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/lmhead_tp_utils.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/vocab_parallel_embedding.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_model_runner_v2_finegrained_tp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_lmhead_all_to_all.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/target_dependent_ar/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/dflash/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/dflash2/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/parallel_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/v1/worker/gpu/spec_decode/speculator.py
  role: constraint
created_at: '2026-11-02T09:16:28Z'
updated_at: '2026-11-04T03:35:06Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend LM-head TP草稿接入：行补齐、词表重排与能力门禁

## 接入任务与证据边界

新模型能生成hidden，但开启LM-head TP后卡在collective、草稿token错误、参数签名不匹配或dummy阶段挂起时，先核对实际head计划、组成员、行容量和采样入口。LmheadTPDraftSamplingMixin处理的是草稿头的组内行对齐；权重是否真实加载、最终RMSNorm和递归状态仍分别由[LM-head归属](../../runbooks/precision/vllm_ascend_mtp_head_ownership.md)与[MTP隐状态合同](../../runbooks/precision/vllm_ascend_mtp_hidden_state_contract.md)维护。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。13个选定来源范围包含5份全文：mixin148行、vocab_parallel_embedding592行、finegrained Runner UT421行、all-to-all UT109行及pin1行；另外8份有界范围为utils710–748与805–998、Runner350–390/634–714/1099–1270、AR74–112、DSpark1–155、DFlash120–190、DFlash2 112–143、AscendConfig1335–1455、parallel_state150–241。vocab文件虽全文阅读，本文只闭合LM-head计划、投影与重排调用合同，不宣称其全部embedding、PCP或量化路径已完成知识生产。

独立Native 5df63a7203cdb9328d824a27b682e77c7b9928be仅阅读base speculator400–535。Main实际配对Native是544f182d9f0c9bfe8bd7645525951d5e3692a542，另按固定Git对象阅读同文件425–515；这两份有界依赖均保持defer，不计新增Native覆盖。配对片段能解释关键字接线，不能代替完整安装ABI与运行验证。

全部上游仅作数据，未导入、执行UT、编译kernel或启动模型。硬件、模型、真实通信、图、数值和性能范围仍未知，保持draft、空平台及framework=vllm部分Scope。[细粒度TP部署](../optimization/vllm_ascend_finegrained_tp_contracts.md)保留配置与来源测量，[PP接入](vllm_ascend_pipeline_partitioning.md)保留PP组合冲突；本卡不以实现分支存在解除这些边界。

## 先确认实际head与通信组

lmhead_tp_enable只检查最终Ascend配置的lmhead_tensor_parallel_size是否大于0，不证明通信组已经初始化。FinegrainedTPConfig检查尺寸非负，启用时要求目标配置为MoE且尺寸整除data_parallel_size；o_proj/MLP的额外图、PD等门禁不能直接套给LM-head。草稿模型自身配置、复制或共享的head仍需独立核对。

所读parallel_state局部以PP、DP、TP三维rank grid构建细粒度组：固定PP与TP坐标，在DP轴按group_size切连续块。组缓存以size为键，相同size的组件可能复用同一个GroupCoordinator；不能仅凭名字断言每个组件都有独立process group。get_lmhead_tp_group在_LMTP未初始化时断言失败，没有自动退回普通TP。这段不闭合整个文件的PCP、EP或其他组初始化。

register_ascend_customop将ParallelLMHead、LogitsProcessor等名称映射到Ascend实现，并通过CustomOp.register_oot注册；兼容硬件能力分支还会替换部分head/embedding类。适配Agent应记录进程里的实际类、MRO、CustomOp绑定和group rank/world_size，不能只看仓库文件名就推导所有硬件进入相同实现。

_resolve_vocab_parallel_plan首先处理disable_tp=True，返回复制权重计划；因此DSpark的Markov head不会因prefix包含head而误入细粒度分片。普通head满足LM-head条件且开关启用时选择FINE_GRAINED及实际LM-head组，不将标准TP尺寸再乘一次。PCP权重分片条件生效时，会拒绝同模块finegrained LM-head knob；不能把这条局部门禁概括为任意PCP配置都由此验证。

## 固定容量有三种调用合同

lmhead_tp_max_num_logits只返回两个入参的乘积，约定全组使用相同容量；它不自行跨rank协商。lmhead_tp_pad_rows检查首维是否超过capacity：超过即ValueError，恰好相等返回原对象，否则对二维hidden追加零行，对一维indices追加零值。源码没有在这里完整验证任意维度、dtype、索引范围或所有非法容量。

| 消费路径 | 固定容量 | 补齐对象与裁剪位置 |
| --- | --- | --- |
| target Runner.sample | max_num_reqs × decode_query_len | 补私有logits_indices副本；新增零索引gather hidden row0；compute_logits后裁掉额外logit行 |
| 通常经过mixin.sample_draft的草稿 | max_num_reqs × (num_speculative_steps + 1) | 对实际hidden_states追加零行；父sample_draft返回后裁回真实输出行 |
| DSpark直接compute_draft_logits | max_num_reqs × num_speculative_steps | 加载时包装模型方法，对hidden补零、对返回logits裁剪；不经过mixin.sample_draft |

target的零索引补齐不等于草稿的零hidden补齐。Runner保留input_batch.logits_indices原对象供参数、penalty等消费者使用；不能为了对齐collective直接改写原batch映射。target在grammar及普通/拒绝Sampler分发前裁回真实logits，常规参数加工仍沿[MRv2采样管线](vllm_ascend_mrv2_sampling_pipeline_contract.md)核对。

mixin只补hidden_states，positions、idx_mapping、temperature、seeds、draft_step等继续原样传给父类。不能据输出被裁剪就假设所有父采样状态也已补齐，或给新模型的自定义sample_draft无条件开启这个mixin。应核对实际compute_logits、父方法副作用及额外行是否会读写请求缓冲；空hidden、零真实行与非法索引也需单独验证。

## 构造门禁必须由宿主接通

_lmhead_tp_validate_draft_sampling在开关关闭时直接返回。开启后按顺序拒绝_lmhead_tp_sample_draft_supported标志为False的宿主、draft_sample_method='probabilistic'、use_local_argmax_reduction和enable_adaptive_verification。AR、DFlash和DSpark的已读构造均在父初始化之后显式调用该验证；仅继承mixin不会自动替新宿主执行构造检查。

概率采样会使用按真实草稿布局分配的固定buffer，不能容纳额外组对齐行。local argmax的get_top_tokens可能只在本地词表分片取候选，不能替代已恢复的完整词表argmax。adaptive estimator按logit行数读写请求映射、特征与confidence缓冲，额外padding行越过其合同。mixin还在实际sample_draft入口检查draft_logits非None并再次拒绝，不能仅依赖启动配置字符串。

独立Native及配对片段的父sample_draft在draft_logits=None且未走local argmax时，计算logits并argmax；随后仍调用_maybe_predict_acceptance。裁掉token输出不会撤销此前状态副作用。若新宿主自行建立estimator或覆盖父方法，须检查实际对象与访问范围，不能把配置guard当作任意自定义状态的完整证明。

DSpark实际将_lmhead_tp_sample_draft_supported设True，并在load_draft_model后包装compute_draft_logits。其容量是max_num_reqs×K，超过即拒绝；普通mixin的K+1不能拿来替换。mixin及部分注释把DSpark列作绕行拒绝示例已不反映此实际实现，所读UT最后也明确断言DSpark为True、DFlash2为False。DSpark顺序Markov和词表反馈仍见[既有合同](vllm_ascend_dspark_block_markov_contract.md)。

DFlash2的get_top_k_tokens链路绕过普通sample_draft，实际标志为False；不能仅加入普通行padding就宣称支持。其MRO与图门禁沿[DFlash适配](vllm_ascend_dflash_runner_graph_contract.md)核对。UT定义检查Eagle、MTP、DFlash、DSpark、DFlash2均保留mixin，但这种继承断言不证明每个新模型的全部方法都使用了相同消费路径。

## sample_draft签名按实际版本解释

mixin在类定义时调用vllm_version_is('0.32.0')选择方法签名。该helper优先读取VLLM_VERSION，否则使用安装包版本，按PEP440 public版本比较并缓存结果；local build段不会改变版本身份。进程运行后修改环境变量不自动重建已经定义的类方法。

0.32.0分支向父类传原有七个采样参数；其他分支额外接受num_steps=1，并以关键字继续传给父类。开关关闭时同样透传这个新签名，所以关闭LM-head TP不能代替版本接线检查。

独立5df父方法有spec_step_idx=0，却没有num_steps；Main实际paired544的已读片段同时包含spec_step_idx=0与num_steps=1，并用后者构造draft watermarker的partial调用。由此可以确认该关键字在真实配对片段存在；不能把独立5df的差异写成paired环境必然失败，也不能从一个参数相符推导全部父类、watermark、配置和模块补丁ABI已经通过。num_steps参与概率水印路线，不证明LM-head TP允许被guard拒绝的概率组合。

迁移时固定Main、实际paired commit、安装包及VLLM_VERSION，记录实际方法签名与MRO。不要给独立5df库存绑定paired544同path，也不要按当前checkout文件替代配对Git对象的内容。

## 从词表分片恢复token owner

AscendLogitsProcessor._get_logits_lmheadtp先在LM-head组沿token维all_gather hidden，再对每rank本地词表权重执行_apply_head，最后调用lmhead_all_to_all，并裁掉词表padding。令P为组大小、N为汇聚后的token行数、V为补齐词表宽度，重排将每rank的`[N, V/P]`转换为该rank负责token行的`[N/P, V]`。

lmhead_all_to_all在P=1时返回同一logits对象且不通信。其他情况显式要求N能被P整除，随后将连续输入view为`[P, N/P, V/P]`，使用device_group执行all_to_all_single，再permute为`[N/P, P, V/P]`并展平成完整词表。缺少permute、按错误rank顺序拼接或只比较shape，都可能掩盖token与词表错位；词表分片相等还依赖建层时的padding与divide，不由这个helper逐rank重新验证。

此处全组固定本地容量C使汇聚后N=P×C，再恢复每rank的C行；真实行数仅在上层裁剪。不能按本rank活跃请求数独立选择collective尺寸，或用尾部无输出为由跳过通信。源码注释中的HCCL融合动机不构成本次测得的性能收益。

_get_logits的skip_gather=True会直接返回_apply_head的未裁剪结果，不进入普通词表恢复；调用方必须明确处理局部分片与padding。复制计划走normal路径且tp_size=1时不执行普通TP gather；PCP_X_TP另有重建分支。不能把这些分支的相同Tensor返回类型解释成同一完整词表布局，也不能把get_top_tokens与完整logits采样任意互换。

## Idle加入、prompt评分与验收

idle rank可能不调用sample。Main在dummy execute_model尾部，仅当LM-head TP启用、非profile且当前为最后PP rank时，用固定容量的零索引gather hidden并调用compute_logits；缺少父execute_model发布的state即RuntimeError。这次加入发生在父_dummy_run继续dummy proposal之前，EPLB步骤在其外围；移到整个父_dummy_run结束后再加入会改变通信顺序。具体PP支持仍需按现有组合边界验收。

sample_tokens另在LM-head TP开启且prompt worker请求prompt_logprobs或fixed-token prompt scoring时抛NotImplementedError，因为这些路线会再次以未补齐行调用compute_logits。不能只关闭普通输出logprobs就假设prompt评分路线已经消失，也不能把构造通过当成此运行门禁已被解除。

finegrained UT定义了CPU/mock的target与draft补齐裁剪、容量超界、构造拒绝、MRO以及idle的forward→LM-head→EPLB顺序，并用canary比较部分grammar/Sampler分发。all-to-all UT用按rank调用顺序工作的fake检查逐元素重排、P=1同对象与非整除错误；它没有真实执行分布式通信。本次也未执行这些测试，不能登记为硬件、图或数值验收。

Agent先保存最终配置、实际head计划、真实权重/组、每rank容量、真实行数、采样方法、版本签名与dummy顺序。用可定位每行每列的小张量核对重排，再覆盖组内不同请求数、idle、恰好容量/超界、target与draft交替、DSpark、绕行方法、prompt评分及新模型父方法副作用。先比较完整logits与greedy输出，再验证真实图/通信和允许的采样路线；正确性通过后分别测head、collective、额外padding、临时分配及端到端TPOT，不能沿用其他模型的显存或时延数字。

遇到签名、容量、rank顺序、输出词表或状态副作用不匹配时，恢复明确匹配的版本、拓扑和已验证配置，并停用新增LM-head TP组合；不要删除guard或静默截断真实请求来获得启动成功。本卡没有新增NPU、模型、Agent A/B或性能结果。
