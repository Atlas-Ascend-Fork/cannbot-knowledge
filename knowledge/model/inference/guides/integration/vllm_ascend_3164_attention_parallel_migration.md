---
type: Guide
title: vLLM Ascend 3164注意力迁移：PCP角色、DCP位保真交换与量化KPool
description: 对照ceac与固定3164版本，说明旧DSA-CP移除、PCP角色metadata及投影委托、DCP query/交换/合并、整数索引与KPool量化缓存的接线变更。 固定3164 Attention并行/metadata/缓存迁移，不把旧DSA-CP删除等同所有CP撤销；记录新DCP与量化KPool的独立门禁。
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/dcp/sfa_dcp_exchange.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/context_parallel/common_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/context_parallel/dsa_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/context_parallel/dsa_v41_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/context_parallel/mla_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/context_parallel/sfa_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/dsa_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/dsa_v41.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/fa_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/indexer_kpool.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/mla_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/sfa_kv_offload.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/attention/sfa_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/dcp/dcp_a2a.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/dcp/sfa_dcp_merge.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/dcp/sfa_dcp_query.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/dcp_a2a_fused.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/glm5_next_cann_keypool.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/sfa_dcp_exchange.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/sfa_dcp_merge.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/sfa_dcp_query.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/sfa_indexer_store.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/sparse_index_remap.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/glm5_next_cann_keypool.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/sfa_indexer_store.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/sparse_index_remap.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/dsa_cp.py
  role: constraint
created_at: '2026-11-03T06:49:55Z'
updated_at: '2026-11-04T03:05:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# 3164注意力并行迁移

本卡归属固定3164。7d9e另有MLA草稿标识与padding后NZ材料化变化，见[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的MLA节；不能把旧view/格式转换说明当作新版本已物化或数值已验收。

## 版本与迁移边界

本卡比较Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2到3164adc8fe75892fbf7f99f524bb72fddf1e6efd，读取本主题全部新增/替换程序AST、文档diff与删除声明/路由投影。未变代码沿ceac来源保留；删除的大段legacy实现用原版本知识与完整声明删除映射追溯，不宣称新版整文件raw全文。未执行import、UT、编译、JIT、分布式或NPU验证。

旧[SFA复制视图](vllm_ascend_sfa_replicated_cache_views.md)、[CP O投影](vllm_ascend_cp_oproj_weight_protocol.md)、[FlashMLA DCP](vllm_ascend_flashmla_dcp_execution_contract.md)与[KPool空工作](../../runbooks/runtime/vllm_ascend_kpool_empty_work_graph_contract.md)保留原版本合同；下面列出迁移时必须重核的变化，不能以新入口覆盖旧pin的验收结果。

## 删除的是legacy token-CP，PCP并未一起删除

新版dsa_cp.py保留MRv2 PCP builder/impl，删除旧AscendDSACPMetadataBuilder/Impl、restore_tp_heads及TP-token局部metadata实现；Triton build_local_metadata_triton文件也删除。dsa_v41_cp删除legacy CP适配器，dsa_v41不再保存cp_token_range且heads固定n_local_heads。sfa_cp同时删除DSACP/DSADCP metadata/builder/impl及相关分支，indexer移除legacy query-gather句柄与局部slot/长度构造。不能只移动import后继续依赖这些旧类或将删除视为“所有CP都不支持”。

PCP O投影改为ParallelOProjection对象，显式传PCP input-shard配置、TP组、共享pool/key、full回调及decode_sharded，prepare_weight_load失败的既有日志/回退仍保留。forward置于对象batch上下文，all_gather_weights和最终forward均委托对象；原卡内自有switch/full/local/activation-exchange方法不再是本文件当前实现。对象内部与最新weight加载来源由其canonical维护，本卡只认精确调用边界，不凭旧函数代码证明新对象恢复/异常路径。

DSA metadata按State/SWA/Attention/Indexer分角色，新增ASCEND_DSA_INDEXER后端；仅覆盖build_req_metadata、无deferred-device metadata且无vision层时启用专门构造。State只需table/request布局；SWA负责原token slots与SAS；Attention负责压缩cache与SAS；Indexer负责QLI及压缩写入。通用/vision/deferred-device路径仍走完整builder。build_query/update_cache是各角色构造开关，不能通过删字段优化把消费者需要的cache/metadata一并省略。

PCP批内共享pcp_global/pcp_local、graph context、query offsets和staged RoPE；每cache group仍替换自己的block table与slot。SAS输出缓存键包括layer/window/DSpark标记、QLI另存输出与floor(seq/4)、remainder(seq,4)视图。DSpark专用RoPE在full图模式copy到step buffer；共享身份是当步批/角色/组，不能跨请求仅按shape复用。device metadata关闭前后的task group与buffer owner也不能混同。

## Dense Q replication与普通FA页规格

use_dcp_q_replicate先看显式VLLM_DCP_Q_REPLICATE，否则读parallel.dcp_q_replicate；只在DCP>1且PCP<=1继续，SFA或LoRA直接ValueError。MLA从q_proj.qrep_active严格True取开关，query投影heads扩为local heads*group size，w_uk_t沿DCP gather；prefill再取_local_view。decode CP若开启则要求NoPE/RoPE都含完整组heads并跳过旧query gather。它不是SFA query优化的同一开关。

FA后端新增head sizes64/72/128/192/256，192物理补到256；customize_spec同时改K/V head size，先清旧page_size_padded重算real_page_size_bytes，再保留与旧padding的最大值。缓存写K/V先pad、Q执行前pad、输出裁回逻辑宽。不能只padQ而沿旧192页分配，或把256的物理行宽暴露为模型输出维。MLA connector wait也从部分条件分支提前/扩大到共用路径，并增加compute-start记录；顺序变化需按新调用route核，不能以旧hook开关跳过等待。

## DCP query：head-major准备与可选view

SFA native DCP对正的二次幂NoPE/RoPE宽及FP16/BF16/FP32非空输入，用Triton直接拼[local_heads,T,N+P]后异步AllGather；context保存两个split宽和query_prepared，消费者wait之后按keep_view选择view或unpack为连续[T,gathered_heads,N/P]。两个kernel不通信；sum宽度不足以恢复split，未wait的context不能读取。PCP组合仍保留既有TP-head路线；无RoPE/非幂二宽度走原query路径，而非强迫零宽tl.arange。

SFA PCP槽映射针对packed cache区分复制decode前缀与gather后缀；NoPE缓存先按operator page view解释再取页。新版NoPE padding只在DCP消费点mask：attention置0、softmax_max置0、sum置1，避免无效padding参与跨rank加权；不能把普通SFA里移除的后置mask当作所有route都可省略padding初始化。

## DCP输出：位保真载荷与非有限LSE

注册dcp_a2a_fused仅在无PCP、无需返回LSE/延迟合并、按head scatter且can_exchange通过时进入新路径，还要求显式All2All组。BF16 output[T,H,D]、FP32 LSE[T,H,1]，R>1且R、H/R、D/2均正二次幂，H整除R。形状是输入与真实process group推导，不再固定D512/H64/DCP8；不满足条件保留原packing。

每peer发送T*(H/R)*(D/2+1)个INT32 word：两BF16位拼一word，LSE原FP32 bitcast一word。T1先flatten contiguous输出再reinterpret，奇storage_offset需clone；多token对非unit feature/奇outer stride做连续化。full向量上限16384项仅选pack实现，超过则最多4096项head/feature tile并按Vector核循环token，不是固定token容量上限。一次all_to_all_single后用as_strided视图分离output与stats，不做receive端transpose。

fused_merge按rank读LSE，把NaN、+Inf、-Inf均排除，有限max替代全无效max，分母0改1，且先把无效rank的output置0再乘weight，防NaN*0污染。全无效输出0；有限rank的非有限output仍不能被此逻辑自动修复。每program只留<=512维FP32 accumulator和rank向量，按rank串行加权；返回FP32，注册边界再转BF16。LSE_RANK_STRIDE仍constexpr，不能据其他do_not_specialize字段承诺任意新layout零编译。

## 索引精确性与原生INT8写缓存

sparse_index_remap对二次幂DCP/interleave用shift/mask取owner与local，保留INT32/INT64宽度、chunk内串行压紧和chunk序汇总。非幂二配置改INT64 div/remainder+唯一order key argsort稳定压紧，可能走AICPU；逻辑token可超过2^24甚至INT32边界，不能再用FP32 fallback/reference或TopK长度上界证明精确。DCP/interleave/rank应由caller先验证为正且匹配组，fallback不是非法0除数的修复。

原生SFA indexer的fused store只在exact backend类、无PCP、C8 INT8、二次幂head width与纯decode实际token>0时启用。量化本身仍用native流程，只延迟scale cast；新kernel按slot同时写INT8 key和FP32→FP16 scale，负/超capacity槽mask，capacity为runtime。目标有效slot须唯一、dense连续cache/quant与slot数匹配；它不解决竞争写，也不把connector等依赖前移。FP8/C4、自定义/并行backend继续旧写法。

## GLM KPool三种dtype与空工作

KPool绑定cache从单tensor扩到tuple：BF16单key；FP8 E4M3FN或INT8必须key+scale。INT8要求硬件profile的POOL_KEY_INDEXER_INT8 capability，FP8另查POOL_KEY_INDEXER_FP8；这些是固定来源门禁，不是本次硬件验证。wk权重跳过NZ转换。INT8按每vector max(abs)/127，夹到FP16 tiny后先存为FP16 scale，再round/clamp[-127,127]；FP8在store里按max/448、零vector用scale1，scale为FP32。

INT8 cache-write要求pooled_scales与scale_cache成对且形状匹配代码的(*cache.shape[:-1],1)，而文档以不同维度视图说明scale页；对接必须按真实绑定key rank核实，不只照文档表猜descriptor。page stride由managed存储提供，keys/scales随同P/D页转移；FP32 raw tail不因量化改变，tail占主导时物理page可能完全不缩小。禁止从key字节减半推导总cache内存减半。

BF16与FP8仍经pool_key_indexer_nonempty追加sentinel/clamp空池历史，FP8在padding之后才量化query并修零descale。INT8直接调CANN quant_mode=2，weights转FP16，要求实际CANN构建支持空completed-pool history；不能复用BF16 dummy请求规避。其他dtype拒绝，BF16不允许多余scale。删除旧DSA-CP guard/元数据并不自动允许所有offload/connector/CP部署；固定文档仍单列FP8 OffloadingConnector/PreemptOffloadConnector限制，完整传输与模型范围由既有canonical和当前配置证明。

当前文档列出的A3分布式、A2/A5单卡用例属于来源作者的有限测试声明，本卡没有重跑；shape、dtype、页表与图稳定性先过参考，再度量pack、collective、merge、索引和cache-store各阶段。不得将注册存在、AST读取或本仓最后检索检查当新模型/NPU性能通过。
