---
type: Guide
title: vLLM Ascend GQA/CP接入：历史与当前KV、图参数和LSE合并
description: 接入GQA上下文并行时分开历史与当前KV，保持host/device长度、PCP片段和图任务一致；按TP/PCP通信域合并LSE，核对当前贡献次数、跨流等待与padding。
aliases:
- GQA上下文切分
- DCPFIAParamProvider
- build_dcp_fia_params
- use_history_current_split_decode
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/attention_cp.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/common_cp.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_attention_cp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_attention_cp_precision.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_common_cp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/dcp/dcp_a2a.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_dcp_a2a_combine.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/utils.py
  role: constraint
created_at: '2026-10-31T08:33:12Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: "2026-11-04T02:54:15Z"
---

# vLLM Ascend GQA/CP接入：历史与当前KV、图参数和LSE合并

## 消费任务与来源边界

新模型接入GQA的PCP/DCP，或MTP、mixed batch、chunked prefill开启后出现重复当前KV、局部片段错位或图参数更新错误时，先核metadata和通信域，再讨论重叠收益。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，attention_cp.py 701行、common_cp.py 342行及四份UT（510/38/239/36行）全文读取；DCP融合算子622行只取1–19、246–622的接口/前端，两份utils只取相关helper。源码和测试只作数据，未导入、编译、执行上游UT、collective或NPU。整项硬件未知，保持draft/空平台。

本卡负责GQA执行协议。[CP拓扑](vllm_ascend_context_parallel_topology.md)说明配置组合，[SFA复制缓存地址](vllm_ascend_sfa_replicated_cache_views.md)说明缓存地址，[CP/O投影](vllm_ascend_cp_oproj_weight_protocol.md)处理投影。主来源类继承Native风格基类，其cache写入、KV准备、完整graph资源和分组验证仍需沿依赖追踪；配对版本见[框架记录](../../concepts/frameworks/vllm_ascend.md)。本卡未闭合Native/CANN ABI、Triton fallback/batched kernel或完整DeviceOperator知识。

## 初始化与host/device长度

AscendAttentionDCPMetadata扩展base metadata，prefill/decode字段只加在这个子类；AscendAttentionDCPMetadataBuilder继承DCPMetadataBuilderMixin与原attention builder。mixin在初始化保存DCP大小和rank，builder保存PCP组及use_dcp；build把本批pcp_context/cache-group放到实例字段再调用父类。后续修改运行配置或并发复用同一builder时，要核这些缓存状态的生命周期。

decode的num_computed_tokens_of_dcp先由Native helper在CPU计算全rank矩阵，再清当前rank列、用producer提供的dcp_local_seq_lens_cpu覆写有效前缀。不能把producer本地界限重新算成全局分片结果。历史长度另从(global_seq_lens-global_query_lens).clamp_min(0)出发，再按DCP interleave/rank分区；先分片再减本地query不是同一计算。

chunked prefill分开保存host FIA的累计KV/query长度与device KV-load的local_context_lens。CPU长度生成actual_seq_lengths_kv、local_total_toks；提供device context时单独分区供cache load，starts为0。两路有各自producer和时序，不能用其中一路无条件替换另一路；运行时仍须保证版本、容量和有效数据相容。

无PCP时只有chunked_prefill_enabled且存在CPU历史才构造history context；device历史可由device seq_lens减device query边界差值得到。PCP路径根据全局历史是否存在构造context，不能仅关chunked-prefill flag就删去全局历史计算。

builder的_split_decodes_and_prefills仅在无PCP且存在spec配置，或无PCP、use_dcp且本实例配置是PD纯consumer/recompute时，将short extend计作decode。共用split helper内部还可能用当前全局PD运行配置覆盖显式False；批次排序、DCP稳定CPU query长度和实例配置必须一起记录。共享helper的详细边界见[SFA地址与metadata](vllm_ascend_sfa_replicated_cache_views.md)。

## PCP的current前缀与history查询顺序

PCP prefill需要global request视图、local_to_global_req_indices和匹配的局部fragment数量。hidden_restore_idx先去掉全局decode前缀，再压缩每rank的[decode,prefill]布局，形成prefill-only query restore；current KV仍保留共享decode区域，所以current_kv_indices还要加回local_decode_tokens。

causal fragment的current长度取局部seq end减该全局请求的history；noncausal fragment取整个global current query长度。一个请求在同rank形成head/tail两个片段时，两个current KV前缀可以重叠，按prefix拼接后的累计KV长度也可以大于一次global current长度；不要为“去重”改变FIA每段边界。

history context要求cache-group与padded_gather_idx，使用global prefill block table。history Q先按PCP token维all-gather并恢复全局顺序，再沿DCP/TP head域取distinct heads；合并后用pcp_local_query_indices只取本rank真实fragment。current FIA始终消费local actual query与按前缀选出的current KV。上游必须供给约定的KV gather顺序，父类的实际生产尚未由这里完整验证。

## decode split策略与三种KV范围

use_history_current_split_decode要求causal且decode存在；draft prefill或spec target（use_spec_decode且非draft）固定走split，以保持捕获任务布局；其余批次只要任一query段长度>1就split。不能只按当前批次是否单token动态省掉已捕获任务。

CPKVScope定义HISTORY、CURRENT、FULL。DCPFIAParamProvider用(metadata_layer_name, attention_kind)作为任务身份，各自从本次metadata解析参数：

| 范围 | query/KV长度与块表 | 消费的数据 |
|---|---|---|
| CURRENT | query累计end同时作KV累计end，block_table=None | 本批current K/V |
| HISTORY | query累计end、cp_history_seq_len、decode block table | 去掉global current之后的分片历史 |
| FULL | query累计end、全rank矩阵中本rank列、decode block table | 常规完整cache路线 |

build_dcp_fia_params按HISTORY→CURRENT顺序发布split任务，否则只发布FULL。provider key必须区分范围，避免同一层的两次FIA任务共享错误的长度或block table。GQA的CURRENT在causal时使用mask/sparse_mode=3；history/full使用mask=None、sparse_mode=0，paged路线加block_size与inner_precise=1；均请求softmax LSE，具体CANN数值契约仍待核验。

## 图捕获保留任务身份与存储

_run_dcp_attention在普通模式调用FIA；捕获模式按provider类、KV范围、num_heads和num_kv_heads取workspace资源，准备empty_like(query)输出及FP32 LSE，用register_task登记out变体与provider。运行更新对象是长度/block table等参数，Q/K/V及输出地址需要上层维持。

这里读取了注册调用，没有执行UpdatableGraph、CANN workspace查询或replay。can_return_lse_for_decode、supports_mtp_with_cp_non_trivial_interleave_size是类能力声明，不能当成本次硬件验证。另见[图消除与host同步边界](graph_break_elimination_host_sync_unsupported_ops.md)。

## distinct head与通信域

DCPImplMixin在PCP>1且DCP大小等于PCP大小时保留原query heads；DCP跨越更大的TP×PCP域时，通过TP组只gather distinct heads。token轴的KV fragment gather仍走DCP域，不能把head域的优化套到token域。fragment先沿最后feature维cat，gather后再按原feature宽度split。

带PCP的_merge_dcp_attention_output先按TP域scatter（没有head gather时大小为1），再沿PCP组gather各KV贡献；无PCP时用DCP组scatter。传给融合op的dcp_size在PCP组合下表示TP scatter world，不是统一DCP world。要同时记录TP、PCP、DCP的rank/world/group_name及Native验证后的关系，不能只带一个总卡数。

## decode事件与当前贡献次数

history query先gather heads，运行HISTORY或FULL FIA。FULL直接归并；split要求current K/V存在，主流记录history_ready，辅助decode stream等待该事件并计算local current FIA。输入Tensor对辅助流record_stream，current结果对主流record_stream，保留异步存储生命期。

当前FIA在history_ready后启动，允许它与随后history packing/A2A重叠。主流对history执行defer_combine=True通信，等待current_attn_done，再将current_output/current_lse作为local贡献加入fused_dcp_lse_combine。只有history参加跨rank历史归并；复制的current贡献只加入一次，不能再随history发送并在每rank重复计数。

cp_decode_comm_stream、cp_chunkedprefill_comm_stream是进程全局lazy stream。这里的正常event/wait/record_stream顺序没有提供所有异常路径的finally join或任务退役保证，故障恢复还要分别检查已启动通信和仍在读取的buffer。

## prefill的两条流水与padding

有history时，comm流先等主流并gather history Q；主流计算current FIA。主流等comm后计算history FIA，再让comm等主流并执行deferred history merge；主流再等comm，PCP时从packed history的query维（dim=2）取local fragments，最后把current作为local贡献一次合并。每个wait都对应实际数据依赖。

没有本地历史token时，_compute_prefill_context返回零output（query dtype）和-inf LSE（FP32），形状仍与非空路径一致；不以(None,None)退出。该分支没有调用非空FIA，普通history路径使用host累计query/KV长度与device cache-load长度。

decode query终点取actual_seq_lengths_q[-1]以保留捕获的PAD query；prefill偏移取num_decode_tokens，history gather可包含pcp_local_num_input_tokens容量，current attention只取actual rows。最后只写真实prefill输出，外部tail可能保留旧值。不要为所有路径统一清PAD，或把decode终点和prefill实际token偏移强行合并。

## 融合LSE接口的输入与返回

pack_dcp_output_lse要求NPU三维output[T,H,D]、同设备FP32 LSE[T,H,1]、正整数且非bool的scatter world、scatter_dim为0/1、非空维及scatter轴整除。output支持BF16/FP16/FP32；接收payload形状为[scatter world, local scatter, replicated axis, D+extra]，extra分别为4/4/1。

本卡原Host选段未展开kernel20–243；同一ceac的四lane数值编码、无效贡献屏蔽和Device归并已由[DCP打包归并合同](vllm_ascend_dcp_lse_kernel_contract.md)单独补读，需编码细节时沿该入口，不据tail宽度猜测或将它误当raw bitcast。

fused_dcp_lse_combine要求连续四维NPU recv、正head_dim和匹配的packed宽度；local_output/local_lse必须成对，形状与post-scatter输出及设备一致。return_lse=True要求FP32 recv；外层dcp_a2a_fused还要求FP32 partial，禁止与defer_combine同时开启。直接调用不同入口时须逐项核各自尺寸前提，不能将pack的所有guard假定为所有入口都有。

dcp_a2a_fused_combine先pack，scatter_size>1时检查group并A2A，否则复用send；再可选PCP gather(dim=0)。defer_combine返回packed贡献，不提前做数值归并。O与对应LSE成对传输时，加权和不依赖source-rank排列；[SFA地址视图](vllm_ascend_sfa_replicated_cache_views.md)的block lookup排列约束不能直接搬到这里。

group_name通过Native注册表weakref解析，scatter组需存活、有device_group且world匹配；PCP组也需存活。dcp_a2a_fused_fake的FakeTensor实现仅传播输出shape/dtype：defer模式贡献rank数乘PCP大小；普通模式返回post-scatter shape，可追加merged LSE。PrivateUse1注册与mutates_args=[]不代表没有collective副作用。

前端含is_950局部batched选择：pack还要求BF16、head scatter、D<=2048、足够rows和连续feature；combine还限制DCP1..8、D<=512、local贡献、无return_lse及stride/rows阈值。完整阈值与batched/fallback的实现阅读范围见前述DCP打包归并合同；两卡均没有执行这些kernel，局部SKU dispatch不能提升成整项平台或性能承诺。

## 数值依据、旧故障卡与待验证项

common_cp的CPU参考为LSE_final=logsumexp(LSE_i)，O_final=sum(exp(LSE_i-LSE_final)*O_i)。这个helper没有显式all--inf guard，不能从有限随机输入或shape检查推断全部空/全mask情形无NaN。旧[decode空位置out/LSE对称屏蔽](../../runbooks/precision/cp_dcp_online_softmax_merge_mask_out_not_only_lse.md)和[prefill空KV占位](../../runbooks/runtime/cp_prefill_empty_kv_shard_none_lse_merge.md)保留各自PR版本与信号，当前Triton融合路线需要自己的证据。

已读UT定义包括PCP rank0/1、history0/101、causal/noncausal、chunked flag、KV heads1/2、PAD tail=-99、producer本地长度101/202、device context偏移0/3、DCP2/4及interleave1/8；有限加权参考输出[4,6]与LSE log4。precision UT定义float64、Q5/H3/D8、KV12分3片，与未分片参考按rtol/atol=1e-10对照。op UT只定义meta/Fake BF16/FP32的两个scatter轴及defer不合并行为。以上均未执行，不能引用为NPU误差或吞吐结果。

Agent适配记录至少包含query/current/history的owner与长度、host/device producer版本、TP/PCP/DCP域、local/global fragment映射、provider范围/key、graph地址、每次event/wait和LSE贡献次数。获准运行后，先与无CP参考逐请求比对current前缀、history分片和合并数值，再覆盖mixed/spec/draft、空rank/PAD、图重放与异常恢复。最后分别测FIA、pack、通信、combine、峰值内存及端到端TTFT/TPOT；本卡没有NPU或Agent A/B结果。
