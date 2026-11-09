---
type: Guide
title: vLLM Ascend SFA 复制缓存地址：DCP块表、PCP顺序与Indexer缓冲
description: 适配SFA缓存时区分物理块表与复制地址，按device查询边界屏蔽padding、按PCP顺序排列slot，并核对Indexer独立元数据、逐步缓冲和别名写入。
aliases:
- SFA地址视图
- get_sfa_pcp_global_metadata
- build_sfa_dcp_replicated_slot_mapping
- AscendSFAIndexerMetadataBuilder
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/sfa_dcp_utils.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/sfa_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_sfa_cp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/common_cp.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_indexer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/utils.py
  role: constraint
created_at: '2026-10-31T08:12:38Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T08:13:33Z'
---

# vLLM Ascend SFA 复制缓存地址：DCP块表、PCP顺序与Indexer缓冲

## 消费任务与固定范围

新模型接入SFA，或PCP/DCP开启后出现Indexer错选、slot越界、padding重放脏值时，先确认每张表属于哪个缓存和哪个token顺序，再追踪实际KV读写。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取sfa_dcp_utils.py 125行、common_cp.py 342行、Indexer UT615行；SFA实现、Indexer实现、SFA UT及两份utils只取明确选段。Indexer实现的metadata-builder类526–1109行完整读取，其余backend计算不由此闭合。源码和测试均只作数据，未执行上游导入、UT、collective、图捕获或NPU，整项硬件未知，保持draft/空平台。

本卡覆盖地址重建和metadata生命周期。[CP cache映射](../../concepts/frameworks/vllm_ascend_cp_cache_mapping.md)说明一般布局，[旧版SFA跨组KV gather](sfa_dsa_cp_cross_group_kv_allgather.md)固定在db51版本并声明A3范围，[hybrid块大小对齐](../../optimizations/rules/hybrid_kv_cache_context_parallel_block_size_alignment.md)处理scheduler粒度，[CP/O投影协议](vllm_ascend_cp_oproj_weight_protocol.md)处理投影与通信。本卡保留这些任务的版本与平台边界；新模型不能只因共享block id或同为CP就套用旧版完整KV重建假设。配对Native及独立快照的版本关系见[框架记录](../../concepts/frameworks/vllm_ascend.md)，这里没有证明Native/CANN ABI。

## 记录四种所有权和布局

| 对象 | 构造与使用 | 接入时需保存 |
|---|---|---|
| DCP本地物理视图 | local block table、原slot mapping和本rank seq lens服务实际KV写入/读取 | cache group、物理block尺寸、已分配列数、DCP rank和interleave |
| SFA replicated地址视图 | 将本地物理块映射到复制Indexer地址空间，处理kernel逻辑子块 | kernel block尺寸、每物理块的子块数、复制列与rank次序 |
| PCP gather顺序视图 | 全局token slot按padded_gather_idx重排，并用写mask置-1 | receiver本地块表、global query边界、gather索引与mask |
| Indexer私有metadata | 独立builder从common metadata产生块表、slot、RoPE和query/key长度 | 输入slot地址key、输出buffer所有者、draft步与capture/runtime对应 |

主SFA缓存与Indexer缓存共享block id，拥有各自物理cache与metadata builder。复用主attention的metadata对象会混淆地址空间；独立builder仍可能通过slice持有common输入的别名，后续原地mask是否修改该输入要按分支核对。

## 先核真实能力门控

enable_sfa_dcp_replicated_indexer要求decode_context_parallel_size>1且model_uses_sfa_sparse为真。后者要求hf_text_config存在且有index_topk属性，并排除任一hf_text_config/hf_config带index_kpool或compress_ratios属性的对象。这里用属性是否存在作判断，不能把属性值False或空列表当成“没有该属性”。这是当前配置结构的路由条件，不是硬件/任意架构的支持清单。

uses_pcp_sharded_layout在use_pcp=False时返回False；PCP配置开启但没有pcp_context时，先断言slot长度不超过num_input_tokens，再返回False。复制执行的draft decode及其PAD可以没有PCP context，不能凭Tensor行数猜测需要扩展所有rank的slot。

## 从物理块到replicated逻辑块

get_sfa_dcp_max_local_block_table_cols计算本地逻辑列上限：local_cols_max = ceil(max_model_len / (physical_block_size * DCP_size)) * blocks_per_physical_block。

get_sfa_dcp_local_block_table取前num_reqs行及min(实际storage列数, local_cols_max)列。storage宽度是容量，不能代替每个请求实际分配的block数。SFA builder要求物理KV block_size能被kernel_block_size整除，以B=physical_block_size/kernel_block_size描述逻辑子块。

build_sfa_dcp_replicated_block_table中，令复制列为r、D为DCP大小、B为每物理块的子块数：local_col=floor(r/(D*B))*B+r%B，replica_rank=floor(r/B)%D。取出本地logical block id后，B=1时生成local_id*D+replica_rank；B>1时先拆physical_id=floor(local_id/B)与sub_id=local_id%B，再生成(physical_id*D+replica_rank)*B+sub_id。这样保留hybrid逻辑子块，不能把任意logical id直接乘D。

seq_lens<=0的请求行在复制block table中乘成0；slot的无效值另用-1。物理block 0可以合法分配，不能把block id为0等同于未分配或padding。

## 用device查询边界生成slot

build_sfa_dcp_replicated_slot_mapping先将调用方输出全部fill_(-1)，有效token数取min(num_actual_tokens,num_input_tokens)。零请求或零有效token直接返回，旧buffer内容不会留在这个返回视图里。

非空时创建num_input_tokens长度的token索引，在device query_start_loc[1:num_reqs+1]上searchsorted(right=True)得到请求归属。有效性同时要求token<actual且req<num_reqs；无效req先clamp到可寻址请求，无效positions先改为0，再按position/kernel_block_size和余数计算块列及块内offset，最终无效slot写-1。这避免固定output_size的repeat_interleave在device query总数之后产生无效请求索引。

调用方仍须保证positions长度、block table宽度、输出容量、block_size及有效position的范围一致。有效position不会被通用clamp；即使随后where写-1，前面的地址读取仍须安全。其他消费者（如RoPE）可能独立读取原positions，本helper没有替它们清洗输入；相关故障探针见[graph padding旧position越界](../../runbooks/runtime/graphmode_padding_stale_position_gatherv3_out_of_range.md)。

## PCP全局token视图与接收方地址

get_sfa_pcp_global_metadata只replace地址重建消费的字段：global query_start_loc、由global numpy边界构造的CPU Tensor、裁到num_reqs的seq_lens、请求/token计数、positions和指定cache group在接收方的global block table。其余字段没有全部改成global，不能将该对象交给任意要求完整global attention metadata的消费者。

PCP+DCP prefill先在这个全局token视图上，用接收方的本地物理块表生成复制地址，再调用build_pcp_ordered_slot_mapping：index_select(global_slot_mapping, padded_gather_idx)写入调用方buffer，最后按gathered_kv_write_mask把不写入的槽置-1。索引和mask都必须存在，容量不足时报错。index_select先于mask执行，所以masked-out的gather索引也必须可读取。

该函数只写num_tokens的返回slice，返回值别名调用方buffer；不能推定整个pool尾部都清零。串行复用、图内消费者生命期与不同draft步的隔离由上层保持。receiver-local block、global token序列和PCP gather顺序三个维度都要记录，不能直接复用另一接收rank的物理地址。

## SFA builder的临时视图与compact字典

AscendSFADCPMetadataBuilder要求DCP>1、interleave为正。请求buffer容量为max_num_seqs，在PCP>1时乘2以容纳DualChunkSwap两段，再加1容纳FIA dummy请求；block/slot buffer另按最大token及列宽准备，超过容量显式报错。地址稳定为图准备提供条件，未构成真实capture/replay验收。

_build_with_metadata_view临时替换common.slot_mapping和block_table_tensor，在try中调用build callback，并在finally恢复这两个原字段。产物dcp_context保留原物理slot、本地块表和本地int32 seq_lens；seq_lens优先取common.dcp_local_seq_lens，否则按配置的DCP rank/interleave计算。这个finally没有包住所有后续计算和共享buffer变更，不能当作整个metadata生产事务的回滚。

普通DCP compact路径从本地表flatten().unique生成字典；PCP+DCP传入全局请求块表时，必须同时提供实际分配block counts，先按counts选择条目再unique，避免不同rank局部请求行不同或尾部旧ID污染发送字典。代码保留共享原表，合法block 0也须保留；本地尾部可以仍有旧ID，消费者只读取已分配列这一前提不能丢。

compact remap使用dcp_collective_rank_order*num_unique偏移。源码记录logical DCP顺序与ProcessGroup排序的排列关系，例如PCP2/TP4/DCP8为[0,4,1,5,2,6,3,7]，让大KV gather维持collective次序。这里是静态地址契约，没有运行HCCL确认实际传输。

global prefill可以在本地没有prefill时仍要求compact数据；PCP context缺省的decode graph回退base build，prefill重建要求cache-group index。PCP prolog给非0 rank的leading replicated decode采用rank0 slot，global prefill slot去掉decode前缀。每种视图的写入者和有效行数需要分别保存。

## Indexer的逐步buffer和别名

AscendSFAIndexerMetadataBuilder直接从common metadata构建自己的地址视图。DCP用复制地址helper；没有DCP但有PCP sharded布局时取完整common slot mapping；普通路径只取输入token slice；DSA-CP且无PCP时补到TP对齐并为PAD写-1。布局flag由helper解析，forward应消费这个flag。

_metadata_buffer_key实际为("slot_mapping", 输入slot_mapping.data_ptr())。上层proposer为每个逻辑draft步保存持久slot Tensor，所有可变派生buffer沿这个地址区分；draft_index本身不是key。输入地址生命周期改变或并发复用需要重新核对，不能把每步不同的整数参数当成buffer隔离证据。

普通build使用cached RoPE，仅在speculative_config存在时复制到逐步buffer；build_for_drafting使用非缓存RoPE并复制；build_for_graph_capture使用缓存再复制。普通target可能直接别名框架RoPE。DSA-CP另拥有局部RoPE及query/key长度buffer，先清局部PAD再裁源；“数值与SFA相同”仍须同时保证存储独立。

普通build显式转发pcp_context/cache-group；draft和graph入口依赖kwargs提供相关上下文，不能假定三种入口隐式构造相同global视图。RoPE复制会检查容量和非token维shape，但全生命周期、所有dtype/device变更与实际图复用仍需要设备侧验证。

LIM路径在req_topk_buffer_active存在且use_fused_copy_sfa启用时，按CPU query边界和请求ownership原地将slot置-1。base/PCP路线可能别名common.slot_mapping，所以“独立Indexer builder”不保证所有模式都不修改输入。完整LIM/offload消费者不是本卡已完成范围。

## decode边界与运行时配置

split_decodes_and_prefills假定批次已按decode→short_extend→long_extend→prefill排序，优先使用DCP稳定CPU query_lens/max_query_len；结果token计数基于num_actual_tokens。零请求返回全0。require_uniform允许零长度padding；关闭short_extend归decode时还会结合is_prefilling标志。

PD decode recompute helper要求纯consumer（consumer且非producer）、scheduler recompute开关，显式配置缺省时从Native current_or_none读取；RuntimeError/AttributeError回False。split helper内部还可用当前全局运行配置将treat_short_extends_as_decodes强制置True。因此单独传入False不总能控制最终分类，要同时保存调用方配置与当前runtime角色。Native重排、CPU/device异步更新和调度实现仍需补证。

## 已读定义与后续验收

SFA UT选段定义：12实际token配12/16输入容量时PAD为-1；global slots[100,101,102]按[2,0,1,0]与写mask得到[102,100,101,-1]；max_seqs=4时请求容量为5或9；本地[10,11,12,13]扩展为[20..27]；global allocated counts保护合法0/3 block并排除旧尾部。Indexer UT全文还定义独立query/key buffer、world1/2/4/8及空/PAD、PCP+DCP slots[2816,2560,2688,-1]、draft步隔离和capture/runtime地址一致。

以上均为CPU/Mock测试定义，此次没有执行。Indexer UT中另外的C4 packed写入、selector ABI和cache字节计算不在本卡选定语义范围；真实cache commit、top-k kernel、设备依赖、RoPE算法、完整attention forward及性能尚未闭合。

Agent接入记录至少包含物理/逻辑block尺寸、每请求allocated counts、receiver rank与cache group、global/device/CPU query边界、actual/input容量、positions范围、gather索引/写mask、输出buffer key及alias、runtime角色和decode分类。先逐rank对照无CP参考的block/slot及Indexer候选覆盖，再覆盖hybrid子块、混合批次、空rank、PAD、draft连续两步、图重放与容量拒绝；获准执行后才能记录数值和性能结果。地址映射、实际KV通信和O投影的时延、字节与峰值内存应分别测量，不将本卡检索验收作为硬件支持或优化收益证明。
