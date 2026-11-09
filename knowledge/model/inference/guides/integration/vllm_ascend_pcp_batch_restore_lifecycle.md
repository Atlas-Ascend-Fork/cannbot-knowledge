---
type: Guide
title: "vLLM Ascend PCP 批次恢复：global/local布局、图请求形状与slot生命周期（AscendPCPManager）"
description: "沿 AscendPCPManager、AscendPCPAttentionContext、restore_for_sampling、restore_hidden_state_buffer、refresh_gathered_slot_mappings 与 get_global_graph_num_reqs 核对全局/局部批次、actual与padded请求/token、最后PP hidden恢复、一次性标记及rank-major slot刷新，保留KPool策略与配对版本边界。 AscendPCPManager.__init__按精确0.32.0选择参数；Native factory的shard flag（pcp_shard_decode_requests/shard_decode_requests）、独立5df与实际paired544须分别复核。"
aliases:
- AscendPCPManager
- AscendPCPAttentionContext
- restore_for_sampling
- restore_hidden_state_buffer
- refresh_gathered_slot_mappings
- get_global_graph_num_reqs
- AscendPCPManager.__init__：版本参数与Native factory的shard flag
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.parallelism
- topic.graph_execution
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/pcp_manager.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/pcp_manager.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_pcp_manager_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/common_cp.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_model_runner_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_mtp_pcp_speculator_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/parallel.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T09:16:13Z'
updated_at: '2026-11-04T03:49:24Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend PCP 批次恢复：global/local布局、图请求形状与slot生命周期

## 适配任务与固定范围

新模型接入MRv2 PCP，或出现采样行错位、图请求数不匹配、重复gather、KV写地址跨rank错位时，先标注每个对象是global调度顺序、rank-local片段顺序还是rank-major gather顺序。本卡负责Manager生产与恢复生命周期；[输入坐标](vllm_ascend_v2_request_input_coordinates.md)负责持久request slot、batch与logit坐标，[CP设计](../../concepts/frameworks/vllm_ascend_cp_cache_mapping.md)负责缓存映射原理，[GQA/CP](vllm_ascend_gqa_cp_history_current.md)、[SFA地址](vllm_ascend_sfa_replicated_cache_views.md)和[O投影](vllm_ascend_cp_oproj_weight_protocol.md)各自保留消费者合同。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读worker/v2/pcp_manager.py750行、对应UT1343行、patch_model_runner.py224行、common_cp.py342行和pin1行。独立Native固定5df63a7203cdb9328d824a27b682e77c7b9928be，全文读gpu/pcp_manager.py859行；另外六个明确有界范围是Main model_runner285–413/475–495/810–850/1050–1078、Runner UT440–525/1253–1315、MTP PCP UT436–487、utils190–213、platform1461–1515及Native config/parallel615–642。

这12个范围是6全文/6有界，不表示整个Runner、MTP、模型、attention Device算子或分布式实现闭合。Main实际配对pin为544f182d9f0c9bfe8bd7645525951d5e3692a542；独立Native快照只作源码对照，未验证实际配对ABI。全部来源和UT仅作数据，没有导入或执行上游、JIT、collective、图或NPU，保持draft、platforms=[]与部分framework Scope。

## 先记录对象布局与持有者

| 对象 | 所属顺序和有效范围 | 适配时的约束 |
| --- | --- | --- |
| global_batch | 本轮完整scheduled请求与token，保留全局投机信息 | 不用局部片段行数替代global请求/token计数 |
| local batch | 一个rank持有的decode和DualChunkSwap头尾片段 | 同一persistent请求slot可以出现两个局部请求行 |
| padded_gather_idx / hidden_restore_idx | rank-major采集顺序与global恢复顺序的映射 | PAD、复制行和真实owner分别处理，长度一致不证明顺序一致 |
| global slots / gathered slots | 全局token地址与按rank-major重排的写地址 | 修改global slots后需要发布刷新，不能沿用旧gather视图 |
| graph descriptor | 当前模型执行所需padded请求/token形状 | 配置模式、descriptor模式、真实数量与buffer容量分别保存 |

AscendPCPManager构造自己的AscendInputBuffers，请求容量为2×max_num_reqs以容纳两段，token容量仍由max_num_tokens限定；query_start_loc去掉FIA额外槽以匹配基础布局。全局/gathered slot及PAD标量转换为实际block-table slot dtype，不以通用Native默认dtype推断Ascend地址ABI。持久buffer地址稳定提供复用条件，不能代替图重放或并发隔离验证。

## 分片策略与配置门禁不能拆开判断

is_decode_sharded使用注入的vllm_config，而不是任意当前全局配置。is_pcp_decode_sharding_enabled在模型有KPool属性时返回False：model_uses_kpool_indexer检查hf_text_config或hf_config是否存在index_kpool属性，不检查其真值或正数；其他情况要求PCP>1且DCP==1。

分片decode的_iter_rank_chunks跳过scheduled为0的请求，只对实际decode轮转owner；多token speculative verification query整体交一个rank，不逐token轮转。owner随本轮调度顺序改变，不能缓存上一步请求归属。prefill继续DualChunkSwap的2P分块与头尾配对；非分片路径委托Native基础迭代器，constructor传入的shard_decode_requests仍影响基础行为。

Native独立快照先形成RankSegment，再按decode优先重排；一个请求的头尾片段可对应相同持久slot。_build_batch_layout生成gather/restore逆映射，复制行只保留一个canonical写入者，非分片复制decode通常由rank0写KV，PAD和重复写行的write mask为False。DCP下过短prefill可走复制，不能一律按双段长度推断每rank都有有效query。

Main validate_config在PCP<=1时直接返回；PCP>1拒绝encoder-decoder、LoRA、非mtp/eagle3/dspark的speculative method和配置CUDAGraphMode.FULL。supports_mm_inputs参数未使用，也未调用Native完整校验；没有拒绝某组合不是模型/硬件支持证明。[DFlash接入](vllm_ascend_dflash_runner_graph_contract.md)中存在PCP helper，不会越过这个当前Manager门禁。MM embedding/EVS完整生产链、其他并行组合和全部Native限制仍需独立核对。

## 全局与局部的请求维、token维和padding

Native partition保留global batch，再从rank片段建立local ids、positions、请求映射和query前缀；local logits不直接采样，恢复global hidden后才使用全局请求布局。local draft元数据可清空而global仍保留，不能把局部None解释成全局没有投机状态。

Main _finalize_partition复制本轮dummy/CPP标记，扩展hidden_restore_idx至global padded extent并以0填索引尾部。CPU seq_lens按局部computed+scheduled产生上界；独立Native device路径按本轮选定positions计算精确局部长度。CPU上界不等于device真值。空rank保留一个零token placeholder请求，清CPU长度与上界；padded请求行也清零。不能因本地没有有效token就跳过全局协议要求的collective。

prefill存在时按局部状态重建attention分类；decode-only保留global attn_state，避免因本地只有部分token误判全局阶段。replicated decode graph另检查token和请求容量，复制全局query布局，并清padding ids、positions、is_padding、seq及DCP长度尾段。真实extent继续单独保存，不能从buffer view首维恢复真实调度量。

_full_decode_requests_are_token_sized只在没有prefill、配置FULL_DECODE_ONLY且没有draft tokens时成立；单token decode才可将请求维pad到token数。多token投机query即使是纯decode，也要保留请求维，不能把padded token数直接当num_reqs。

get_global_graph_num_reqs仅对decode-sharded且当前descriptor.cg_mode=FULL放大全局请求数，取local_num_reqs×PCP、global请求容量与max_num_tokens//uniform_query_len的最小值。uniform且非零query长度是caller前提。配置FULL被validate拒绝，与FULL_DECODE_ONLY选中的本轮FULL descriptor属于不同层次，不据后者宣布任意configured FULL已受支持。

## capture、CPP与本次dummy作用域

普通capture/profile入口按定义时vLLM版本选择prepare_inputs_to_capture或prepare_inputs_for_capture_or_profile钩子，准备rank-local dummy与global形状。CPP逻辑dummy采用实际partition并以NONE descriptor处理，不照搬普通FULL捕获的padding假设。

build_attention_context在dummy路径消费本次传入batch；不能把Manager此前保存的real global_batch拿来替代当前dummy。sharded dummy重建global graph请求/token extent、dummy表与PAD slots，构造全局RoPE后恢复局部positions的RoPE视图。相关buffer复用和初始化行为不是所有消费者已完成capture/replay的证明。

## hidden恢复与一次性采样标记

restore_hidden_states在非最后PP rank原样返回。最后PP调用基础gather/restore；没有global batch时保持基础结果，否则必须恰好得到global num_tokens_after_padding行，不匹配直接RuntimeError。真实token之后的padding行清零，不能仅依靠restore索引尾部取row0就把PAD内容当安全零值。

当存在speculative_config、decode sharding开启、global batch存在且不是dummy时，_restore_unpadded_global_batch使恢复结果裁到实际num_tokens；dummy图路径仍维持padded布局。_expose_unpadded_global_batch用replace返回实际extent及真实query边界视图，不原地破坏target捕获所持有的batch。

restore_for_sampling同时处理main与aux hidden。_sampling_hidden_restored为真时只消费一次并清回False，跳过第二次gather；否则委托Native恢复main/aux/global batch。需要unpad时三者按同一真实extent处理。相同Tensor行数不能判断local/global布局，graph padding恰好可能使两者shape相同。

所读Runner sample_tokens每步先清marker。非末PP阶段将execute state.input_batch换为global；最后PP且replicated_pcp时，_restore_replicated_draft_target_states还可恢复模型自有MTP buffer、main和aux。只有main hidden存在才设置已恢复marker；仅恢复模型自有buffer不触发这个标记。该局部协议没有提供异常事务、并发复用或全部PP传输正确性的证明；后者见[PP载荷合同](vllm_ascend_pp_typed_transport_contract.md)。

restore_hidden_state_buffer仅在最后PP执行，从padded_gather_idx长度/PCP得到local padded前缀，恢复后copy回模型buffer前部；caller仍须保证容量、对象寿命及后续消费者使用global实际extent。

broadcast_replicated_hidden_states只在replicated PCP执行，对实际num_tokens前缀取contiguous，并由PCP rank0广播。last_hidden与hidden是同一Python对象时只发一次；不同对象即使共享storage也不自动按相同对象去重，不能擅自拓展成通用alias分析。MTP PCP UT仅定义实际前缀广播检查，未执行真实网络。

## slot的rank-major扩容和刷新

prepare_slot_mappings先调用基础实现将global slots重排为rank-major布局。decode-sharded、非纯decode或没有额外graph padding时直接返回；replicated decode需将每rank紧凑区间分别扩展成[rank0实际|rank0 PAD|rank1实际|rank1 PAD|…]，而不是只在全buffer尾部加PAD。

紧凑slot_mappings是可复用目标buffer的view。每rank3行扩到graph4行时，先写rank0 padding会覆盖rank1原始源区；源码因此在原地展开前clone紧凑映射，再逐段copy并fill(-1)。rank跨度不能整除PCP时显式拒绝，不以截断掩盖布局错位。这里的clone解决同buffer重叠写，不能因而认定所有跨流生命周期已经闭合。

模型或回放修改global slots后，refresh_gathered_slot_mappings从实际global token前缀重新_convert_to_gathered_slot_mappings，仅当返回data_ptr与目标不同才copy。指针相等不是一般性的shape、stride、容量或并发寿命验证。[SWA回放](vllm_ascend_swa_bounded_replay_contract.md)拥有何时修改slots的规则，本Manager拥有发布到原rank-major布局的入口。

AscendPCPAttentionContext保存global batch、global block tables、slot mappings和hidden_restore_idx，还可携带padded gather/write mask、local→global请求行、实际local token索引，以及DCP prefill每global请求已分配kernel block数量。使用方必须保留这些坐标含义；不能把一个按global顺序生成的表与local片段请求行直接配对，或用storage容量代替已分配列数。

## 版本、测试证据和交付检查

Main构造仅在精确0.32.0分支省略moe_gathers_tokens，其他分支转发该参数；req_states被接受不等于本方法已经使用或转交。独立Native maybe_build_pcp_manager调用cls.validate_config，按组rank/容量实例化并转发ParallelConfig.pcp_shard_decode_requests；该属性只判PCP>1/DCP==1，不含Main的KPool排除。Main platform选段还明确不把派生decode flag塞回ParallelConfig，以免draft dataclass replace拒绝未知字段。

因此迁移时须检查实际caller传入flag与Main helper政策是否一致。这里比较的是两个固定快照，实际配对544实现未在本卡读完；不能据差异宣布生产缺陷，也不能把UT默认constructor flag当成真实factory参数已经匹配。

所读Manager UT定义分片owner、graph请求/token维、replicated padding、PAD slots重叠保护、dummy上下文、hidden恢复及错误长度等检查；Runner/MTP选段定义全局batch交接、main/aux/model buffer恢复和实际前缀广播。这些CPU/mock定义没有运行，不登记硬件、模型精度、图或性能通过。

Agent交付应保存Main/实际配对Native版本、PCP/DCP/PP rank与构造flag、模型KPool属性是否存在、global/local请求slot与片段映射、actual/padded请求和token数、query边界、CPU上界/device真值、gather/restore索引及写mask、main/aux/model-owned对象与marker、每组global/gathered slots的顺序和地址。

先以无PCP参考验证恢复后的有效行和KV写入，再覆盖grow/shrink、零schedule、空rank、双片段prefill、混合批次、单token与多tokenverify、CPP/dummy、连续两步采样、padding扩容以及global slots修改后刷新。版本签名、恢复长度或容量拒绝时保留诊断并回到明确配对且已验证配置；功能与数值通过后才分别测partition、gather/restore、slot准备和端到端收益，本卡不声称任何优化数字。
