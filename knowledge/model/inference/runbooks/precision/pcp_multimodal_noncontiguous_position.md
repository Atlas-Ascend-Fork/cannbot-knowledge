---
type: Runbook
title: Prefill 上下文并行下多模态推理静默掉精度：非连续/非单调 position 与 embedding 错位
description: Prefill context parallel 下，多模态 token 被分配到各 worker 后，本地 position 可能非连续、非单调，若仍按连续区间切 prompt/MM embedding，会在无报错情况下产生精度偏差。修复包含两部分：按本地 position 通过 index_select/index_copy 取 embedding，并临时本地化 scheduler 的 token 与 encoder-input 计数；同一请求命中多个 MM feature 时，记录本地 token index 并稳定排序后再拼接，重叠 feature 使用 first-writer 去重，同时保活仍需使用的 encoder cache。仅 Prefill、cp_size>1、多模态、first PP rank 且非 encoder-decoder 路径触发；cp_size≤1 保持原连续逻辑。scheduler 本地化仍是临时 workaround。
tags:
- task.debugging
- topic.parallelism
- topic.precision
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/8038
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Prefill 上下文并行下多模态推理静默掉精度：非连续/非单调 position 与 embedding 错位

## 适用场景

同时满足以下条件时，本页描述的两类错位可能命中：

- **并行**：Prefill 阶段开启上下文并行（沿 Sequence 维切分请求 token 到多个 worker，`cp_size > 1`）。
- **输入**：多模态（图文）推理，请求含 image / video embedding，走 prompt-embeds 或 encoder-cache + MM embedding gather 路径；纯文本路径不受影响。
- **调度形态**：CP 会把**同一请求**的 token 切成**跨 worker 的非连续、且可能非单调**的 position 集合，且本地 worker 实际处理的 token 数**不等于** scheduler 的全局计数。

> 核心症状：**静默掉精度**——多模态输出精度异常，但无报错、无 crash、无编译失败。文本-only case 正常时首先怀疑本页。

CP 的输入准备原本假设「每请求的本地 token 是一段连续、单调递增的 position 区间」。这个假设在 CP 下不成立，会同时引出两个**正交**的错位点：一处在「按连续区间取 embedding」，一处在「多 feature embedding 拼接顺序」。二者互相独立，可能只中其一，也可能同时命中。

---

## 信号 A：按连续区间取 prompt-embeds / MM embedding 时错位

### 信号（现象）
- CP 开 + 多模态时输出精度异常；关掉 CP（`cp_size <= 1`）或换纯文本即恢复正常。这一「关掉 CP 精度即恢复」可作为排查手段用于定位本页错位面（对比 CP-on / CP-off 输出），而非该场景的既有测试断言。

### 触发条件
- 输入准备用「连续切片」取本请求 embedding，形如 `start_pos = num_computed_tokens[req]; end_pos = start_pos + num_sched`，然后 `req_embeds[start_pos:end_pos]`。
- MM embedding gather / encoder 调度直接消费 scheduler 的**全局** `num_scheduled_tokens` / `total_num_scheduled_tokens`。

### 根因
- CP 把一个请求的调度 token 拆成**非连续的 position**，因此「本地实际处理的这批 token」并不对应 `req_embeds` 里一段连续的行区间——按 `start_pos:end_pos` 连续切片会取到与本地实际 position 不匹配的 embedding 行。
- 同时本地 worker 处理的 token 数 ≠ scheduler 的全局计数，直接吃全局 `num_scheduled_tokens` 会把 encoder 调度、free list 释放都算错。

### 修法
1. **按 position 取数，而非按连续区间**：用本地实际调度到的 position 数组（如 `req_positions_np`）对 `req_embeds` 做 gather（`index_select` / `index_copy_`），取代 `start_pos:end_pos` 连续切片；越界 position 用 `valid_mask = req_positions < req_embeds.shape[0]` 过滤后再取。
2. **本地化调度视图**：先缓存一份本地 `num_scheduled_tokens[:num_reqs]`（`.copy()` 与会被复用的可变 batch 数组解耦）与其 total；进入 MM 预处理前，把 `scheduler_output` 的 `total_num_scheduled_tokens` / `num_scheduled_tokens` / `scheduled_encoder_inputs` / `free_encoder_mm_hashes` 临时替换成本地视图，预处理用 `try/finally` 结束后**还原**。为不污染上游 scheduler_output，可对其 `deepcopy` 后再改（这属临时 workaround，待框架层原生支持 CP+MM 后应移除）。
3. **encoder-cache 保活**：按本地 position 落在各 mm_feature 的 `[offset, offset+length)` 区间内重建本地的 `scheduled_encoder_inputs`；因为 CP 下全局 free list 可能早于本地消费而提前释放 encoder cache，需保留**所有 active 请求**的 mm_hash（`active_mm_hashes | local_needed_mm_hashes`），否则本地 gather 时会命中 `Encoder cache miss`（断言失败）。

---

## 信号 B：多 feature embedding 按 feature 顺序拼接与掩码遍历错位

### 信号（现象）
- 一个请求含 **>1 个 mm feature**（多图 / 多段视频）时精度异常；单 feature 请求可能正常。CP 开启是前提。

### 触发条件
- 消费端按本地 token index **升序**遍历 `is_mm_embed` 布尔掩码取用 mm_embeds。
- 生产端把各 feature 的 embedding 段按 **feature 枚举顺序**依次 concat。

### 根因
- CP 下同一请求的 position **非单调**。当生产端按 feature 顺序拼接、消费端按 token index 升序遍历时，两者顺序不一致 → embedding 被贴到**错误的 token** 上（精度错误，无报错）。

### 修法
- 每个 feature 命中的**本地 token index** 记入一个数组，对应 embedding 段记入另一个数组。
- 当命中 feature 数 >1 且行数一致（拼起来的 local index 总数 == embedding 总行数）时：拼接各段 local index 得 `local_idx_cat`，`torch.cat` 各段 embedding，用 **`np.argsort(local_idx_cat, kind="stable")`** 求稳定升序 `order`，再 `embed_cat.index_select(0, order)` 重排为单段，使 embedding 顺序与 `is_mm_embed` 掩码的升序遍历对齐。
- **行数不一致**（尺寸对不上）时**不重排**，`warning_once` 告警并跳过——保守回退，不静默改数据。
- overlapping mm feature（同一 token 被多个 feature 覆盖）用「first writer」OR 语义（`req_taken_mask`）去重，避免重复写同一 token。

---

## 前置条件与边界

- 仅 Prefill 阶段 + `cp_size > 1` + 多模态输入命中；Decode（单 token）、纯文本、`cp_size <= 1` 均不触发，修法应对 `cp_size <= 1` 保持原连续逻辑，不影响非 CP 路径。
- 只在 first PP rank、非 encoder-decoder 结构上处理 MM embedding。
- correctness 验证靠端到端多模态用例（多卡长序列多模态用例断言输出非空）；本类修复属机制性修复，通常无独立量化精度数字。

## 参考实现及其约束

- 参考实现来自 vLLM-Ascend worker（`vllm_ascend/worker/model_runner_v1.py` + `pcp_utils.py`）的 PCP（prefill context parallel）路径，围绕 `PCPManager` 组织：`fill_prompt_embeds_for_pcp`（按 position gather prompt-embeds）、`cache_local_schedule_layout` + `maybe_localize_scheduler_output_for_mm_preprocess` / `restore_scheduler_output_after_mm_preprocess`（本地化并还原 scheduler_output 四字段）、`build_local_mm_schedule`（encoder-cache 保活）、`gather_mm_embeddings_for_pcp`（多 feature 稳定重排）。
- **约束**（属该参考实现，非技术本身）：scheduler_output 的本地化/deepcopy 在源码注释中标为临时 workaround，待上游框架原生支持 CP+MM 后移除；重排仅在生产/消费行数一致时生效，尺寸不一致时告警跳过。
- 验证覆盖模型：Kimi、Qwen3-VL-8B-Instruct（TP2+CP2）、Qwen3.5-4B（TP1+CP4）。这些是参考实现的实测模型，非技术适用面上限。

## 相关静态概念

- [context-parallel](../../concepts/parallelism/context_parallel.md) — CP 沿 Sequence 切分请求 token 的机制与约束；本页是它在多模态 prefill 下的输入准备失效面。
- [ulysses](../../concepts/parallelism/ulysses.md) — 同属沿序列维切分的并行；若其多模态输入准备同样依赖「本地 token 是一段连续/单调区间」的假设，可参照本页按 position 取数（而非连续区间）的思路排查——这是可迁移的排查思路，非已在 Ulysses 上验证的结论。

## Evidence

- 根因「CP 把请求 token 切成非连续 position 且本地计数 ≠ 全局计数」「position 可能非单调，按 feature 顺序拼接会与布尔掩码升序遍历错位」对应源码内注释（`"PCP can split one request into non-contiguous token positions"`、`"Under PCP, request positions may be non-monotonic; concatenating by feature order can misalign embeddings with boolean mask traversal."`）。
- 溯源：`[pcp-prefill-上下文并行-下多模态推理静默掉精度-多模态-embedding-prompt-embed-按连续](https://github.com/vllm-project/vllm-ascend/pull/8038)`、`[pcp-下多模态-position-非单调-同一请求多个-mm-feature-的-embedding-若按-featu](https://github.com/vllm-project/vllm-ascend/pull/8038)`（vllm-project/vllm-ascend merge sha `8ba9808c81d456d74ad91cc4ee59016ff53c403f`，`model_runner_v1.py` / `pcp_utils.py`）。