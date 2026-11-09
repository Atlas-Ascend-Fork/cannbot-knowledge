---
type: Guide
title: vLLM Ascend 310P MTP输入：Host镜像、CPU slot与逐步图捕获
description: 沿 AscendMTPSpeculator310 和 AutoRegressiveAclGraphManager310 核对MRv2的工厂接线、草稿量化配置、拒绝后prefill输入、Host步号、CPU块表与序列长度，以及FULL逐步回放尚需验证的列写入和输入推进。核对每批num_speculative_steps由caller实际传入的协议，None缺省不能直接作为多步循环预算。
  AscendMTPSpeculator310._create_draft_vllm_config对非dict的hf_overrides浅复制模型配置后设空dict，避免修改共享draft；其RoPE全局flag在finally清False，不等于恢复嵌套原值或线程隔离。
aliases:
- AscendMTPSpeculator310
- AutoRegressiveAclGraphManager310
- _as_numpy_host
- _compute_draft_slot_mappings
- _capture_decode_per_step
- set_draft_step_host
- AscendMTPSpeculator310._multi_step_decode
- AscendMTPSpeculator310._create_draft_vllm_config
- AscendMTPSpeculator310._rope_position_flag_310p
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.speculative_decoding
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/spec_decode/mtp_speculator.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/spec_decode/aclgraph.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/block_table.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_spec_decode_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/spec_decode/test_mtp_mrv2_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/spec_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/target_dependent_ar/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/target_dependent_ar/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T06:33:52Z'
updated_at: '2026-11-03T07:29:07Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 310P MTP输入：Host镜像、CPU slot与逐步图捕获

## 任务、版本与证据边界

接入新模型的310P命名MRv2 MTP路径，或排查拒绝后草稿输入错位、捕获期间D2H、第二步以后重复token与陈旧长度时，先沿实际proposer、Host元数据和图管理器核对。本卡完整读取固定Main ceac1a2b的mtp_speculator 361行、aclgraph 264行、block_table 212行、patch_spec_decode_310 63行及MRv2 UT 221行，复用spec_utils 546行、worker补丁90行和pin全文；Runner仅1290–1458，公共Main AR仅89–148、305–485、719–900。

独立Native 5df63a72仅提供AR的1–485、622–700及基类speculator的190–220、285–325接口对照，未把这两个文件未读部分算作已闭合实现。Main配对pin实际为544f182d9f0c9bfe8bd7645525951d5e3692a542；独立Native不是该pin的ABI验收。本次未导入或执行上游、UT、NPU、模型和服务，保持draft/空平台，A2、A3、950及其他硬件与模型整体适用范围仍未知。

[310P状态接入](vllm_ascend_310p_model_state_contract.md)负责目标状态与捕获长度地址；[采样与拒绝提交](vllm_ascend_310p_sampling_contract.md)负责sampler、RNG和采样结果。本文解释其结果怎样进入下一轮草稿输入；LM-head加载与递归hidden语义分别见[头权重归属](../../runbooks/precision/vllm_ascend_mtp_head_ownership.md)和[MTP隐状态](../../runbooks/precision/vllm_ascend_mtp_hidden_state_contract.md)。

## 确认MRv2实际接线

worker补丁按STANDARD_WORKER_PATCHES capability选择分支，非标准分支导入patch_spec_decode_310。该补丁把Native AR模块的prepare_prefill_inputs、prepare_decode_inputs、update_draft_inputs替换为310P CPU helper，再包Ascend init_speculator：仅method=mtp且不是Gemma4/Step3p5专用MTP时返回AscendMTPSpeculator310，其余委托原工厂。不能只由配置里出现mtp或目录名310P判断最终对象。

如果Runner已经按名字导入工厂，补丁尝试重绑Runner引用；其except Exception直接忽略异常，因此需要实际记录最终工厂、实例类/MRO及模块函数引用。ModelWithContext缺少embed_input_ids时补转发。worker在通用eagle补丁之后再覆盖SpeculatorCudaGraphManager为AutoRegressiveAclGraphManager310，导入顺序也属于接线合同。所选分支直接返回专用实例，不能自动套用原工厂内部的所有enforce_eager规范化步骤。

旧_310p/spec_decode/llm_base_proposer_310.py继承MRv1 proposer。其尾元素保护或RoPE单测不能代替这里的MRv2调用证据，更不能把CANN Executor的next_n接口移植为本路径注册方法。

## 草稿配置和加载先独立核对

_create_draft_vllm_config遇到非dict hf_overrides时浅复制draft ModelConfig并在副本设空dict，避免直接修改共享SpeculativeConfig中的对象。它将草稿pipeline_parallel_size设1，首次replace即传target quant_config；target/draft realpath相同且target量化配置非空时再次显式传递该配置。这里的路径比较和配置继承没有验证checkpoint中的量化权重、scale或真实加载结果，不能扩成任意异路径量化兼容保证。

load_draft_model委托load_eagle_model。步间top-k复用要求draft HF标志index_share_for_mtp_iteration以及模型提供set_skip_topk和compact_topk_indices；这只是本类的门控，不证明任意模型、并行配置或异常恢复均正确。先完成真实权重和两项hidden返回合同，再进入输入及性能验证。

## 拒绝结果与Host镜像必须属于同一轮请求

Runner的已读postprocess先同步拒绝采样CPU结果，再消费其view、更新请求/模型状态并发布后续prefill Host镜像，同时把num_rejected CPU镜像放到speculator。propose只有_last_num_rejected_cpu不存在时才从传入Tensor补一个CPU副本；已经存在的镜像不会在此自动逐轮刷新， freshness依赖调用方发布。

prepare_prefill_inputs_cpu优先采用全局_PREFILL_HOST_META，但命中条件只比较num_reqs。setter保存传入数组引用，没有请求身份、调度轮次或跨实例隔离校验；相同batch大小不能证明请求重排、slot复用或上轮异常后的镜像仍有效。不命中时会将小型采样计数和最后token等元数据取回CPU，因此该路径不能被描述为完全无D2H或无同步。

对每个batch行，idx_mapping转换到持久请求slot；query_len先减拒绝数，仅保留有效前缀。输入token左移拷贝前保存目的尾元素，拷贝后恢复，再在最后有效位置写入选定next token；有采样结果取last_sampled，否则取next_prefill。positions按保留区间复制，query边界、seq_lens与last_token_indices写入持久buffer，并按各自规则填充尾部。有效query长度、数组容量、持久slot与batch行必须匹配，不能将这段局部更新当完整非法输入schema或失败回滚事务。

## CPU块表、采样位置与草稿步号

_as_numpy_host允许NumPy和CPU Tensor转换为int64视图或数组；device Tensor在非捕获期间可D2H，在NPU stream捕获期间明确抛错，要求预先准备Host镜像。_compute_draft_slot_mappings先转换idx_mapping、query_start_loc和positions，再调用CPU块表计算并按layer映射。

Ascend310PBlockTables要求cp_size=1，并核对cache group相关长度。块ID按每KV block包含的kernel block数展开；slot计算使用kernel block size，按position整除查物理块、取模求块内偏移。compute_slot_mappings校验query边界数量和token容量，活动列先填PAD_SLOT_ID，负请求索引保持PAD；未完整校验任意正越界请求、position或非单调query边界。只清活动列并复制对应前缀，不承诺容量尾部全清；dummy slot接口则填满持久device buffer。块表自身的_as_numpy拒绝device Tensor，与proposer外层允许非捕获D2H的转换区分。

prepare_decode_inputs_cpu先按target_seq_lens-num_rejected计算长度；advance_draft_positions为真才加1并clamp到max_model_len，同时位置加1并clamp到max_model_len-1。sample_src_positions始终加1，不能因位置不推进而也停掉采样key。该helper会读取少量device元数据到CPU，需安排在捕获之外。

update_draft_inputs_cpu丢弃传入device current_draft_step，使用全局_DRAFT_STEP_HOST；先写output_draft_tokens的对应列，达到末步才返回，否则推进采样key、token和下一步hidden，按advance flag更新位置与长度。_set_draft_step会同时更新device步号和set_draft_step_host。不能在捕获里用.item()替代Host步号，也不能只更新其中一份；全局int并无跨实例/并发隔离保证。

## 长度、phase与每批草稿预算

_calc_next_seq_lens_cpu从目标CPU长度的padded前缀clone；只有拒绝镜像存在且足够长时才减拒绝数，再加step并clamp上界，实际请求之后的填充行清零。缺镜像时没有在这里重新同步或拒绝执行，不能据函数名假设拒绝修正必然发生。

_build_draft_attn_metadata通过当前Ascend factory接入batch descriptor。step0、每请求多query或padded平均query长度大于1时设SpecDecoding；其余单token草稿decode设DecodeOnly，step>0再调用公共长度更新。实际/padded请求数、query边界与目标上界各有用途，不把padding行当真实接受过token。

_multi_step_decode使用range(1,num_speculative_steps)，新每批预算必须由匹配版本caller实际传入；签名中的None缺省不证明可省略。非skip_attn且需要推进位置或首decode步时，在捕获外重算CPU slot和attention metadata，再按FULL回放或eager生成。本类_generate_draft显式委托Native单步生成，以绕过Main父类在捕获中的额外metadata H2D；非捕获结束后再更新CPU长度。

独立Native propose按supports_decode_metadata_update选择fused或_multi_step_decode。该flag由初始化后的attention group能力决定，名义K=1另禁用；不能仅见310P自定义循环就断言运行时总会进入它。还要记录实际backend、能力flag、每批K与最终调用路径。Main AR自己覆盖capture，本MRO经它进入310P manager；不能把独立Native capture新增的specialize_spec_tokens关键字直接推成这里的调用异常。

## FULL逐步捕获的已知动作与未闭合边界

AutoRegressiveAclGraphManager310在draft prefill FULL期间临时替换AscendInputBatch.make_dummy：请求数大于0且整数平均query长度大于1时改SpecDecoding，finally恢复原引用。这是进程全局替换，没有证明并发或嵌套隔离。_rope_position_flag_310p也在_run_model期间开全局RoPE标志并finally设False；它不保存并恢复进入前的True状态，不能解释成任意嵌套安全。

_capture_decode_per_step在真正graph开始前准备输入、持久dummy slot、attention metadata和device seq_lens，并同步当前流、发布步号1。捕获闭包执行forward、sample并写持久draft buffer，明确不调用update_draft_inputs_cpu。回放前刷新ModelState记录的捕获长度地址，decode用_pending_draft_attn_metadata再交底层CudaGraphManager；prefill的updatable replay仅在实际存在更新任务时进行相应等待和update。

这里必须保留一个验收边界：所读decode捕获闭包固定写draft_tokens[:,1]，没有在闭包中看见通用helper的下一token/hidden推进；外层循环则可以有step>1。仅凭这些片段不能宣称真实K>2完整回放成功，也不能未经执行直接判定某配置必然出错。接入时应逐步核对每列草稿写入、下一步token/hidden、采样key、position、slot及捕获地址，再比较eager与FULL结果。

[历史310P图捕获报错](../../runbooks/runtime/ascend_310p_graph_mode_unsupported_enforce_eager.md)记录v0.9.2rc1-310p环境。当前固定Main出现FULL代码与CPU mock测试，不能作为历史约束已解除、任意310P图模式已支持或全模型已有性能收益的证据。按真实设备、软件栈和模型交集决定可用模式。

## 交付、验证与停止条件

已读UT定义采样源位置+1、decode输入推进、Host步号在mock捕获中不读device值、RoPE标志清理及decode capture路由等场景；本次没有执行这些测试，更没有真实NPU捕获、K>2数值、分布或性能证明。

适配交付应保存最终类/MRO与补丁引用、量化配置和实际权重、每轮请求slot/batch映射、采样/拒绝数、Host镜像发布点、每批K及能力flag；对每步保留输入token、两项hidden、位置、采样key、query边界、seq_lens、slot与输出列。覆盖零/部分/全接受、chunked prefill、batch收缩与同大小重排、slot复用、K变化及异常恢复，再核对eager/FULL与无投机基线。

镜像身份或步号不一致、捕获中触发Host读取、必要列或反馈未推进、输出不对齐时，停止性能结论并回到已验证的eager或无投机配置。性能分别量Host规划、D2H/H2D、每个draft、target验证和端到端有效token时延；减少某次同步的源码动机不代替净收益测量。
