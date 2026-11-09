---
type: Guide
title: vLLM Ascend MRv2草稿执行：AR族适配、KV共享与ACL图重放
description: 聚合Eagle、MTP、Gemma4、StandaloneAR和MultiModuleMTP的真实工厂与继承合同，核对dense draft配置、correction token长度、模块索引与反馈状态、共享KV尺度、replicated
  PCP、逐步metadata及ACL graph的捕获/重放和版本门禁。
aliases:
- AscendEagleSpeculator
- AscendGemma4Speculator
- AscendStandaloneARSpeculator
- AscendMultiModuleMTPSpeculator
- AscendTargetDependentARSpeculator.build_draft_attn_metadatas
- AutoRegressiveAclGraphManager
- prepare_replicated_pcp_config
- SparseKVOffloadMetadata.build_kwargs
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.speculative_decoding
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/multi_module_mtp/speculator.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/eagle/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/standalone_ar/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/gemma4/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/pcp_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/target_dependent_ar/aclgraph.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/target_dependent_ar/sparse_kv_offload.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_eagle_speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_multi_module_mtp_speculator.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_gemma4_speculator_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_eagle_aclgraph_source_regression.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/mtp/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/target_dependent_ar/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/v1/worker/gpu/spec_decode/multi_module_mtp/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/v1/worker/gpu/spec_decode/standalone_ar/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/v1/worker/gpu/spec_decode/gemma4/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/v1/worker/gpu/spec_decode/eagle/speculator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/v1/worker/gpu/spec_decode/target_dependent_ar/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/v1/worker/gpu/spec_decode/target_dependent_ar/cudagraph_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/v1/worker/gpu/spec_decode/speculator.py
  role: constraint
created_at: '2026-11-03T01:35:09Z'
updated_at: '2026-11-03T01:35:09Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MRv2草稿执行：AR族适配、KV共享与ACL图重放

## 任务与版本边界

新模型接入MRv2投机解码时，应按实际speculator区分配置、KV读写、递归状态及图执行。Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的Ascend wrapper与实际配对Native544f182d9f0c9bfe8bd7645525951d5e3692a542共同决定本卡合同；Native字节均来自该固定Git对象，独立5df快照不是本卡继承依据。

本卡聚合框架执行差异，方法与质量选型沿用[投机方法指南](../optimization/vllm_ascend_speculative_method_selection.md)，模型内部VWN见[Eagle3接入](vllm_ascend_eagle3_vwn_draft_contract.md)，LM-head/embedding所有权见[MTP加载诊断](../../runbooks/precision/vllm_ascend_mtp_head_ownership.md)。[DFlash接入](vllm_ascend_dflash_runner_graph_contract.md)、DSpark及310P有独立实现，不能从本卡外推它们具有同样的KV、metadata或graph语义。

Main四个主要wrapper、MTP wrapper、共享TargetDependentAR、ACL manager、PCP配置helper、sparse metadata helper及工厂均完整阅读；配对Native只覆盖文末明确的类/接口范围。三个UT只读未执行。本次未运行上游导入、Triton/JIT、模型、NPU、通信、图、精度或性能实验；整项硬件与模型组合保持未知，卡为draft、空平台和framework=vllm部分Scope。

## 工厂与真实Worker接线

init_speculator先处理ngram和extract_hidden_states，再按DSpark、DFlash、Gemma4 MTP、普通MTP、MultiModuleMTP、Eagle、通用draft model的顺序选类。Gemma4分支早于use_eagle，Step3p5 MTP不走普通AscendMTPSpeculator分支；不能用method=mtp或类名相近代替真实工厂结果。enforce_eager只复制传入VllmConfig和compilation_config后设置CompilationMode.NONE，不同时关闭原target全部配置。

Main NPUModelRunner185–243显示只在PP末阶段创建speculator，使用替换后的AscendRequestState，随后把Runner的update_stream赋给speculator；FULL配置才创建该stream。图manager初始化还需把当前speculator和stream补绑到manager，不能只构造manager就开始replay。

patch_eagle_speculator替换Native target_dependent_ar模块持有的SpeculatorCudaGraphManager符号。Worker导入补丁完成这项赋值；310P随后又以自己的manager覆盖，导入顺序具有实际作用。MultiModuleMTP则直接构造Ascend manager。仅检查补丁文件存在、Native原始定义或先前按名导入对象，都不能确认当前Worker正在消费哪一个manager。

| 实际路径 | 草稿语义 | 首要接入门禁 |
| --- | --- | --- |
| AscendEagleSpeculator | 共享Ascend AR循环，Native Eagle负责draft模型加载 | dense draft配置、辅助hidden与词表映射 |
| AscendMTPSpeculator | 薄继承层，MLA等处理在共享base | 实际backend、head及反馈hidden所有权 |
| AscendGemma4Speculator | 目标相关、Q-only、读取target共享KV | matching attention类型、KV scale与impl共享目标同步 |
| AscendStandaloneARSpeculator | 独立小LM，step0扩展输入并加入correction token | expanded位置、长度上界及eager边界 |
| AscendMultiModuleMTPSpeculator | 每步选择MTP module/head，滚动一段输入 | spec_step_idx、re-prefill缓存与共享metadata |

## dense draft与replicated PCP配置

Eagle和Gemma4 wrapper对draft显式设PCP=1、enable_expert_parallel=False和enable_eplb=False，target是MoE并不使dense draft也成为MoE。共享Ascend base将draft PP设为1，先用target派生配置通过重建，再换入draft model_config并更新is_moe_model；这与对最终draft配置重新执行所有校验不同。

prepare_replicated_pcp_config在target PCP>1时创建执行副本，暂设DCP=1完成重建后恢复target DCP值；源码明确此恢复不重跑DCP校验或重算相关设置。只有PCP维承担并行且target启用EPLB时，它为draft关闭EPLB并把冗余专家数归零，target配置保留；特定DP共享Engram状态也只在draft副本关闭。不要从“恢复了DCP字段”推导任意PCP/DCP/EP/EPLB组合均正确。

disable_target_pcp_for_replicated_draft检查共享model_state确实指向目标pcp_manager，再临时置None并在finally恢复；这是防止复制草稿再次被target PCP切分的作用域。它不替代token/hidden的全局恢复和同步。[PCP批次生命周期](vllm_ascend_pcp_batch_restore_lifecycle.md)继续负责实际global/local布局与还原。

PP target构建PP1 draft时，disable_profiling_chunk_for_draft按嵌套配置优先级复制并关闭profiling chunk，临时重绑additional_config后finally还原。它不永久修改target，也不证明每个draft方法获得PP支持。共享base在PP>1加载后将supports_mm_inputs设False，须与公开PP组合门禁共同检查。

## Standalone AR：correction token与长度上界

配对StandaloneAR为每请求预留一个extra query，step0的expanded输入包含接受窗口、correction token及保留的拒绝槽。Ascend metadata hook只在step==0把seq_lens_cpu_upper_bound的有效请求前缀加1并clamp到max_model_len，传新Tensor给父builder，保留input_batch原上界。positions在step0取expanded_positions，后续取input_buffers.positions；num_tokens来自传入query_start_loc的末项，不能混用target原始长度。

metadata工厂显式选择DecodeOnly，但不等于step0每请求只处理一个token。配对父类后续decode先初始化seq_lens为target长度−num_rejected+1，每次forward前再递增；给uniform metadata的step为实际draft step+1，包含correction token。若仅修step0 Host长度，仍需验证GPU位置、slot、拒绝数与后续上界同步。

固定544的StandaloneAR.init_cudagraph_manager和capture为空，模型forward使用CUDAGraphMode.NONE，并显式supports_mm_inputs=False；Main wrapper没有补全这些能力。其propose虽然接受num_speculative_tokens参数，已读循环仍按self.num_speculative_steps生成，不消费该每批参数。不能由公共签名直接宣告动态K、图或多模态支持。

## Gemma4：共享KV、scale与状态副本

配对Gemma4Speculator按sliding/full attention类型，把每个draft层映射到target同类型最后一个非KV-shared层。找不到候选时warning并跳过；这不是已成功建立全部映射。target层prefix从实际attention层名取得，还需static_forward_context中存在对应层对象。

共享cache Tensor不自动共享Attention模块上的量化scale。配对helper对_k_scale/_v_scale做detach.clone并保留draft原注册类型，复制Host float和CPU缓存；这避免直接别名target参数，但也意味着之后更新target scale不会自动刷新draft副本。Main在late-bound sharing完成后再将kv_sharing_target_layer_name同步到Ascend attn.impl，只对有target且有impl的层赋值，日志数量不是所有层成功的强制断言。

Main _prefill遇PrefillNoCache时浅复制metadata对象，把这些条目改为PrefillCacheHit后传父类，保留调用方原状态；其他状态保持语义。浅复制不会使其内部Tensor成为独立存储，不能在此基础上任意原位改共享数据。配对embedding共享只在PP world_size==1进行，不能外推PP末阶段也持有可共享target embedding。

Gemma4继承advance_draft_positions=False，配对Native因此保持Q-only位置和seq_lens，不写新的KV；普通Eagle/MTP会推进。Main共享CPU更新函数仍以base长度+step生成Host列表，generic FIA参数也按步递增，未在这些函数里检查该property。因此多步Gemma4在eager/FULL、具体backend和CPU/device长度上的一致性必须单独闭合，不能把普通MTP的+step规则无条件赋给共享KV草稿。本卡没有证明运行错误或给出数值修复。

## MultiModule MTP：模块、head与滚动反馈

Main在load_model前修补Step3.5的layer_types：当长度不足num_hidden_layers+num_nextn_predict_layers时，以sliding_attention补齐，并可能同时更新target hf_config。它只填缺少尾项，不验证checkpoint是否按相同attention类型训练；配置补齐不能替代模型结构验收。draft配置使用PP1和get_draft_quant_config，再由load_eagle_model加载。

配对_generate_drafts在每步传spec_module_idx=step到_run_model，实际模型入参为spec_step_idx；compute_logits/get_top_tokens也接收同一step。因此多个MTP module可有各自head，不能把它等同一个module递归K次或始终取首层head。模型返回tuple时，第一项用于本步logits，第二项供下一步hidden反馈，不能重复final norm或交换两者。

循环开始缓存末尾token id、target hidden与可选embedding，以便下一轮拒绝后重做后续module的KV。每步从last_token_indices采样，随机key位置初值为position+1并逐步递增；chunked-prefilling请求可用draft_input_id_overrides的已知未来token替代采样结果，再滚动input ids/embedding。清空缓存、强行以采样token替代override或只滚动ids都可能改变协议。

配对类的propose重建slots，并将不对应真实draft token的尾部slot标为padding；只在step0构建一次attention metadata，多个module forward共享。Main replay hook从当前self.input_batch重建FULL metadata并筛到draft层，返回单元素list，不缓存上轮metadata。is_prefilling有效前缀任一为真选ChunkedPrefill，否则DecodeOnly；CPU长度只取真实请求，descriptor保留padded请求/token数。

Main build_fia_params为每个draft attention层输出一个layer_name及query/KV长度、block table条目，而不是每个step复制一组。同一图中的任务按真实层名匹配；把普通AR每步一份metadata的规则移植过来可能使任务数量不符。MultiModule不继承LmheadTPDraftSamplingMixin，不能由普通AR的LM-head TP门禁与padding推出本路径也具备相同支持。

## 共享AR metadata：padded批次、逐步状态与拒绝边界

共享base按第一个可执行draft attention backend区分DSA、MLA、SFA和GQA，其他backend报错。DSA/SFA由自己的builder维护逐步稀疏状态，跳过generic MLA/GQA初始化和CPU更新；不能拿空generic更新列表证明该backend无需状态推进。

GQA/MLA FULL decode先按padded请求数重建一token/request metadata，再为后续K−1步创建副本，使用各自CPU长度buffer。MLA以及DCP下GQA还复制decode对象，避免各步覆盖同一组长度字段；这仍是浅复制，底层Tensor与block table的别名范围应按真实字段确认。

_get_seq_lens_cpu从target AscendInputBuffers取足够长的持久CPU存储，不用可能只有active请求的紧凑seq_lens_np。_calc_next_seq_lens_cpu把base+step限制到max_model_len，并将padded请求长度归零。源码明确没有在该Host计算中扣num_rejected，这是当前对齐选择；它不是精确设备有效KV长度或接受后序列长度的证明。[拒绝与重采样](vllm_ascend_mrv2_rejection_resampling_contract.md)继续维护接受数和设备状态。

replicated PCP prefill会刷新draft全局block/slot，FULL padding还为额外token创建dummy请求边界和零缓存长度。不同query长度不能直接用uniform decode metadata代替。propose保存当前input_batch，并在复制PCP路径让每个DP rank参与draft同步；临时关闭target PCP只是其中一环。

## ACL捕获、重放与版本差异

共享AR分别有prefill和decode manager。capture清零last_token_indices/idx_mapping，执行对应begin/end hooks；K=1只捕prefill。FULL decode把后续多步合在一次图replay，而eager/PIECEWISE委托父循环逐步执行。实际父类还可依据supports_decode_metadata_update选择fused循环，不能只阅读Main _multi_step_decode就断言所有运行都必经该覆写。

AutoRegressiveAclGraphManager从实际_capture_descs收集捕获token尺寸，以decode_query_len>1区分draft prefill桶和decode桶。配置中的原始sizes、物理捕获token数、真实请求数和K+1 query宽是不同量。manager需当前speculator、update_stream和匹配descriptor；桶初始化不能证明图已捕获。

MultiModule Main遇piecewise模式就降为FULL_DECODE_ONLY或NONE；paired Native仅在未启用breakable graph时作此降级。Main breakable初始化没有照Native显式传按spec_step_idx取module索引的key_fn。不能凭breakable flag就证明多module specialization完全等价，先按实际允许路径验收。

配对Native manager可按每批num_speculative_tokens专门化descriptor，找不到专门化图时降NONE；Main自定义capture没有完整复用这条specialize_spec_tokens捕获入口，并在decode capture传静态num_speculative_steps。结合继承fused路径和每批K传播逐项核对，不能由propose接收动态K就宣布FULL图覆盖所有K。

replay先重建本批draft metadata，再按backend选择传统参数更新或UpdatableGraph。传统路径让update_stream等待当前流，调用父replay后在draft配置和forward context中更新图参数；updatable路径先resolve_tasks，再等待、父replay、graph.update。传统分支仍保留hybrid backend TODO。Python顺序不能代替设备事件、跨批次依赖或数值正确性；[图生命周期](../../concepts/frameworks/vllm_ascend_aclgraph_replay_lifecycle.md)保留公共同步合同。

torch_gather_wrapper在作用域内把out=路径改为先普通gather再赋值out[:]，finally恢复torch.gather；这是进程全局函数临时替换，不是每个对象独立配置。异常恢复语句不证明并发多个外部修改互相隔离，也不能把源码注释的问题报告当作本次设备复现。

## Sparse offload metadata的逐步所有权

SparseKVOffloadMetadata仅在enabled时为K步各分配稳定req_ids和token_to_req CpuGpuBuffer。build_kwargs按step索引选本步buffer，以真实query_start末项确定num_tokens，FULL才将token范围扩到descriptor的padded数；dummy批次使用offload-dummy标识。返回值还携带offload pool的CPU slots/active前缀和copy_sfa_draft_index=step。

该helper没有为任意越界step提供额外恢复，也不证明pool内容、异步拷贝或manager已完成。稳定buffer服务图/跨步引用，不能随意把全部步折叠为同一buffer；真实offload调度及设备复制消费者在本卡范围之外。

## 新模型验收顺序与证据范围

先记录工厂结果、MRO、外层/草稿配置、量化与head所有权、实际attention backend和target/draft层名，再分别核对输入、correction/拒绝窗口、双hidden输出、每模块head、KV-sharing和scale。随后覆盖K1/多步/每批K变化、真实与padded请求、chunked prefill、请求重排、dummy、PP/PCP/DCP的实际允许分支；最后对齐eager与图的token/hidden及数值，再测接受率、TTFT/TPOT和峰值内存。

三个Main UT定义了Gemma4路由/MRO、共享目标同步、原metadata保持，MultiModule当前batch重建、draft层过滤和状态选择，以及ACL补丁符号的AST/文本断言。它们未在本次执行，也没有验证真实Triton kernels、NPU attention、设备事件、动态K图、多卡或端到端质量。

Main sources中除model_runner185–243外均按整文件阅读，保留旧canonical owner。paired Native范围为MultiModule1124行文件的1–477、Standalone540行文件的1–409、TargetDependent994行文件的1–682；其Triton kernel bodies未在本卡审读。Gemma4187、Eagle18及SpeculatorCudaGraphManager117行全文，DraftModelSpeculator603行文件只读107–213、278–402、568–603。模型loader、采样kernel、全部attention/device消费者和实际安装ABI仍需相应主题与运行证据，不因本卡聚合而计作全执行闭包。
