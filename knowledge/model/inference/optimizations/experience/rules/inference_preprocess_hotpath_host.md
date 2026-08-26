---
type: Optimization
title: 推理输入预处理（host 侧）两类坑：大 batch 分词 host OOM + 逐 batch .item() 同步 / 逐次整数算术
description: 推理输入预处理（host 侧）两类坑：大 batch 分词 host OOM + 逐 batch .item() 同步 / 逐次整数算术。推理的输入准备 / 预处理阶段（分词、按 batch 展平写 KV、位置换算）跑在 host CPU、且大 batch / 每 step 都触发。两类隐蔽坑：一类吃 host CPU 内存导致 OOM，一类每步触发 device→host 同步拖慢 launch。注意力算子入参（FA scale / seq-length / 量化 scale）的同类去同步见 decode-host-scalar-precompute-passthrough，本页管分词与 KV-写 / 预处理热路径。
tags:
- task.optimization
- topic.model_architecture
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/138
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/282
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 推理输入预处理（host 侧）两类坑：大 batch 分词 host OOM + 逐 batch .item() 同步 / 逐次整数算术

## 适用场景

推理的输入准备 / 预处理阶段（分词、按 batch 展平写 KV、位置换算）跑在 host CPU、且大 batch / 每 step 都触发。两类隐蔽坑：一类吃 host CPU 内存导致 OOM，一类每步触发 device→host 同步拖慢 launch。注意力算子入参（FA scale / seq-length / 量化 scale）的同类去同步见 [decode-host-scalar-precompute-passthrough](decode_host_scalar_precompute_passthrough.md)，本页管**分词与 KV-写 / 预处理热路径**。

## 坑一 · 大 batch 分词一次性全量 → host CPU OOM

dataset benchmark 的输入构造若用单次 `tokenizer(prompts).input_ids` 对**全部** prompts 一次性分词、且不截断，query 数很多时会一次性在 host 持有全量 token id（且无长度上限），耗尽 host CPU 内存。

**修法**：分段 + 截断 + 关 attention_mask：
- **分段**：按 `section_size`（如 1024）一段段分词，不一次性持有全量。
- **截断**：`truncation=True, max_length=input_max_len`，让每条 token id 长度受上限约束，避免超长文本产生巨大 id 列表。
- **关闭 attention_mask**：`return_attention_mask=False` 少构造一份等长张量。

## 坑二 · 逐 batch 循环 .item() 同步 + 热路径逐次整数算术

按 batch 展平写 KV 这类每 step 跑的预处理热路径上有两个反模式：

- **逐 batch 循环里对 device 张量 `.item()`**（如 `for b: start=int(indptr[b].item())`）：每个 `.item()` 触发一次 device→host 同步（打断流水、拖慢 launch），且 Python 循环开销随 batch 线性上升。
- **热路径每次现算整数 `//` / `%`**（如每次 `append_kvcache` 都 `page = pos // page_size; entry = pos % page_size`）：同样的位置→页号 / 页内偏移映射被反复计算。

**修法（向量化 + 预建查表）**：
- **用 `searchsorted` 消除逐 batch 循环与 `.item()`**：对累积 offset 数组做 `torch.searchsorted(indptr[1:], arange(nnz), right=True)` 一次算出每个展平 token 的 batch 索引，再由 offset / 序列长度向量化推出写入位置；全程无 `.item()` / 无 device→host 同步（`nnz==0` 加早返回避免空 batch 边界）。
- **预建位置查找表替代逐次 `//` / `%`**：在层 `__init__` 按 `max_seqlen` 一次性建 `pos2page = pos // page_size`、`pos2entry = pos % page_size` 两张表存到 device，热路径改用 `pos2page.index_select(0, pos)` 查表，把每步整数除模换成一次 gather。

## 判断准则

推理预处理 / 输入准备阶段：大 batch 一次性 host 侧构造（分词 / 全量张量）优先分段 + 截断防 host OOM；每 step 现算、可提前 / 可批量的 host 侧循环与整数算术优先向量化算子（searchsorted）+ 预建查表，去掉逐元素 `.item()` 同步。手段本身不限于观测模型。收益方向明确，源未给量化数字。

## 参考实现及其约束

分词分段参考 cann-recipes-infer 的 dataset benchmark 预处理（[cann-executor](../../../concepts/frameworks/cann_executor.md) 的 `executor/utils/data_utils.py` `tokenizer_in_loop`，`section_size=1024` 默认）；searchsorted / 查表参考 [hstu](../../../concepts/models/hstu.md) 的 `get_batch_indices_positions` / `append_kvcache`。`section_size` 默认值、触发 OOM 的具体 query 数阈值为参考实现细节 / 未给。

## Evidence

- `diff 事实`（@14e61fb855ed）：`tokenizer_in_loop` 的 `section_size=1024` + `truncation=True, max_length=input_max_len, return_attention_mask=False` + `build_dataset_input` 改循环分词；commit `fix tokenizer host oom` 交叉印证问题即 host OOM。
- `diff 事实`（@99cf645981392c）：`gpu_kv_cache_manager.py` 的 `get_batch_indices_positions` 新旧实现 + `nnz==0` 早返回 + searchsorted、`paged_hstu_infer_layer.py` 的 `build_pos_tables` + `append_kvcache` 改 `index_select` 查表。
- 溯源下探：
  - [cann-recipes-infer-pr-138-fix-add-adaptive-system-prompts-and-fix-eos-outputs-in-dsr1-qwen-and-fix](https://gitcode.com/cann/cann-recipes-infer/merge_requests/138)
  - [cann-recipes-infer-pr-282-feat-hstu-model-add-kv-offload-and-optimize-preprocessing](https://gitcode.com/cann/cann-recipes-infer/merge_requests/282)
