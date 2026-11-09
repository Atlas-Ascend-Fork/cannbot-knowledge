---
type: Guide
title: vLLM Ascend 310P 状态接入：Ascend310PModelState、CPU规划与图缓冲
description: 沿 Ascend310PModelState、Ascend310PMambaHybridModelState 和 Ascend310PRopeState 核对父类初始化、CPU位置与状态拷贝、FULL捕获地址刷新，以及投机解码的实际计数和填充行条件。
aliases:
- Ascend310PModelState
- Ascend310PMambaHybridModelState
- Ascend310PRopeState
- _refresh_capture_seq_lens
- _copy_mamba_state_from_cpu_plan
- _num_accepted_tokens_cpu
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.graph_execution
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/model_state.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/rope.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/test_model_runner_v2_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/default.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/mamba_hybrid.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T04:15:23Z'
updated_at: '2026-11-02T04:15:23Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 310P 状态接入：Ascend310PModelState、CPU规划与图缓冲

## 任务与证据范围

为310P命名的MRv2 dense/VL或hybrid状态适配新模型，或诊断FULL回放后序列长度陈旧、MTP填充请求进入错误phase、Mamba页边界迁移异常时，先确认实际状态类和CPU/device数据的所有者。固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：model_state.py 476行、rope.py 129行、公共default 579行、公共Mamba 496行、工厂84行及pin全文；UT仅135–217、946–998，没有读取或执行其余1070行文件的全部测试。

该Main配对Native pin为544f182d9f0c9bfe8bd7645525951d5e3692a542；[通用ModelState协议](../../concepts/frameworks/vllm_model_state_protocol.md)使用的独立5df快照提供版本对照，不构成生产ABI已验证。全部源码和测试只作数据。类名、CPU fixture与FULL代码分支没有证明整模型/软件栈/硬件交集，保持draft/空平台。

[310P GDN接入](vllm_ascend_310p_gdn_execution_contract.md)拥有实际conv/recurrent/chunk入口，[GDN填充诊断](../../runbooks/precision/vllm_ascend_310p_gdn_padding_readiness.md)拥有PAD/NULL与consumer检查。本文补状态producer、位置准备和捕获地址，不替代完整Device算子、采样器实现或性能验证。

## 先完整初始化父合同，再替换专用状态

Ascend310PModelState先调用AscendModelState.__init__，保留父类创建的prompt_embeds_state、encoder_runner等属性，再创建捕获长度字典并替换RoPE。hybrid类也先调用完整AscendMambaHybridModelState构造，再准备CPU接受长度、对齐页索引和copy函数缓存；不能为避开某个GPU操作而跳过整层父初始化。

_replace_310p_rope_state调用get_310p_rope_state，并无条件把mm_pruner置None。原因是本专用RoPE没有EVS依赖的位置读写接口；不能将公共EVS重算路径直接复用。uses_mrope为真时，工厂要求模型满足SupportsMRoPE并按mrope_num_dims构造状态，否则返回None。返回None时prepare_inputs委托父类；有专用RoPE时走本类CPU位置准备并返回positions，uses_mrope时还调用专用cos/sin切片helper。

源码的Triton-free描述针对这些专用入口。父类保留的嵌入、encoder、device metadata、公共Mamba与外部helper仍需逐项核对，不据这个注释宣称新模型全部路径均无Triton。状态工厂的模型覆盖与capability顺序见[Mamba状态选择](vllm_ascend_mamba_kv_load_copy_contract.md)，不能仅凭硬件名或is_hybrid猜最终类。

## MRoPE的请求表、当前位置和完整拷贝

Ascend310PRopeState按请求slot×维度保存prefill_positions，并保存每请求prefill_delta。init_prefill_positions调用模型get_mrope_input_positions，对每维stage_write；apply_staged_writes再提交位置表与delta。外部staged tensor与模型位置算法未在本文闭合，不能把暂存完成等同设备已可读。

prepare_positions_cpu先清positions_cpu的当前num_tokens_after_padding前缀，再按batch顺序和持久req_idx查询已计算token数。prefill分支从该请求各维的暂存表取[num_computed, num_computed+query_len)；decode分支用delta和context_len调用MRotaryEmbedding的输出helper，直接写持久NumPy视图。这里没有独立处理任意越界请求、跨prefill边界query或非法映射的完整schema。

位置buffer形状为[num_dims, max_num_tokens+1]，保留一列dummy。只切活动列会形成非连续二维view，所以H2D复制整个连续buffer，get_positions再返回所需token列。CPU存储仅在is_pin_memory_available时申请pin；non_blocking和源码的性能动机不等于本次实际测得异步重叠或收益。它也不是每轮把整个CPU容量全部清零：清零范围与传输范围不同。

## FULL回放必须刷新捕获时绑定的地址

_record_capture_seq_lens按Tensor的data_ptr记录view，同一首地址保留numel最大的view。不同offset的view可有不同首地址，不能把字典key当整个底层storage的统一身份；字典持有引用也不能证明图已捕获成功。

_refresh_capture_seq_lens遍历已记录buffer，把runtime与capture两者较小长度的前缀copy过去，再将capture剩余尾部清零。runtime更长时不在此自动扩容。只更新当前input_batch.seq_lens不足以保证图读到新长度，因为图可能仍绑定另一个capture地址。

dense mixin在for_capture时记录；正常执行只有cudagraph_mode为FULL才刷新，其他模式直接委托父prepare_attn。hybrid覆盖也执行相同记录/刷新逻辑，再自行构造元数据。这里没有新增设备event或跨rank同步，必须结合实际capture、流和父builder确认可见性。

已读UT用CPU Tensor定义同址2行/4行保留4行、另一个3行buffer一起刷新到[17,9,0,…]，并检查PIECEWISE不刷新、FULL刷新。它没有执行真实NPU capture/replay。

## 专用采样器与MTP门禁

custom_sampler从max_num_reqs取容量，缺失或假值回退1；device缺失回退CPU，方便object.__new__ fixture。vocab_size优先取传入sampler.sampling_states，否则尝试model_config.get_vocab_size。随后创建Ascend310PSampler；无speculative_config时返回它与None，有配置时仅method等于mtp才创建RejectionSampler310V2，其他方法明确拒绝并说明310P MRv2仅支持MTP。

这些fixture缺省不构成生产环境自动恢复的建议。真实配置、vocab、采样质量与penalty/top-k/top-p能力要读实际sampler并运行验收；本文没有完整读取或执行两种采样器。父Runner的last PP、pooling和watermark条件见[ModelState协议](../../concepts/frameworks/vllm_model_state_protocol.md)，不能把本hook有返回值当所有rank均已接线。

## hybrid的真实计数与填充行

hybrid add_request显式使用super(MambaHybridModelState, self)跨过Native Mamba层的GPU scalar初始化，仍调用后续父hook，然后将_num_accepted_tokens_cpu对应slot设1。align开启时，初始页索引取(num_computed_tokens-1)//cache_config.block_size；后续迁移另使用Mamba spec的block_size，二者一致性需实际配置证明。

prepare_attn首先拒绝ubatch_idx非0。FULL用padded请求数和token容量；其他模式用真实数，num_actual_reqs与num_actual_tokens始终保存真实量。is_prefilling先分配CPU零数组，再填实际请求行。non-capture且存在投机token时，accepted按持久idx_mapping从CPU状态取实际行，padding默认1。

真实spec行要求num_draft_tokens_per_req大于0，且num_scheduled_tokens等于draft数加1；其余行draft标为-1。只有FULL有填充请求、draft数组存在，并且全部真实请求为spec或attn_state.name已经是SpecDecoding，且所有padding query长度都等于配置K+1时，才把padding draft设为对应长度减1。不能无条件将所有padding提升为spec，也不能把accepted尾1解释为这些行真实接受过一个token。

CPU seq_lens若存在且需要padding，会先复制再仅清[num_actual_reqs,num_reqs)；不是原地清原数组，也不是承诺全部容量尾部清零。随后交给公共build_attn_metadata与MambaHybridAttnMetadata。空调度数组的max、外部builder和实际图一致性仍需沿调用链验证。

## CPU规划Mamba页迁移

preprocess_state在align关闭或请求数为0时返回。有效路径要求input_batch.block_tables_np存在，保存本轮CPU块表、idx_mapping副本及cache config；copy函数按Mamba类型映射到各group并缓存。num_computed_tokens的传入Tensor在这个方法中不直接使用，计算依赖input_batch内的CPU数据。

对每个batch请求，token_bias=max(accepted-1,0)，computed_after是该batch行的已计算数量加本轮query长度；new_state_idx=ceil(computed_after/spec.block_size)-1。先更新CPU页索引，只有旧索引非负且发生页变化时才复制，并把accepted重置1。copy失败时没有回滚刚更新索引的统一事务保证，重试前应保存原页和偏移。

_copy_mamba_state_from_cpu_plan按group、layer和state与copy函数的zip配对：函数名包含conv时，按is_conv_state_dim_first选择滑动维，拷贝宽度为width-token_bias，不大于0则跳过；先clone源切片以处理可能重叠。其他state从src_column+token_bias对应的块复制到目标块，也先clone。这里没有给zip提供严格等长校验，也没有覆盖所有块表索引、布局与函数命名的输入验证。

本CPU preprocess覆盖没有采用公共路径的_pending_bulk_copy决策。涉及远端KV加载时，要单独核对它和实际connector加载的先后关系，不能由[通用wrapper的加载后回调](vllm_ascend_mamba_kv_load_copy_contract.md)直接推成本路径的CPU预复制也已经延后。

## 采样后提交与失败边界

postprocess_state直接对idx_mapping及Tensor形式num_sampled使用numpy，调用方需提供相应CPU对象。它过滤负请求索引，把有效slot的接受数设为至少1；UT用[0,-1,2]定义padding索引不写到最后一项。这个过滤不能证明任意正越界索引也被校验。

有RecoverSSM时，会把CPU接受长度及必要的页索引物化到device，调用commit_step，再把结果拷回CPU；该分支在后面的零请求早退之前，不能宣称idle一定没有提交或CPU/device往返。具体staging、图视图与commit消费者见[RecoverSSM诊断](../../runbooks/precision/vllm_ascend_glm_recoverssm_graph_metadata.md)。

后续align路径按persistent req_idx读取num_computed_tokens，计算running_tokens=new_computed-accepted+1与对齐边界；达到边界才按token_bias复制。来源/目标列相同且bias为0时可跳过。与preprocess按batch行读取的数组区分，不能混用两个索引空间。局部更新、copy和commit异常没有在此形成全链路自动回滚。

## 适配交付与验证

记录实际状态类/MRO、父接口版本、MRoPE维度与暂存表、请求slot和batch映射、原始/实际/填充计数、capture/runtime地址、CPU块表与页索引、accepted/draft及copy前后state。先检查完整父初始化、请求复用、连续prefill/decode、padding收缩、页边界与失败恢复，再比较目标模型输出和有效图模式。性能分别量CPU规划、位置H2D、state clone/copy、RecoverSSM往返与forward；源码减少某些分配的动机不代替真实端到端收益。
