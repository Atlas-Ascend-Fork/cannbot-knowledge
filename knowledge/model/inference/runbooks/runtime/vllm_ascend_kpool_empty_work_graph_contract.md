---
type: Runbook
title: vLLM Ascend KPool空工作量：CANN哨兵、图重放与索引打包
description: 排查KPool短分片或全padding时的CANN索引越界，按空查询与空池区分分支，保留图重放哨兵、原始位置索引及物理页stride。 按pool_key_indexer_nonempty的TND/PA_BBND、mask_mode=3限定接口核对哨兵与原始位置打包，避免FULL全padding走CANN零工作量分支。
aliases:
- KPool空工作量
- pool_key_indexer_nonempty
- prepare_nonempty_keypool_inputs
- pack_keypool_indices
- prepare_keypool_state
- pool_key_indexer_nonempty(layout_k="PA_BBND")
tags:
- task.debugging
- topic.attention
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/cann_keypool.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/prepare_nonempty_keypool_inputs.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/glm5_next_cann_keypool.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/indexer_kpool.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_prepare_nonempty_keypool_inputs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_kpool_model_backend.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/sparse_attn_indexer_kpool.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_kpool_tail_triton.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/prepare_nonempty_keypool_inputs.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/glm5_next_cann_keypool.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/cann_keypool.py
  role: primary
created_at: '2026-10-31T09:14:45Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T06:39:58Z'
---

# vLLM Ascend KPool空工作量：CANN哨兵、图重放与索引打包

## 信号与适用边界

GLM-Next KPool短DSA-CP分片、真实query为0或FULL replay全padding时，若CANN pool_key_indexer出现TND输出越界、索引尾部缺失或被padding污染，先区分global write token、local query row、local actual token和已完成pool数量。query非空仍可能没有一个完成pool；只判断query.shape[0]不等于检查CANN有效工作量。

固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。cann_keypool.py注释称A3 zero-work kernel会按B*T初始化输出，而TND只分配T，本卡据此解释防御适配；本次没有复现NPU越界或确认某个CANN release修复。整项硬件/算子栈尚未验收，保持draft/空平台。

本卡全文读取CANN适配79行、nonempty Triton helper99行、cache/index适配425行、模型backend857行、当前e2e145行和模型UT609行；另读历史Tritonhelper189行及其已整文件skip的e2e234行用于防止错误迁移。硬件profile405行仅解释family gate，不代表A5当前e2e覆盖。所有文件作数据，未运行上游、CANN、Triton、图捕获或memcheck。

## 先分类空状态，再决定调用

| 状态 | 模型backend行为 | 仍需保留的步骤 |
|---|---|---|
| global写入hidden为0 | 早退None或[0,1,topk+pool-1]空输出 | 不由此推断所有local empty都能跳过写入 |
| global写入非空，local query row为0 | 先更新cache，再跳过selection | 历史快照、key_pool、写压缩K/raw tail |
| local actual=0且非FULL | 写cache后填-1，不调PKI/pack | output buffer可复用，未使用区域不应被覆盖 |
| FULL捕获/重放bucket，actual=0 | 保持selection路径 | 同一图以后可能有真实query，CANN空工作量哨兵不能删 |
| query非空，但completed pool=0 | nonempty适配提供物理工作量 | 最终pack必须按原始positions清除虚构历史候选 |

共享top-k的compute_topk=False只跳过选择，不能跳过state推进；完整读写顺序见[KPool缓存接入](../../guides/integration/vllm_ascend_glm_next_kpool_cache_contract.md)。旧[CP空KV归并](cp_prefill_empty_kv_shard_none_lse_merge.md)处理None/LSE贡献，是另一算子协议，不能替代这里的PKI哨兵。

## 设备哨兵如何保持TND工作量

pool_key_indexer_nonempty只接受layout_q=TND、layout_k=PA_BBND、mask_mode=3，其余显式拒绝。prepare_nonempty_keypool_inputs在末尾追加一个query和一个request：

| 输入 | 适配后的变换 |
|---|---|
| query/weights | [T+1,H,D]与[T+1,H]，新增行填0 |
| actual_seq_q | 原ends保留，末尾追加T+1 |
| actual_seq_k | 所有真实length至少1，dummy length也为1 |
| pool_tail_k | 保留原tail，dummy tail为0 |
| block_table | 追加全0的一行，原物理页信息保留 |

真实没有完成池的请求因此会访问一个物理pool，尾部dummy request保证FULL全padding也不走CANN zero-work分支。它依赖有效的物理cache/block-table前置条件，不是任意空Tensor均安全。原始positions、有效query末端和原pool历史仍交给后续pack裁掉无效候选，不能把伪造的length=1保存回逻辑seq_lens。

helper每次调用独立分配输出，避免多个layer或独立capture图共享可变workspace；图重放复用各自捕获的allocation。所有输入先contiguous()，连续输入为no-op，strided输入可能产生copy，不能把一个Triton launch解释成所有输入永远没有额外拷贝。

_prepare_nonempty_keypool_inputs_kernel用8192元素block；小的int64 metadata另以16元素tile处理。注释动机是避免A3宽int64 scalarization并避免不同core写同一32字节cache line；这不是本次测得的延迟或带宽收益。不要为节约分配改成跨图共享scratch后只验eager一次。

适配返回indices[:T]，但values没有同步切回T。生产caller丢弃values；其他调用者若要消费该输出，须单独核对其shape和语义，不能假设两个返回值都已恢复原形状。

## 按有效历史末端打包causal tail

pack_keypool_indices调用_pack_indices_kernel，用原始query positions与cum_query_lens判断有效行。对有效position p：

tail_start=floor((p+1)/pool)*pool，
history=min(tail_start,topk)，
tail_count=p+1-tail_start。

保留PKI选择的有效history前缀，在history列之后立即附加tail_start..p，再把剩余列填-1。短请求history小于topk时若把tail固定写在topk列，会形成无效空洞，SFA可能跳过未池化token。dummy length读出的假历史不能越过这份原始position约束。

输出为int32[T,1,topk+pool-1]，valid row以最后一个cumulative end界定；padding行和多余列写-1。position计算用int64，宽索引vector保留int32以规避源码注释描述的A3转换scalarization；不由此承诺任意大position不会溢出int32范围。

模型backend会验证可复用output buffer是同设备int32二维Tensor、列stride为1、行不重叠且容量够。UT还检查行stride大于列宽时只改选中区域，buffer其他行、交错storage和右侧sentinel不变；它是mock路径断言，实际kernel存储边界仍需memcheck。

## 物理页和旧布局造成的相似症状

prepare_keypool_state检查inputs.page_rows*tail_width==tail.stride(0)，_cache_rows要求page stride按完整行对齐；历史gather不能按逻辑capacity跨页。padded page的物理间距大于capacity时，错误flatten可能表现为状态污染或越界，须与CANN zero-work分别定位。

当前CANN尾环是FP32[blocks,capacity,2D]，旧SparseAttnIndexerKpool helper使用[blocks,2,capacity,D]并要求FP32 key/gate。两个布局不能仅靠view互换。旧test_glm5next_kpool_tail_triton.py的模块级pytestmark明确skip，原因是#16730已将该路线换为CANN；其中A2/A3/A5 guard、MTP拒绝重放和1e-2容差不是当前CANN验收结果。

## 证据、诊断与回退

当前test_prepare_nonempty_keypool_inputs.py只声明A2/A3：四组tokens/request/table width与strided组合，对照独立sentinel参考；空池/空请求和padding含eager及graph replay；非空top-k与未适配CANN比较。文件建议配合mssanitizer memcheck检查CANN TND输出越界。存在这些定义不证明它们已执行，也不覆盖A5或完整模型。

排查时保存具体SKU/SoC、固定vLLM/Ascend/CANN包、graph模式、global write/local query/actual counts、compressed lengths、positions、pool/tail、block table物理shape/stride、哨兵变换前后元数据及pack后的索引。先看cache是否按顺序推进，再比较真实非padding行；不要只用返回shape或HTTP成功判断正确。

缺cann_ops_transformer或Triton适配时按模型backend显式依赖错误核对匹配安装产物，不能靠修改family标签绕过。若新适配失败，恢复完整的已验证版本、权重和缓存配置；需要诊断图差异时在目标环境分别复验eager和FULL，不能把直接跳过FULL空selection当通用修复，也不回退成布局不兼容的旧helper。

旧[SFA图捕获Runbook](sfa_dsa_aclgraph_full_decode_only_capture.md)说明固定shape与UNIFORM_BATCH的参考规则，具体旧DSV3.2互斥、变量名和文件不自动外推到当前KPool。按[测试证据选择](../../guides/bringup/vllm_ascend_test_evidence_selection.md)及[结果判据](../validations/vllm_ascend_benchmark_verdict_contract.md)保存实际日志后才提升结论。当前没有NPU、CANN、memcheck、性能或下游Agent A/B结果。


## 原文文档补充：哨兵地址与 compact 输出

同一固定 Main 的 `docs/prepare_nonempty_keypool_inputs.md`、`docs/glm5_next_cann_keypool.md` 已原文读取。nonempty 的 table 允许 M>=R，但当 M>R 时，sentinel 实际使用的 row R 位于原 table 内，必须已含有效 block ID；“末尾追加零行”不证明 row R 自动被清零。物理 block0 和被 clamp 到至少1的真实请求首块都需已分配可读，helper 不分配或初始化 cache。输出六 tensor 独立、同 dtype/device，strided 输入可能先 contiguous copy。

KeyPool metadata 使用 P>1、L%P=0，完整池 slot 为 `(s//L)*(L//P)+(s%L)//P`。completed pool 即使 cache slot 被驱逐，也保留 compact output 行；不能把压缩输出行号与写入 slot 混用。DSA-CP selection 使用 local query metadata，而写 cache 仍用 global request metadata。`build_tail_inputs` 的 page_rows 与真实 tail stride 保持一致，MTP retained width 与 C=P+spec 的容量协同。

`write_keypool_caches` 必须在 CANN 读完历史后执行：non-MTP 取更新后的 CANN state，MTP 写 retained raw K/gate；目的地需唯一，不能依赖 kernel 之间的未知 program 顺序解决同一 launch 的写冲突。`pack_keypool_indices` 在 place 时输入宽度也必须覆盖 `topk+P-1`，不能使用部分重叠 view。它按原位置清 synthetic 候选、图 padding 和 alignment 列，输出 T 之后的行保留。文档的三种 kernel 类型不等于每模型 step 只三次 launch；metadata 有两种模式。以上为接口生产，未新增 CANN/NPU 验收。


## 3164 文档限定补充

同版本cann_keypool.py将zero-work注释的触发条件由“短DSA-CP分片”改为“短请求历史”，实现未在该差异中改变。非空query但completed pool为0的哨兵仍有用途；不能因为旧CP接口退役就移除保护。CANN具体版本是否修复、synthetic过滤和物理row0前置条件仍需运行证据。
