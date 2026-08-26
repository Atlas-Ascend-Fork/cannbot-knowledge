---
type: Optimization
title: 因果稀疏注意力 CP prefill 的 zigzag 负载均衡：每 rank 两段两次调用 + 头尾因果前缀 actual_seq_lengths（qlen≠kvlen）
description: 对因果掩码的注意力（含稀疏注意力：lightning-indexer 算 topk 索引 + sparse-flash-attention 下游）在 prefill 阶段开 context-parallel（query 沿序列维切到各 rank、KV 需完整）时，不要按「连续切分 + rank r 独占第 r 个 token」的朴素方式切——因果三角会让负载严重倾斜。正确做法是 zigzag 头尾配对切分，并且每 rank 对每个算子发两次调用、两次分别用「头段」「尾段」各自的因果前缀长度作 actual_seq_lengths_key。这是把 long-seq-prefill-context-parallel 的 CP 策略落到因果稀疏注意力时，决定正确性与均衡的一处关键实现细节。
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
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 因果稀疏注意力 CP prefill 的 zigzag 负载均衡：每 rank 两段两次调用 + 头尾因果前缀 actual_seq_lengths（qlen≠kvlen）

## 条件 → 该怎么切、怎么设 seqlen

对**因果掩码**的注意力（含稀疏注意力：[lightning-indexer](../../../concepts/kernels/lightning_indexer.md) 算 topk 索引 + [sparse-flash-attention](../../../concepts/kernels/sparse_flash_attention.md) 下游）在 prefill 阶段开 [context-parallel](../../../concepts/parallelism/context_parallel.md)（query 沿序列维切到各 rank、KV 需完整）时，**不要按「连续切分 + rank r 独占第 r 个 token」的朴素方式切**——因果三角会让负载严重倾斜。正确做法是 **zigzag 头尾配对切分**，并且每 rank 对每个算子**发两次调用**、两次分别用「头段」「尾段」各自的因果前缀长度作 `actual_seq_lengths_key`。这是把 [long-seq-prefill-context-parallel](long_seq_prefill_context_parallel.md) 的 CP 策略落到因果稀疏注意力时，决定**正确性与均衡**的一处关键实现细节。

## 为何朴素连续切分不行（因果三角负载倾斜）

因果注意力下序列位置 `p` 的 token 要看 `p+1` 个 KV。若按「连续切分、rank r 领第 r 个 token」分 CP（例：prompt 长 16、16 卡、每卡 1 token），则各 rank 的因果前缀沿序列单调变长——头部 rank 的 token 只看很短前缀、算得轻，尾部 rank 的 token 几乎看全序列、算得重。各 rank 计算量沿因果三角单调递增，尾 rank ≈ 首 rank 的约 `2·CP` 倍，负载严重不均、拖慢整段 prefill。

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

参考实现见 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md)（[dsa](../../../concepts/modules/dsa.md) / [deepseek-indexer-attention](../../../concepts/kernels/deepseek_indexer_attention.md)，SGLang + PyPTO/AscendC 融合算子栈），`prepare_prefill_extra_input` 在 `cp_size>1` 分支给出 `cp_segment_num`、`zigzag_index`、`kv_len_prev/next`、`actual_seq_q`；`indexer.py` 的 CP prefill 路径 all-gather K 后两次调 `npu_lightning_indexer` 返回 `(topk_indices_prev, topk_indices_next)`，sparse_flash_attention 路径同样两次 `attn_func` 再 `cat`。以下是**该参考实现绑定这两个算子的约束，非 zigzag 思想本身的限制**——迁移「头尾配对 + 两段因果前缀 seqlen」这套算法到其它因果注意力 CP 时不受它们约束，照搬这套代码才受：

- `npu_lightning_indexer` 侧 `actual_seq_lengths_key` / `block_table` 当前**必传**。
- CP 下 `layout_query = "TND"`（packed 序列，故 `actual_seq_q` 走 `cumsum`）、`layout_key = "PA_BSND"`。
- `sparse_mode = 3`（rightDownCausal，右顶点下三角）承接因果语义。
- 序列需 pad 到 `2·CP` 对齐；KV 需跨 CP 组 all-gather；每 rank 每算子多一次 kernel 调用（代价换均衡）。

### 应用在 vLLM：vllm-ascend PCP 的 head/tail q 切分

同一套「头尾配对 + 两段各自因果前缀 seqlen」在 **vllm-ascend** 上有一份独立参考实现（vLLM 语境下称 **PCP**：prefill-context-parallel，`prefill_context_parallel_size>1`），与 cann-recipes-infer/SGLang 版栈不同但算法同构——第二份跨框架实现印证了这套 zigzag 负载均衡不绑定单一框架。

- **分派入口**：`sfa_cp.py` 新增 `AscendSFACPImpl` / `AscendSFACPMetadataBuilder`；`sfa_v1.py` 经 `enable_cp()` 在 `get_builder_cls` / `get_impl_cls` 处分派到该 CP 变体。
- **两段 KV 前缀长度（`build_cp_metadata`）**，与本页头尾公式同构、按本实现变量写：
  - `q_head_kv_lens = (seq_lens // 2) * (pcp_rank + 1)`（头段因果前缀）
  - `q_tail_kv_lens = seq_lens * pcp_size - (seq_lens // 2) * pcp_rank`（尾段因果前缀）
- **切分与拼回用置换索引（非拼接 zigzag_index）**：head/tail query 由 `torch.index_select(x, 0, q_head_idx)` / `q_tail_idx` 取出，各调一次稀疏注意力，两段输出 `torch.cat([q_head_output, q_tail_output])` 后再 `torch.index_select(..., q_full_idx)` **按原 token 顺序拼回**。`q_head_idx` / `q_tail_idx` / `q_full_idx` 是 CP 侧预先算好的置换索引，来自框架 `prefill_context_parallel_metadata`（`common_long_seq_metadata.q_head_idx_tensor` 等）——本实现把「哪些 token 归头段/尾段、如何还原原序」外置成框架预置张量，而非在算子调用处现算重排。
- **indexer 侧**（`indexer_select_post_process`）用同一套 head/tail 切分生成 topk_indices。
- **昇腾侧算子入参**：每段一次 `npu_sparse_flash_attention`（`layout_query="TND", layout_kv="PA_BSND", sparse_mode=3`）与 `npu_lightning_indexer`（`sparse_count=2048`）；head/tail 的 `actual_seq_lengths_query = prefill_q_cum_seqlens // 2`、`actual_seq_lengths_kv` = 对应 head/tail KV 长度。`sparse_mode=3`（rightDownCausal）、`TND`/`PA_BSND` layout 与本页 DSA 参考实现一致。

上述 `q_head_idx` / `q_full_idx` 置换机制、`sparse_count=2048`、`prefill_q_cum_seqlens // 2` 等是**这份 vllm-ascend 实现的绑定细节**，非 zigzag 思想本身的限制。

## 正确性 / 风险 / rollback

- **正确性锚点**：两次调用的 `actual_seq_lengths_key` 必须精确等于该段 token 的因果前缀（头 `seg·(r+1)`、尾 `seg·(2·CP−r)`），且写在 all-gather 完整 K **之后**；错设会取错因果前缀、静默破精度。
- **均衡收益**：头短尾长配对使各 rank 因果工作量≈常数；无独立复测 TTFT / per-rank 负载 / 吞吐 before→after 数字，收益为机制层结论（vllm-ascend 与 cann-recipes-infer 两份实现均只给整体正确性、未给负载/吞吐对比）。
- **e2e 正确性数据点（vllm-ascend PCP）**：`TP=2, PCP=2, DCP=2, EP=True, block_size=128, quantization="ascend"`、模型 `vllm-ascend/DeepSeek-V3.2-W8A8-Pruning` 下，gsm8k accuracy = 96.35（AISBench）。该数字锚定「头尾两段切分 + 拼回原序」的端到端正确性，不代表加速幅度。
- **rollback**：`cp_size=1` 即回落单段、单次调用的非 CP 因果路径。
- **短序列边界**：当序列短到有效 KV 落进单个段时，头尾配对的「借上一段」假设会失效，见 [zigzag-cp-short-seq-single-segment-window](../../../runbooks/precision/zigzag_cp_short_seq_single_segment_window.md)。

## 反例 / 边界

- 适用面 = 因果注意力的 **CP prefill 负载均衡**；`sparse_mode`/layout/必传项等算子参数细节绑定 DSA 这两个算子，不外推为昇腾栈通用律。
- decode 无 CP（CP 仅 prefill 生效），走单段路径。
- CP 下 MLA-prolog 的 paged KV cache 写法另有正确性要求，见 [mla-prolog-zigzag-cp-kv-write](mla_prolog_zigzag_cp_kv_write.md)。

## Evidence

- **diff 事实**（clone `@2c45117`）：`models/deepseek-v3.2-exp/models/modeling_deepseek.py::prepare_prefill_extra_input` 的 `cp_size>1` 分支给出 `cp_segment_num=cp_size*2`、`zigzag_index`、`kv_len_prev=seg*(rank+1)`、`kv_len_next=seg*(2CP-rank)`、`actual_seq_q=seg.cumsum`（CP=16/seg=1 与维护者算例逐项吻合）；`indexer.py::prefill_decode_ascendc` 在 CP prefill 下 all-gather K 后两次调 `npu_lightning_indexer`；同文件 sparse_flash_attention 路径两次 `attn_func`（prev/next）再 cat，与 indexer 共用同一 `actual_seq_q`/`kv_len_prev`/`kv_len_next`。
- **维护者确认**：SFA-under-CP 的 `qlen ≠ kvlen` 适用边界（「是否支持 qlen 与 kvlen 不对等？支持」）；zigzag 头尾配对 + 两次调用方案由维护者答复并标记 Accepted。
- **第二份跨框架实现（diff 事实，vllm-ascend）**：合并态（merge commit `db51a1b9`）新增 `vllm_ascend/attention/context_parallel/sfa_cp.py`——`build_cp_metadata` 的 `q_head_kv_lens=(seq_lens//2)*(pcp_rank+1)`、`q_tail_kv_lens=seq_lens*pcp_size-(seq_lens//2)*pcp_rank`，`_execute_sparse_flash_attention_process` 用 `index_select(q_head_idx/q_tail_idx)` 切两段各调一次 SFA、`cat` 后 `index_select(q_full_idx)` 拼回，`indexer_select_post_process` 同套逻辑；`sfa_v1.py` 经 `enable_cp()` 分派 CP 变体。gsm8k 96.35（AISBench，`TP=2/PCP=2/DCP=2/EP=True/block_size=128/quant=ascend`）为源自报整体正确性，无负载/吞吐 before→after。
- **仓自报（doc）**：zigzag（`cp_size*2` 头尾对称 + Token 重排还原因果）为仓官方推理指南「Prefill 并行策略」章节披露；`sparse_mode=3=rightDownCausal` 与「必传」为算子文档披露。「可迁移到其它因果注意力 CP」为对 zigzag 通用性的合理推断，算子参数细节不外推。
- 溯源下探：
  - [cann-recipes-infer-issue-27-question-ds-v3-2-sfa-cp-sp-mindie](https://gitcode.com/cann/cann-recipes-infer/issues/27)
  - [cann-recipes-infer-issue-67-question-torch-ops-custom-npu-sparse-flash-attention-torch-ops-custom-np](https://gitcode.com/cann/cann-recipes-infer/issues/67)
  - [vllm-ascend-pr-6733-feat-ds3-2-support-pcp](https://github.com/vllm-project/vllm-ascend/pull/6733)（sfa_cp.py @`db51a1b9`，PR#6733 merged）
