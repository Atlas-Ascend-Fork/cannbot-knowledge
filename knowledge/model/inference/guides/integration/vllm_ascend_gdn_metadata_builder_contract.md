---
type: Guide
title: vLLM Ascend GDN元数据接入：请求分组、Host分块与卷积字段
description: 接入GDN/KDA元数据时核对动态投机分组、state与token索引、conv和chunk两套offsets、Host描述符及后端字段，保留Native与设备实现边界。
aliases:
- GDN元数据接入
- AscendGDNAttentionMetadataBuilder
- AscendGDNHostMetadataBuilder
- _compact_empty_segments
tags:
- task.implementation
- topic.model_adaptation
- topic.attention
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/gdn_attn_builder.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/gdn_attn_builder_310.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_gdn_attn_builder.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/gdn_attn_builder.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/gdn.py
  role: implementation
created_at: '2026-10-31T11:05:12Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T06:39:58Z'
---

# vLLM Ascend GDN元数据接入：请求分组、Host分块与卷积字段

## 任务与固定证据

为新GDN/KDA模型接入元数据、替换Host prefill或排查conv/chunk字段错位时，先核对请求分类、token分区、state IDs及每个kernel实际消费的字段。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：gdn_attn_builder.py1158、FLA utils133、310P builder60和metadata UT1595全文，均作为数据读取，未运行torch/NPU、上游测试、JIT或模型。

Native父类分配、mamba block-table helper和实际GDN/FLA/CANN kernels未闭合；配对Native与独立快照身份沿[框架入口](../../concepts/frameworks/vllm_ascend.md)核对，不能把名称相同当ABI相同。整项硬件范围未知，保持draft/空平台。

[普通输入元数据](../../concepts/frameworks/vllm_ascend_input_attention_metadata.md)解释请求/token/slot量纲；[KDA接入](vllm_ascend_glm_next_kda_dispatch_contract.md)消费这里的conv/chunk/state协议；[GDN图回放诊断](../../runbooks/precision/vllm_ascend_gdn_graph_metadata_lifecycle.md)拥有持久buffer和padding探针。GLM RecoverSSM另走专用builder与commit，不与公共GDN协议合并。

## backend选择与字段集合

| 路径 | 实际选择与消费 |
|---|---|
| AscendGDNAttentionBackend | AscendGDNAttentionMetadataBuilder，公共kernel字段 |
| AscendGDNHostMetadataBackend | 通常Host builder；当前config为GLM且use_glm_recoverssm命中时延迟返回专用RecoverSSM builder |
| AscendGDNFusedAttentionBackend | PCP world1且consumer支持Host prefill才选Host，否则公共builder |
| GDNAttentionMetadataBuilder310 | 共享分组/图物化，省略公共chunk/length/non-spec包装，由310P消费者自行派生长度 |

Host选择读取已校验的opt-in，不在这里派生内部use_kda_recoverssm。consumer支持方法的硬件探针和kernel实现未读，不据布尔条件宣布所有Qwen/GLM/Kimi及平台均通过。Host传递pcp_context也不放宽RecoverSSM PCP=1限制。

## 先分清逻辑请求和图请求

build先在full graph+spec条件下调用_remove_spec_graph_padding_queries，再记graph_request_count。num_actual_reqs省略时取图请求数，显式值必须0..graph；小于graph时调用父unpadded并裁accepted/draft数组。有效token数与图请求数分别保存，不能只用一个batch字段解释两者。

_treat_single_token_prefills_with_state_as_decodes只在is_prefilling=True、query_len=1且seq_len>1时，将该请求改为decode；先clone phase mask，保留共享输入。首token seq_len1仍prefill，K+1宽prompt chunk也不能仅凭长度当投机decode。

block table交Native mamba_get_block_table_tensor，使用device seq_lens。非0.32、cache mode非none且行数不符时，Ascend先将block-table行裁到seq_lens行数；0.32保持原分支。这里核对的是固定调用条件，不是所有版本兼容证明，不能用旧CPU长度替代当前device长度。

## 动态投机的请求分类

未启投机或没有CPU draft counts时，走普通decode/prefill拆分。启用时，只有非负draft counts之和>0才将draft>=0标为spec；因此某请求本轮draft0也可能随批走spec。全批没有实际draft时mask清空，回普通分组，不把配置开关等同本轮有spec。

无spec时split_decodes_and_prefills的decode_threshold=1、treat_short_extends_as_decodes=False；state取block table首列，conv保留所需block表视图，accepted=None。query_start_loc是边界前缀和，不是每请求长度数组。

有spec时，非spec query_len1计decode、0计padding、其余prefill。若普通decode和spec同时出现，普通decode被并入prefill计数，避免同一结果同时num_decodes>0与num_spec_decodes>0。适配方按最终分类消费，不按原始请求标签猜测分支。

纯spec直接构造arange token indices，长度受num_spec_requests×(K+1)与末offset限制；混batch将请求mask展开为token mask，再稳定排序分区。_stable_argsort_for_npu只把bool转FP32，保留组内顺序；大整数不转浮点，避免2^40附近精度丢失。AiCore/AiCPU动机来自注释，本卡没有测得排序kernel时延。

请求indices用于gather state/accepted，token indices用于gather投影和scatter输出，两者不能互换。spec state可有K+1列；non-spec recurrent取首列，conv的block-table视图另行保留。

## conv字段与chunk字段不共用同一坐标

有普通decode前缀和prefill尾部时，chunk的prefill_query_start_loc去掉decode行并减去decode token数，prefill state也切尾部；conv prefill包装仍使用non-spec整段offsets/cache indices及has_initial_state。只修一个offset却不切state，会破坏producer-consumer对应。

has_initial_state由已计算context>0生成，再按non-spec请求选择；prefill_has_initial_state另外取prefill尾部。新请求在所有rank都应忽略复用conv历史，不能仅在PCP rank0标fresh。上下文查询的Native实现仍需按实际版本确认。

GDNDecodeMetadata.actual_seq_lengths为“首边界+相邻差”，常见[0,1,1]或[0,4,4]；它不是cu_seqlens的[0,4,8]。公共spec/non-spec包装按最终graph-stable引用生成，310P的对应公共长度字段可为None/不存在，不能为了凑shape补造值。

## Host分块描述符与空段压缩

GDNChunkedPrefillMetadata保存host cu_seqlens和展平chunk64 indices，并有六项可选device chunk字段。公共builder只有实际non-spec prefill且_USE_COMMON_KERNEL_METADATA=True时构建，不在纯decode/spec批重复准备prefill描述符。

_compact_empty_segments只保留正长度段的终点，形成compact offsets；无删除时keep_meta=None，有删除时返回mask，builder将其准备到消费设备。kernel输出state必须按该mask写回原请求坐标；空段保留原初始状态，不能把compact行直接写回整个pool。

utils.prepare_chunk_indices按ceil(length/chunk_size)生成段内chunk号，以非空段起始重编号，因此空段会改变kernel侧紧凑编号。prepare_chunk_offsets累加ceil长度，prepare_update_chunk_offsets每段再加1，prepare_final_chunk_indices为cumsum(ceil+1)-1；三者不是同一种offset。

公共常量chunk64、solve-tril大块1216和working set2^18用于元数据规划。local GDN heads先取linear_attn_config.num_heads/TP，再取linear_num_value_heads/TP，否则调用模型head helper；不能拿普通attention heads替代Kimi等线性层heads。

cumsum chunk规划以max(1,working_set//(heads×64))为基础，取1或向上2幂。build_device_chunk_metadata=True才构造chunk64 indices/offsets/update/final、large-block和cumsum六项device张量；Host False只准备实际需要的host chunk64/offset/compact，其他字段为None，并跳过无用helper调用。

这些是结构和计算合同，没有实测加速百分比。utils里的input_guard、safe_exp和clear_ssm_states不在这里的metadata调用链，不能套用本卡推导它们的设备和状态语义；完整算子分析另需对应producer。

## Host卷积buffer的接入

Host builder以group首个layer为代表。只有显式use_contiguous_conv_indices才懒分配额外index buffers；只有use_shared_conv_output才分配[token_capacity,3×local_projection_size]，capacity=max(max_num_seqs×(K+1),decode_graph_max_bs)，不按全部prefill token预算扩大。

每步清共享conv输出一次，包括失活的已捕获分支，group内各layer按序复用。spec和普通decode包装接同一buffer；recurrent state indices不改，只为conv构造连续vector。已有连续一维indices直接alias；矩阵即使仅一行也取首列复制到group buffer，并检查容量。

non-spec prefill/decode引用同一indices前缀，取最长来源准备一次，再分配各自视图。是否跨请求/stream并发安全仍需实际Runner生命周期验证，不由“同地址”自动推出。

## 测试定义与适配验收

UT1595行包含34个test函数，使用CPU metadata、真实父类构造及局部patch/mock，覆盖Host helper省略、head来源、普通/spec/mixed、one-token prompt、device block-table、align和graph稳定引用。参数化里的DCP16、310P、graph/eager仍是CPU元数据fixture，不是分布式或硬件结果；临时补triton.cdiv的fixture也不等于运行环境已兼容。

Agent交付请求/图计数、phase与draft来源、state/token索引、conv/chunk两组offsets、initial-state mask、Host/device字段表及group buffer容量/地址。先按这些字段逐个比对参考，再进入真实kernel、eager/graph、动态draft0、混batch和目标平台验证，分别记录CPU规划、H2D、卷积和状态kernel成本。

失败恢复匹配版本的builder/backend/config与完整状态，停止新增并行或图组合；不要统一修改所有padding、伪造length字段或把源码测试定义写成NPU验收。


## 3164 版本补充：align GDN 元数据融合与 padded state I/O

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`；完整变化与必要上下文静态读取，不标目标全文FULL，未执行upstream/JIT/NPU/图/通信/性能测试。

batch分类抽到_split_gdn_batch：无spec按普通decode/prefill；全spec只有spec token；混合时所有非spec正长度行统一进入prefill分支，ordinary decode也随之进入。CPU分区稳定生成spec/non-spec请求与token映射，不能用query_len=1覆盖phase语义。

只有runtime传num_actual_reqs且>0才尝试_build_fused_metadata；Host builder还要求conv索引buffer存在、mamba_cache_mode=align、speculative blocks够。其他路径保留generic构造和旧0.32/main block table行裁剪。融合复用捕获state/query/length/accepted buffer，小于capacity取view，大eager batch才另分配；FULL padding的spec与non-spec行数分别推导。

混合spec用一次pinned int32[R,2] layout上传替代mask与两个sequence-index复制：第一列spec非负ordinal，non-spec为负ordinal-1，第二列对应compact token起点。prepare_gdn设备kernel同时生成physical state、conv indices、mask、query ends、actual lengths、accepted、token索引、initial flags与prefill query，并清conv输出；普通finalize才额外zero，融合不重复清零。metadata attach必须保留这些最终graph-stable引用，fused和generic的numerical/shape比较是验收要求。

GDN普通chunk fallback检测state.stride(0)是否等于逻辑row numel。padded页使用selected-row gather/scatter，只复制选中历史，转换末两维布局再送chunk核；紧凑池保留普通index与clear。不得为了索引先把整个padded pool contiguous。fresh flag、重复写slot、state dtype与真实stride按[状态I/O](vllm_ascend_triton_mamba_state_io_contract.md)进一步核对；新prepare kernel细节另由同版本Triton主题记录。
