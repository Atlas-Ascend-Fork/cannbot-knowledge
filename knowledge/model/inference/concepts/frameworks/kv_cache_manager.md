---
type: Concept
title: KV Cache Manager（框架级 Paged Attention KV Cache 管理）
description: Executor 缓存管理的四种策略、manager_key 分组、压缩布局、HBM 与 swapped 分配、owner 选择、投机状态预留及 PD 导出限制；按当前实现核对容量公式与接入契约。
tags:
- task.implementation
- topic.architecture
- topic.kv_cache
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/cache_info.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/kv_cache_manager.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/single_type_kv_cache_manager.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/cache_utils.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/block_pool.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/kv_cache_design.md
  role: supporting
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
platforms:
- agnostic
---

# KV Cache Manager（分页缓存与固定状态管理）

## Summary

`executor/core/kv_cache/` 按 `KVCacheManager → SingleTypeKVCacheManager → BlockPool` 三层管理请求、逻辑块和物理块。当前支持 `FullAttention`、`SlidingWindow`、`RingCache`、`Mamba` 四种策略；后两者分别管理循环缓冲和固定形状状态，不能一律按逐 token 的 KV Cache 理解。

模型的 `get_cache_info()` 返回 `ModelCacheInfo` 时，由框架规划、分配和绑定缓存；未返回时才走模型自管的 fallback。Gemma 4 和 Hy3 当前均实现 `get_cache_info()`，不能再作为“只支持模型自管连续缓存”的例子。

## 分组与元数据契约

- `CacheEntry` 声明 `attn_type`、`block_size`、`manager_key`、`dim`、`num_head`、`dtype`、`tensor_setter`、`needs_block`，以及 `allocator`、`compress_ratio`、`cache_layout` 等存储属性。`dim` 可描述复合维度，通过 `cache_dim_numel()` 取得元素数。
- `group_key` 优先取显式 `manager_key`，否则取 `attn_type`。同一类型可拆成多个 manager；共享 manager 的条目必须满足同一类型、块大小及该策略的附加约束。FullAttention 还校验压缩比，Mamba 校验 `next_n`。
- `LayerCacheInfo` 汇集一层的条目；`ModelCacheInfo` 汇集所有层并声明 `is_mla_backend`，不接受模型级 `block_size`。`merge()` 校验 MLA 标志、偏移另一份的层索引后合并，用于主模型和草稿模型共同管理。
- `is_mla_backend` 必须显式声明，不能由 `num_head == 1` 推断：GQA 切分后也可能每 rank 只有一个 KV head。PD 传输据此判断 MLA 缓存是否复制。

`block_table`、`slot_mapping`、block id、容量与使用率均按 **manager key** 索引，而不是仅按注意力类型。多个条目共享 key 时共享逻辑索引；需要不同块粒度时必须使用不同 key。

## 三层职责

| 层 | 职责 |
|---|---|
| `KVCacheManager` | 筛选本次参与的 managers，统一预检、分配、查询和释放请求资源 |
| `SingleTypeKVCacheManager` | 维护 `req_to_blocks`、逻辑块布局、跳过与回收策略及 `_null_block` |
| `BlockPool` | 用 FIFO `deque` 分配空闲物理块，用集合检测重复释放 |

BlockPool 初始预留一个 `_null_block`，只作合法索引占位；释放它会被忽略，释放已经空闲的普通 block 则抛 `ValueError`。空闲普通块从队首取出、回收到队尾。这里没有证明跨请求 prefix caching，不能把物理块回收复用等同于前缀共享。

## allocate_slots：对选定分组先预检后分配

```python
allocate_slots(request_id, computed_tokens, num_new_tokens,
               lookahead_tokens=0, reserved_tokens=0, manager_keys=None)
```

先将已计算长度和本次所需长度截断到 `max_model_len`：

```text
total_computed_tokens = min(computed_tokens, max_model_len)
num_tokens_need_slot = min(computed_tokens + num_new_tokens + lookahead_tokens,
                           max_model_len)
```

`manager_keys=None` 选择全部分组，指定集合则只处理这些分组。对选定分组先 `remove_skipped_blocks`，再调用含 `lookahead_tokens` 的 `pre_allocate_blocks`；任一不满足就返回 False，不分配新块。回收旧块已经可能发生，因此这不是回滚全部操作的事务。全部通过后才逐一 `allocate_new_blocks`。

`get_request_owner_manager_keys(is_owner)` 在 owner rank 保留全部分组，在非 owner rank 只保留 Mamba 状态。不能再把每次申请描述为无条件广播到全部分组。

## 四种策略

| 策略 | 物理块与请求的关系 |
|---|---|
| FullAttention | 随总长度追加，所需逻辑块为 `ceil(num_tokens / block_size)`；预检还考虑已登记请求的 `reserved_tokens` 预留 |
| SlidingWindow | 仅有效窗口保留真实块，历史逻辑位置以 null block 补齐，窗口滑出后回收 |
| RingCache | 每个请求首次申请一个固定容量块，随后循环覆盖，直到请求结束才释放；块表宽度固定为 1 |
| Mamba | 每请求一个固定形状状态，后续为投机步骤扩展到 `1 + next_n` 个状态块，不做 token 窗口回收 |

SlidingWindow 的本轮布局包含 lookahead：

```text
valid_tokens = num_tokens - lookahead_tokens
first_valid_token = max(0, (valid_tokens - 1) - sliding_window)
first_valid_block = first_valid_token // block_size
last_block = (num_tokens - 1) // block_size
real_blocks_needed = last_block - first_valid_block + 1
```

窗口前的无效逻辑块仍占块表位置，但不占普通物理块。不能使用整段序列的 `ceil` 值估算其真实占用。

`MambaCacheEntry` 的 `block_size=1` 表示一个完整状态，`shape` 是非空的正整数维度列表，`next_n>=0`；`dim`、`num_head` 不用于该状态布局。入场时只先分配一个，后续申请补齐草稿状态，而不是初次就全部占用。

## 逻辑粒度、物理布局和索引

`storage_block_size = block_size // compress_ratio`，要求整除。普通缓存支持 `BnBsND` 与 `BnNBsD` 布局：分别以 `[blocks, storage_block, heads, *dim]` 和 `[blocks, heads, storage_block, *dim]` 分配。`CacheAllocator` 可选 HBM 或 swapped memory；Mamba 状态形状为 `[blocks, *shape]`，当前只接受 HBM。

`prepare_block_tables(..., is_prefill=...)` 按 manager key 生成索引。Mamba 的 Prefill 表宽为 1，Decode 表宽为 `1 + next_n`；真实请求缺少所需状态块会报错，dummy 请求用 null block 填充。

普通未压缩缓存的 slot mapping 使用 `position // block_size` 和 `position % block_size`。Mamba 直接按块表寻址，不生成 token slot；`compress_ratio>1` 的条目同样跳过普通逐 token slot 生成，由模型的压缩缓存逻辑处理。RingCache 使用 `block_id * block_size + position % block_size`，同次请求超过容量时只保留最后一圈的写入，其余置 -1，避免环绕位置冲突；null block 对应槽位也置 -1。

## 容量与显存预算

`FIXED_BLOCK_ATTN_TYPES` 包含 SlidingWindow、Mamba、RingCache。最大并发数取 `batch_size_per_dp_rank`：

| 类型 | 规划块数（含末尾一个 null block） |
|---|---|
| SlidingWindow | `concurrency * (ceil((sliding_window + 2*next_n) / block_size) + 1) + 1` |
| Mamba | `concurrency * (1 + cache.next_n) + 1` |
| RingCache | `concurrency + 1` |

SlidingWindow 括号内额外一个块覆盖窗口跨块边界；`2*next_n` 覆盖主模型校验和草稿继续推测的预留。相同 manager key 的固定条目必须给出相同块数。仅 HBM 条目计入这里的 NPU 常驻缓存预算。

FullAttention 等非固定类型：

- **离线**：`ceil(offline_max_len / block_size) * local_concurrency + 1`。FullAttention 启用 `offline_prefill_dp_group_size>1` 时，`local_concurrency` 是每 DP rank batch 再除以该分组大小，其他条目不使用这个分区因子。分页 HBM、固定 HBM 和 `extra_reserved_memory_bytes` 的总需求超过当前 free memory 时提前报错。
- **在线**：可用预算为 `total_memory * mem_fraction_static - used_memory - fixed_block_memory_bytes - extra_reserved_memory_bytes`。每 token 字节数按 HBM 条目的 `cache_dim_numel * num_head * dtype_size // compress_ratio` 求和，先换算 token 容量，再按各 manager 的逻辑块大小换算块数；TP 组用 all-reduce MIN 统一最保守 token 容量。null block 从已算出的块数中扣除，不额外加一。
- 在线动态规划要求至少一个 HBM 分页条目；全部分页缓存都放 swapped memory 时会报错，需用离线容量规划或保留 HBM 分页条目。不能把被 offload 的缓存和工作区都当作零 NPU 预算：模型的 `OffloadWorkspaceMemoryInfo` 还能报告需额外预留的 NPU 内存。

在线最终用最小的 `(block_num - 1) * block_size` 检查所需 Prefill token 容量，保留源码中的边界余量检查。

## PD 导出与模型自管边界

`get_contiguous_buf_infos()` 按层索引和层内条目次序，仅导出 `needs_block=True` 的缓存，返回 `(data_ptrs, data_lens, item_lens, attn_types, block_sizes)` 五个等长列表。`attn_types` 实际为 manager key；`item_lens` 和 `block_sizes` 使用压缩后的 **storage_block_size**。两端必须有一致的缓存定义与导出次序。当前导出遇到 Mamba 会抛 `NotImplementedError`，不能据此宣称已支持 Mamba 状态的 PD 传输。

模型未提供 cache-info 时，`ModelWorker.init_kvcache()` 优先调用模型 `init_cache(device)`，否则按模块的 `k_cache`、`v_cache` 和 `cache_unit` 做 legacy 连续分配。该 fallback 不等于自动获得框架分页、在线调度或 PD 能力；新接入应明确实现元数据、分配与 forward 索引消费。

## 接入与核验

按 `get_cache_info → validate_cache_info → calculate_block_num → allocate_cache_tensors → create_single_type_managers → KVCacheManager` 检查初始化，再核对运行期的 allocate、块表和 slot mapping、模型实际读写以及 free。新增类型要同时扩展 manager 注册、容量规划、tensor 分配和索引路径。`format_usage()` 输出为 `manager_key:used/total`，block size 由 `get_block_sizes()` 单独查询。

## Evidence

- [cache_info.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/cache_info.py)（primary）
- [kv_cache_manager.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/kv_cache_manager.py)（implementation）
- [single_type_kv_cache_manager.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/single_type_kv_cache_manager.py)（implementation）
- [cache_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/cache_utils.py)（implementation）
- [block_pool.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/block_pool.py)（implementation）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（implementation）
- [kv_cache_design.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/kv_cache_design.md)（supporting）

## Links

- [Executor](cann_executor.md)
- [在线 PD 推理](online_pd_inference.md)
- [推理配置](../techniques/inference_config.md)
- [投机解码](../techniques/mtp_speculative_decoding.md)
- [MLA](../modules/mla.md)
- [Gemma 4](../models/gemma4_26b_a4b.md)
- [Hy3](../models/hy3_preview.md)
