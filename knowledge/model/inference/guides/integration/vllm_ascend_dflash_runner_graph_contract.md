---
type: Guide
title: vLLM Ascend DFlash MRv2接入：块表粒度、填充元数据与图门禁
description: "沿 AscendDFlashSpeculator、AscendDFlash2Speculator、prepare_dflash_inputs_factory 和 DFlashAclGraphManager 核对架构/MRO、kernel与physical块粒度、padded actual_seq_lengths_q、num_reqs_override及dummy DP隔离；区分prepare_forward与旧capture参数、全局callback、enforce_eager和selector walk的fp64/int32边界。 DFlashAclGraphManager.run_fullgraph在graph update流等待当前流后replay，再按传统或updatable路径更新参数；Python返回不能证明设备任务已完成。 发布5f5e25移除DFlash2图拒绝guard，selector使用按请求数的局部ForwardContext与独立缓存namespace。 ceac的DFlash KV输入准备先用原query位置计算slot，再截断输出position；逻辑位置clamp不证明KV地址安全。"
aliases:
- AscendDFlashSpeculator
- AscendDFlash2Speculator
- prepare_dflash_inputs_factory
- DFlashAclGraphManager
- _update_draft_attn_metadata
- _selector_walk_kernel_ascend
- DFlashAclGraphManager._graph_replay
- DFlashAclGraphManager._updatable_graph_replay
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.speculative_decoding
- topic.graph_execution
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/dflash/speculator.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/dflash2/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dflash2_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/spec_decode/prepare_dflash_inputs.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/attn_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/aclgraph_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/dflash2/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/pcp_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/lmhead_tp_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/spec_decode/lilicorr/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/vllm_ascend/worker/v2/spec_decode/dflash2/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/vllm_ascend/models/qwen3_dflash2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T08:20:30Z'
updated_at: '2026-11-04T03:35:06Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend DFlash MRv2接入：块表粒度、填充元数据与图门禁

## 接入任务与阅读边界

新模型接入MRv2 DFlash/DFlash2，或排查草稿块表寻址错误、FULL的query长度不匹配、dummy profiling沿用目标DP数量、DFlash2误入图路径时，先核对真实工厂、输入callback、metadata和图管理器。本卡解释框架适配合同；[方法选型](../optimization/vllm_ascend_speculative_method_selection.md)负责用户方法与质量选择，[950 Draft FlashAttn](vllm_ascend_cann_flash_draft_backend.md)负责特定backend的device长度、plan和output，二者的已有结论仍保留。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：全文读取DFlash speculator 345行、DFlash2 143行、图管理器152行、patch33行、工厂106行、UT503行、worker补丁90行和pin1行。2026-11-04补读prepare_dflash_inputs.py的Device1–299，结合已读Host300–417形成该文件417行的全文静态阅读。其他有界部分仍是attn_utils1980–2035、aclgraph_utils304–322及utils1906–1922；单文件阅读不代表上游调用者或设备运行已验收。

独立Native 5df63a72只读DFlash815行文件的1–190、343–555，DFlash2的111–265及graph manager131行全文；Main pcp_utils只读1–118，LM-head mixin只读1–65。Native DFlash既有来源归属保留，其余四个依赖不作为新增已摄取覆盖。Main配对pin实际为544f182d9f0c9bfe8bd7645525951d5e3692a542，独立快照不构成安装ABI已验证。

全部上游仅作数据，没有导入或执行UT、JIT、NPU、模型、图捕获、采样分布或性能实验。保持draft、空平台及framework=vllm部分Scope；A2、A3、950及其他硬件、模型的整体适用范围仍未知。

## 工厂、MRO和target/draft配置隔离

init_speculator先看use_dspark，再看use_dflash；DFlash分支在draft architectures包含DFlash2DraftModel时返回AscendDFlash2Speculator，否则返回AscendDFlashSpeculator。不能只用method=dflash区分两者。enforce_eager为真时，工厂浅复制vllm_config和compilation_config，只把副本的CompilationMode设NONE；target原编译与图配置不因此一起被关闭。

AscendDFlash2Speculator以Native DFlash2Speculator在前、AscendDFlashSpeculator在后声明继承。前者的候选buffer构造和_generate_draft胜过普通DFlash生成，同时super链仍经过Ascend初始化、attention与图适配。独立Native片段显示DFlash2按sample_indices取K步hidden，调用compute_candidates和candidate_selector，再交CandidateSampler；不能把这条selector链路替换成K个彼此独立的argmax。

本地DFlash2将_lmhead_tp_sample_draft_supported设False。已读mixin在LM-head TP启用时于构造拒绝该路径，因为它绕过sample_draft的组内行padding；不能靠打开普通草稿padding开关补齐。mixin还分别拒绝若干概率、local argmax和adaptive组合，不能从“普通DFlash继承mixin”推导任意采样配置都支持。

独立Native DFlash构造把query宽度设为K+1，anchor是bonus，明确拒绝sample_from_anchor=True，并将supports_mm_inputs设False。Main propose接受和转发mm_inputs不等于已经支持多模态。不同版本仍须核对实际父类；[DSpark块布局](vllm_ascend_dspark_block_markov_contract.md)可有另一种anchor布局，不能直接套用。

## 输入准备必须分开physical与kernel块

AscendBlockTables按kernel块寻址，而已读Native caller按group传入input_block_tables[gid]与block_sizes[gid]。prepare_dflash_inputs_factory据此保留两种量：closure中的kv_cache_block_size来自set_attn传入的cache_config.block_size，传给prep的block_size则恢复为该表对应的kernel大小。还需核对该物理块配置与实际group缓存一致，不把局部恢复kernel大小当作所有group配置已校验。管理块展开由[MRv2输入坐标](vllm_ascend_v2_request_input_coordinates.md)解释，本卡不重定义其缓存所有权。

提供block_tables时必须有kernel_block_sizes和input_block_tables，否则直接拒绝。factory用`id(table)`建立逐组映射；映射非空而收到未知表对象时拒绝，数值相等、clone或另建view不能自动代替原对象。zip本身没有核对两列表等长，调用方还要验证组数和实际buffer寿命。没有建立任何映射时，包括未提供块表或空配对，会保留caller的block_size；不能把这种回退误当成有效组验证。

例如物理块384、kernel块128时，kernel寻址参数恢复128，而kv_cache_block_size保持384；不能把两个参数统一改成128。Host launcher检查物理块大小能被kernel块大小整除，后者用于表寻址，前者用于DCP ownership及global/local position换算。具体Device地址与截断规则见下一节，静态公式不证明所有调用输入都满足前提。

num_reqs_override在factory和包装函数中透传；Host launcher要求`0 < num_reqs <= input_batch.num_reqs`，据有效前缀的最大scheduled长度安排workers。它不是接受任意override或零请求的统一入口。独立Native已读propose调用没有传这个新增参数；UT也对main-only场景设版本skip，不能由适配器保留参数就声称所有caller版本均已匹配。

## Device输入坐标：位置截断不等于KV地址校验

以下均来自固定ceac的[prepare_dflash_inputs.py](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/spec_decode/prepare_dflash_inputs.py#L39-L297)。`req_idx`是本批请求索引；`idx_mapping[req_idx]`是请求持久采样状态索引，二者不能混用。`query_start_loc`给目标输入的请求区间，`num_rejected`是该请求尾部被拒绝的数量。令区间为`[ctx_start, ctx_end)`，则`num_ctx=ctx_end−ctx_start`、有效尾为`ctx_end−num_rejected`。

| 输出或中间量 | 实际计算 | Agent需要保证的输入条件 |
| --- | --- | --- |
| context positions/slots | 只加载有效context的位置；被拒绝尾部的位置写0、slot写`PAD_SLOT_ID` | 目标区间有效，且`0 ≤ num_rejected ≤ num_ctx`；当前launcher没有检查后者 |
| `last_valid_pos` | 有有效context时取最后一个；全被拒绝时取请求首位置减1，使下一query从首位置重启 | 目标位置是线性标量KV位置；源码明确不支持多模态/M-RoPE坐标 |
| query token | `query_off=0`取bonus；有sampled则读last_sampled，否则读next_prefill_tokens；其他位置用parallel_drafting_token_id | 持久状态索引和buffer寿命匹配，不能用batch行号直接代替 |
| query KV slot | 先用未经截断的`query_pos=last_valid_pos+1+query_off`调用`_dflash_local_slot` | 原始位置、块表列数、有效物理块与buffer容量均需合法 |
| 输出query position、seq_len | position上限截到`max_model_len−1`；seq_len另截到`max_model_len` | 截断发生在slot计算之后，不会修复前一步地址 |
| sample indices/positions | 默认跳过anchor，从query偏移1开始；sample_from_anchor时偏移0且sample position再加1；sample position本身未做上述截断 | caller应核对实际方法的anchor约定，不能因函数有参数就推导DFlash父类支持该组合 |

DCP大小为1时，local position就是原position；大于1时，先以`kv_cache_block_size × CP_SIZE`划虚拟块，再按`CP_INTERLEAVE`条带判定rank所有权，压去其他rank条带得到local position。表列为`min(local_position // block_size, block_table_stride−1)`，只做上限截断，没有负值下限保护；物理块号0或非本rank/无效元素输出`PAD_SLOT_ID`。上限截断会把超范围位置指向最后一列表项，并不报告“越界输入”。因此必须在caller核对位置范围、CP参数、表形状和分配容量，不能把有clamp视为完整地址安全证明。

每个请求用商余数分区让多个worker处理互不重叠的context、query和sample范围。图padding在全grid分摊：query_start_loc尾部写有效query总数，seq_lens尾部写0，sample indices/positions写0、映射写−1，query slot尾部写`PAD_SLOT_ID`。这不表示所有input_ids/positions缓冲尾部也都被初始化；下游须遵守有效长度。Host按context/query/sample工作量及vectorcore数安排workers，并要求物理块大小可被kernel块大小整除；未对所有上述语义前提统一assert。

排查草稿越界时，应先保存请求区间、拒绝数、原query位置、输出截断位置、CP归属和最终slot，再核对采样状态索引。仅比较截断后的position或最终输出文本会漏掉地址错误；本次只验证源码解释，没有执行kernel、graph或采样分布测试。

## set_attn、全局callback与引用寿命

set_attn先委托父类，再创建draft KV group数×max_num_tokens的int32 _context_slot_mappings。backend收集按真实draft_attn_layer_names与每组layer names求交，再从实际layer对象读取；不能把target、indexer或猜测层号填作草稿backend。

随后它将Native dflash模块的prepare_dflash_inputs替换为当前factory closure。该赋值不是每次propose的临时作用域，也没有在本方法返回时恢复；closure保存当前表对象的identity映射。多实例、重建KV、换表或不同导入绑定并存时，必须确认调用的callback仍属于当前speculator。不能把某次set_attn成功当作进程内所有实例已经隔离。

worker导入patch_dflash_speculator后，还替换Native graph模块的build_attn_metadata、Native speculator持有的DFlashCudaGraphManager以及Native DFlash2的_selector_walk_kernel。按名导入和模块属性是不同绑定，需要记录真正Worker中的引用，不能只检查补丁文件存在。

build_attn_metadata_wrapper和model_capture_wrapper分别临时替换元数据函数及模型对象，并在finally恢复。它们为已读调用区间提供恢复路径，没有证明任意并发实例或嵌套外部修改均有隔离，也不承担全部父类/设备资源回滚。

## padded query与精确KV长度分开

build_draft_attn_metadatas按padded请求数×num_query_per_req创建FULL descriptor，但传给uniform builder的num_reqs仍取真实input_batch.num_reqs，并传本组causal映射与CPU长度上界。_update_draft_attn_metadata随后将每层actual_seq_lengths_q重写为Q、2Q、…、padded B×Q，使FIA TND累计query末项覆盖捕获图的query token数。

这个重写不等于精确KV长度校正，也没有更新所有backend字段。它直接访问metadata对象属性，不能当作任意mapping、None条目或外部backend对象的完整schema校验。[DSpark长度诊断](../../runbooks/precision/vllm_ascend_dspark_query_kv_length_mismatch.md)和[Draft FlashAttn](vllm_ascend_cann_flash_draft_backend.md)分别保留其有效KV与device长度方案；不要用target optimistic上界替换已经拒绝修正的device真值。

propose先保存当前input_batch，只有dummy_run且skip_attn_for_dummy_run同时为真时把传给父类的DP sync state置None。该profiling路径使用自己的query token数，不能沿用target的DP数量；普通请求、只有一个标志为真的路径仍保留传入state。每批num_speculative_tokens及其他新参数也继续透传，不能靠旧签名或参数位置猜配对。

load_draft_model另用disable_profiling_chunk_for_draft作用域：PP target且启用了相应profiling chunk配置时，按嵌套配置优先级构造禁用副本，临时重新绑定additional_config并finally恢复。这个局部加载处理不证明DFlash获得完整PP支持，仍要遵守[PP组合边界](vllm_ascend_pipeline_partitioning.md)。

## DFlash与DFlash2的实际图门禁

普通AscendDFlashSpeculator在enforce_eager为真时把传给父图初始化的模式改NONE。父类创建query_cudagraph_manager后，本类补绑speculator和update_stream；这些引用供后续参数刷新使用。独立Native还按attention的UNIFORM_BATCH能力选择FULL_DECODE_ONLY或NONE，不支持DFlash的PIECEWISE；这只是该快照的对照合同。

ceac版本的DFlash2覆盖更严格：enforce_eager为真才委托父类且强制NONE；否则在父manager初始化前抛NotImplementedError。其类docstring关于_generate_draft进入capture的结构说明，不能越过这个真实guard；“未来版本支持”的报错文字也不是当前图支持承诺。target可以保留自己的图模式，不能为解决draft拒绝而无记录地修改整服务配置。

DFlashAclGraphManager从实际_capture_descs提取capture_sizes，而非直接使用原始配置尺寸；它使用独立draft参数桶，不套Eagle的prefill/decode分桶。manager只有在父类判断需要capture时设置相应draft graph params，不能由桶已初始化反推图已捕获。

Main capture签名同时接收precompute_context_kv和prepare_forward，但实际只向父类传prepare_forward；前一个参数在方法体中未使用。独立Native graph manager把prepare_forward(num_reqs, attn_metadata)记录在query forward之前调用。因此不能照Main docstring概括成任意旧/新版本自动互换：安装caller必须真正提供匹配的callback和签名，且Main配对pin仍需独立验证。

## replay分支与selector边界

run_fullgraph先从attn_backends取第一个backend。只有所有backend都精确等于AscendFlashAttentionBackend类时，才直接走父replay，依赖该backend在图内读取持久device长度。子类不等于该精确比较；空mapping也不能当成合法无attention路径。

其他分支先构建draft metadata，再按首backend是否适用updatable graph选路。传统路径等待更新流与当前流的顺序，调用父replay后在draft forward context中更新full graph参数；源码仍保留hybrid backend TODO，不能把一个代表backend用于所有混合层当作已证明正确。updatable路径按draft metadata解析任务，等待后replay，再提交graph.update。Python返回、地址没变或调用顺序不能代替实际设备依赖和数值验证。

_selector_walk_kernel_ascend替换Native同名符号。已读Main kernel按previous candidate串行walk，greedy并列分数取最小候选下标，负请求映射不写有效输出；概率分支由SAMPLE_PROBABILISTIC控制，不启用时即使请求temperature非零也走greedy。Native CandidateSampler按draft_logits是否为None传该flag，并把walk使用的scores交给外部proposal cache kernel。

该Ascend kernel以log(1-u)替代log1p相关调用，并static_assert拒绝USE_FP64；随机seed、position和candidate键还转int32。代数说明不构成浮点端点、超int32范围、跨实现同seed一致或采样分布已验证的证明；Native proposal cache kernel及完整拒绝器也未在这里闭合。不要把概率缓存存在解释成任意词表、参数或模型质量已经通过。

## 交付、验证与停止条件

UT503定义工厂/eager隔离、加载成功与异常后的配置恢复、精确device长度与请求重排、padded query、profiling DP、draft层过滤、int32 slots及physical/kernel参数转发。selector测试是纯Python greedy镜像，kernel不能在CPU启动；部分输入准备场景另有版本skip。它们是未执行的测试定义，不能登记为NPU、图或分布验收结果。

Agent交付应保存Main/实际配对Native与安装版本、target/draft config、最终类/MRO、全局callback和表对象identity、每组物理/kernel块大小、Q/K、真实/padded请求与token数、精确device/Host上界长度、graph descriptor及selector配置。覆盖换表、多group、拒绝与重排、grow/shrink、dummy profiling、加载异常、target/draft交替及eager/FULL的实际允许分支，再对齐草稿输出、proposal缓存和target验证。

callback归属错误、未知表、块粒度不匹配、query末项不覆盖图、draft图被guard拒绝或数值异常时，先恢复明确匹配的版本和已验证的无投机/eager配置，停止性能结论。分别测输入准备、context KV预计算、draft、selector与target验证；不以少一次同步、替换kernel或启动成功代替端到端收益。


## 2026-11-03 main 增量：LiLiCorr 词表布局 guard

固定3164adc8fe75892fbf7f99f524bb72fddf1e6efd新增AscendLiLiCorrSpeculator40行全文读取；其Native LiLiCorr父类与完整correlator没有在本节闭合。它以LiLiCorrSpeculator在前、AscendDFlash2Speculator在后继承，声明复用上游评分及Ascend DFlash2运行guard，不能据父类名称把普通DFlash checkpoint替换成LiLiCorr。

load_draft_model委托super加载后，分别检查target_embeddings与candidate model.lm_head的parallel_mode，遇FINE_GRAINED或PCP_X_TP便NotImplementedError。注释给出的原因是candidate只沿标准TP聚合词表，candidate IDs为[requests,steps,topk]而Ascend特殊embedding交换使用平坦行；缺失维度/组内聚合不能靠给buffer扩容修复。普通TP被允许不等于整个设备/模型组合通过；缺parallel_mode属性也不能作为语义布局已校验的证据。

文档要求MRv2、匹配的专用checkpoint、draft eager并保留target模式；训练block size、top-k/卷积几何、真实q与独立RNG按[投机选型增量](../optimization/vllm_ascend_speculative_method_selection.md)核对。这里只确认新wrapper及文档有界区间，没有执行CI、模型、候选kernel、概率或NPU图。原ceac工厂分派及本卡明确保留的Native父类、外部kernel未闭合边界仍有效；输入准备Device已按前文补读。不能由新wrapper存在推原工厂已有其分支。

## 2026-11-03 发布快照：DFlash2 图 guard 迁移

本节固定 `5f5e25dd94db85b59251be7d3baf7c808475b6d7` 的 speculator/model 差异及公开中文文档。原 ceac 的 `init_cudagraph_manager` 拒绝非 eager 路径已在这个版本删除；前文“误入图路径”的诊断须先确认版本。它继承普通 DFlash 图管理，draft enforce_eager=true 仍保留自己的 NONE 路径，target 不因此一起关闭图。

新增 `_score_candidates` 在 backbone forward context 退出后，显式创建局部 ForwardContext，BatchDescriptor 的 num_tokens 取 `candidate_ids.shape[0]`（请求数），不取展平 draft token 数。selector 内层图模式为 NONE，由外层 DFlash ACL 图捕获编译后的 scoring、TopK、路径采样和 proposal cache 更新；局部 context 不携带 target MoE 的 DP同步或 attention metadata。model 的 `dflash2_candidate_selector` tag 使不同输入几何的 selector 与 backbone 使用独立编译缓存 namespace。

后续文档的非因果滑窗 band4、K+1 capture 预算与 eager/graph 对照见[投机选型增量](../optimization/vllm_ascend_speculative_method_selection.md)。发布源码的 Native main pin 为 `24420b7a341af37a9bc3186e6fc6062512e0aa58`，不同于前文544f配对和独立5df快照；本节只确认 pin 与所述 Ascend 接线，没有闭合该新 Native 父类全部 ABI 或运行设备图。`test_dflash2_v2_acceptance` 的两NPU定义不能写成本仓已通过结果。
