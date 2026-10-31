---
type: Optimization
title: 因果稀疏注意力 CP prefill 的 zigzag 负载均衡：每 rank 两段两次调用 + 头尾因果前缀 actual_seq_lengths（qlen≠kvlen）
description: 解释每请求ZigZag头尾配对和两次因果调用，更新统一PrefillCPMetaData与双缓存映射，保留独立vLLM参考边界。
tags:
- task.optimization
- topic.attention
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/27
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/67
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/6733
  role: evidence
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/db51a1b9b6ee93c8c820b6833e244fe0405559b9/vllm_ascend/attention/context_parallel/sfa_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/db51a1b9b6ee93c8c820b6833e244fe0405559b9/tests/e2e/multicard/4-cards/long_sequence/test_basic.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:49:38Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      parallelism:
        all_of:
        - cp
---

# 因果稀疏注意力 CP prefill 的 zigzag 负载均衡：每 rank 两段两次调用 + 头尾因果前缀 actual_seq_lengths（qlen≠kvlen）

## 条件 → 该怎么切、怎么设 seqlen

对**因果掩码**的注意力（含稀疏注意力：[lightning-indexer](../../concepts/kernels/lightning_indexer.md) 算 topk 索引 + [sparse-flash-attention](../../concepts/kernels/sparse_flash_attention.md) 下游）在 prefill 阶段开 [context-parallel](../../concepts/parallelism/context_parallel.md)（query 沿序列维切到各 rank、KV 需完整）时，**不要按「连续切分 + rank r 独占第 r 个 token」的朴素方式切**——因果三角会让负载严重倾斜。正确做法是 **zigzag 头尾配对切分**，并且每 rank 对每个算子**发两次调用**、两次分别用「头段」「尾段」各自的因果前缀长度作 `actual_seq_lengths_key`。这是把 [long-seq-prefill-context-parallel](long_seq_prefill_context_parallel.md) 的 CP 策略落到因果稀疏注意力时，决定**正确性与均衡**的一处关键实现细节。

## 为何朴素连续切分不行（因果三角负载倾斜）

因果注意力下序列位置 `p` 的 token 要看 `p+1` 个 KV。若按「连续切分、rank r 领第 r 个 token」分 CP（例：prompt 长 16、16 卡、每卡 1 token），则各 rank 的因果前缀沿序列单调变长——头部 rank 的 token 只看很短前缀、算得轻，尾部 rank 的 token 几乎看全序列、算得重。各 rank 计算量沿因果三角单调递增，该例首尾分别处理 1 和 16 个 KV，比例为 16（即 CP），不是 2·CP，负载严重不均、拖慢整段 prefill。

## zigzag 头尾配对：段数 2·CP、每 rank 领一头一尾

把序列切成 `2·CP` 段（`cp_segment_num = cp_size * 2`）、每段长 `seg = ceil(seq_len / (2·CP))`（序列 pad/切到 `2·CP` 对齐），每个 rank 领**两段**：头段 index = `global_rank`、尾段 index = `2·CP − global_rank − 1`。「短前缀的头段 + 长前缀的尾段」配对后，每 rank 的因果总工作量≈常数，消除三角倾斜。

KV 侧跨 CP 组 `all_gather_into_tensor` 收齐、再按逆序索引重排还原成完整因果前缀，供两段调用共用（AllGather 一次、两段复用）。

## 关键：每 rank 每算子两次调用 + 头尾各自的因果前缀 seqlen

领到两段后，**每 rank 对每个算子发两次调用**（不是一次），把头段、尾段分别当一次 indexer / FA，二者共用同一份 all-gather 后的完整 K，仅切换 `q` 与 `actual_seq_lengths_key`：

```python
# 每段长 seg；rank = global_rank
kv_len_prev = seg * (global_rank + 1)          # 头段因果前缀长度
kv_len_next = seg * (2 * cp_size - global_rank) # 尾段因果前缀长度
actual_seq_q = seg                              # 两次调用的 query 有效长都是一段 seg

# lightning_indexer / sparse_flash_attention 各调两次（复用完整 K，仅换 q / kv_len）：
out_prev = op(q=q_prev, actual_seq_lengths_query=actual_seq_q, actual_seq_lengths_kv=kv_len_prev, ...)
out_next = op(q=q_next, actual_seq_lengths_query=actual_seq_q, actual_seq_lengths_kv=kv_len_next, ...)
result   = torch.cat([out_prev, out_next])     # 拼回该 rank 负责的两段输出
```

维护者给的算例（CP=16、序列 pad 到 `2·CP=32`、每段 `seg=1`）与上式逐项对上：rank r → 头 token r（kv 有效 `r+1`）、尾 token `2·CP−1−r`（kv 有效 `2·CP−r`）；即 rank0 →{头 kv 1，尾 kv 32}、rank1 →{2，31}、…。每次调用的 `actual_seq_lengths_key` 精确等于该段 token 的因果前缀长，配合完整 K，语义等价于单卡因果计算。

## qlen ≠ kvlen 是允许的（不必强求 q/kv 等长）

CP 下每 rank 只持 `q = seq/cp_size` 的 token，却对 AllGather 后的**完整 kv** 算注意力——**q 长与 kv 长天然不对等**。SFA 支持 qlen 与 kvlen 不对等（维护者确认），因此对 DSA/SFA 做 CP 切分时**无需强求 q/kv 等长**，也不必为对齐而 pad KV。这条边界让上面的头尾两段方案成立：每段 `actual_seq_lengths_query = seg` 远小于其 `actual_seq_lengths_key`（因果前缀）。

## 参考实现及其约束

当前cann-recipes-infer由ExecutionEngine._apply_prefill_cp逐请求构造PrefillCPMetaData，不再使用prepare_prefill_extra_input。模型使用local_prev_token_num/local_next_token_num拆Q，Indexer和SFA分别调用头/尾两次；每段actual_seq_q_prev/next为请求累计Q边界，kv_len_prev/next为每请求因果前缀。全局rank只在cp_size=world_size这一当前约束下与CP rank相同。

当前按每请求ceil(seq_len/(2CP))构造段长，可叠加模型cp_segment_min_len；不能用全batch一个seg替代不等长请求。计算cache与持久cache分别按global与persistent映射写入，见[MLA缓存规则](mla_prolog_zigzag_cp_kv_write.md)。此处是CANN Executor，不能标为SGLang入口。算子layout/必传长度仍须按实际所选LI/SFA接口核对。

## 应用在 vLLM：vllm-ascend PCP 的 head/tail q 切分

同一套「头尾配对 + 两段各自因果前缀 seqlen」在 **vllm-ascend** 上有一份独立参考实现（vLLM 语境下称 **PCP**：prefill-context-parallel，`prefill_context_parallel_size>1`），与 cann-recipes-infer/SGLang 版栈不同但算法同构——第二份跨框架实现印证了这套 zigzag 负载均衡不绑定单一框架。

- **分派入口**：`sfa_cp.py` 新增 `AscendSFACPImpl` / `AscendSFACPMetadataBuilder`；`sfa_v1.py` 经 `enable_cp()` 在 `get_builder_cls` / `get_impl_cls` 处分派到该 CP 变体。
- **两段 KV 前缀长度（`build_cp_metadata`）**，与本页头尾公式同构、按本实现变量写：
  - `q_head_kv_lens = (seq_lens // 2) * (pcp_rank + 1)`（头段因果前缀）
  - `q_tail_kv_lens = seq_lens * pcp_size - (seq_lens // 2) * pcp_rank`（尾段因果前缀）
- **切分与拼回用置换索引（非拼接 zigzag_index）**：head/tail query 由 `torch.index_select(x, 0, q_head_idx)` / `q_tail_idx` 取出，各调一次稀疏注意力，两段输出 `torch.cat([q_head_output, q_tail_output])` 后再 `torch.index_select(..., q_full_idx)` **按原 token 顺序拼回**。`q_head_idx` / `q_tail_idx` / `q_full_idx` 是 CP 侧预先算好的置换索引，来自框架 `prefill_context_parallel_metadata`（`common_long_seq_metadata.q_head_idx_tensor` 等）——本实现把「哪些 token 归头段/尾段、如何还原原序」外置成框架预置张量，而非在算子调用处现算重排。
- **indexer 侧**（`indexer_select_post_process`）用同一套 head/tail 切分生成 topk_indices。
- **昇腾侧算子入参**：每段一次 `npu_sparse_flash_attention`（`layout_query="TND", layout_kv="PA_BSND", sparse_mode=3`）与 `npu_lightning_indexer`（`sparse_count=2048`）；head/tail 的 `actual_seq_lengths_query = prefill_q_cum_seqlens // 2`、`actual_seq_lengths_kv` = 对应 head/tail KV 长度。`sparse_mode=3`（rightDownCausal）、`TND`/`PA_BSND` layout 与本页 DSA 参考实现一致。

上述 `q_head_idx` / `q_full_idx` 置换机制、`sparse_count=2048`、`prefill_q_cum_seqlens // 2` 等是**这份 vllm-ascend 实现的绑定细节**，非 zigzag 思想本身的限制。

该固定 vLLM 集成还明确注明 **PCP Prefill 不支持 MLAPO**，采用本节具体路径前须核对这一组合；这是参考实现的兼容边界，不是 zigzag 头尾切分算法的一般限制。其他前置条件见 [vLLM PCP/DCP 的 KV 重建路径](../../guides/integration/sfa_dsa_cp_cross_group_kv_allgather.md)。

## 正确性 / 风险 / rollback

- **正确性锚点**：两次调用的 `actual_seq_lengths_key` 必须精确等于该段 token 的因果前缀（头 `seg·(r+1)`、尾 `seg·(2·CP−r)`），算子计算前须完成 KV 汇聚与顺序恢复，并传入对应段的因果前缀长度；`_apply_prefill_cp` 可以提前构造长度元数据，不要求元数据晚于 all-gather 生成；错设会取错因果前缀、静默破精度。
- **均衡收益**：头短尾长配对使各 rank 因果工作量≈常数；本仓无独立复测 TTFT / per-rank 负载 / 吞吐 before→after 数字，收益为机制层结论（vllm-ascend 与 cann-recipes-infer 两份实现均只给整体正确性、未给负载/吞吐对比）。
- **源码中的测试配置**：固定 `test_basic.py` 的 `test_models_pcp_dcp_basic` 为 `vllm-ascend/DeepSeek-V3.2-W8A8-Pruning` 配置了 `enforce_eager=True, max_model_len=1024, TP=2, PCP=2, DCP=2, EP=True, block_size=128, quantization="ascend"` 并调用生成。该源码示例说明集成入口与参数组合，不表示本仓执行过测试，也不是下述分数对应的启动记录。
- **PR 自报精度**：PR6733 给出 AISBench 的 `gsm8k accuracy = 96.35` 日志和 vLLM `v0.15.0` 版本，但没有能将该分数与上述配置、硬件或完整启动参数关联的运行记录。该分数只作为作者自报保留，不能据此确认具体 PCP/DCP 组合或头尾切分的独立精度收益。
- **rollback（按实现区分）**：cann-recipes-infer 的参考路径将 `cp_size=1` 时回落单段、单次调用；vLLM 的 `pcp_size=1` 会绕过头尾切分，但 DCP 仍可独立参与 KV 聚合，不能把它等同于关闭全部上下文并行。
- **短序列边界**：DeepSeek-V4 的 CP 滑窗实现中，`last_rank==0` 且 `last_kv_len<window_size` 时，借上一段构造 last-window 的元数据逻辑可能失效；这是特定滑窗实现的边界，不是本页 DSA 两段因果前缀算法的一般失效条件，见 [zigzag-cp-short-seq-single-segment-window](../../runbooks/precision/zigzag_cp_short_seq_single_segment_window.md)。

## 反例 / 边界

- 适用面 = 因果注意力的 **CP prefill 负载均衡**；`sparse_mode`/layout/必传项等算子参数细节绑定 DSA 这两个算子，不外推为昇腾栈通用律。
- **阶段边界**：本页 zigzag 头尾 query 切分仅用于 **Prefill**。cann-recipes-infer 的上述参考实现按阶段取 `cp_size`，Decode 使用 1；vLLM 的 SFA 实现则会先聚合跨组 KV，再处理 Decode，`dcp_size>1` 时仍有 DCP 通信。后者的单段 Decode 不代表没有上下文并行，数据流见 [vLLM PCP/DCP 的 KV 重建路径](../../guides/integration/sfa_dsa_cp_cross_group_kv_allgather.md)。本卡 Scope 的 Prefill 限定指头尾切分规则。
- CP 下 MLA-prolog 的 paged KV cache 写法另有正确性要求，见 [mla-prolog-zigzag-cp-kv-write](mla_prolog_zigzag_cp_kv_write.md)。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/27)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/67)（evidence）
- [远程来源](https://github.com/vllm-project/vllm-ascend/pull/6733)（evidence）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（implementation）
- [远程来源](https://github.com/vllm-project/vllm-ascend/blob/db51a1b9b6ee93c8c820b6833e244fe0405559b9/vllm_ascend/attention/context_parallel/sfa_cp.py)（implementation）
- [远程来源](https://github.com/vllm-project/vllm-ascend/blob/db51a1b9b6ee93c8c820b6833e244fe0405559b9/tests/e2e/multicard/4-cards/long_sequence/test_basic.py)（supporting）
- [execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)（implementation）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py)（implementation）
