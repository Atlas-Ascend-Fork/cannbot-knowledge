---
type: Optimization
title: KVCache 卸载到 Host + 稀疏 TopK-selection decode：跨 step 复用设备常驻选中块摊薄 H2D
description: KVCache 卸载到 Host + 稀疏 TopK-selection decode：跨 step 复用设备常驻选中块摊薄 H2D。把 KVCache 全量 卸载到 Host 以省 device 内存后，decode 每步需从 Host 取参与计算的 kv token，H2D 成为主要新增开销；且 decode 走稀疏注意力的 TopK-selection 路径（Lightning Indexer 产 topk 索引 → Sparse Flash Attention 计算），如 DeepSeek-V3.2-Exp 及同族 DSA 结构。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/134
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# KVCache 卸载到 Host + 稀疏 TopK-selection decode：跨 step 复用设备常驻选中块摊薄 H2D

## 适用场景
- 把 KVCache 全量 [卸载到 Host](../../../concepts/techniques/kvcache_offload.md) 以省 device 内存后，decode 每步需从 Host 取参与计算的 kv token，**H2D 成为主要新增开销**；且 decode 走稀疏注意力的 TopK-selection 路径（[Lightning Indexer](../../../concepts/kernels/lightning_indexer.md) 产 topk 索引 → [Sparse Flash Attention](../../../concepts/kernels/sparse_flash_attention.md) 计算），如 DeepSeek-V3.2-Exp 及同族 [DSA](../../../concepts/modules/dsa.md) 结构。

## 规则
- **利用相邻 step 在同一层的 TopK 命中集高度重叠**：稀疏注意力下相邻 token 在**同一层**的 TopK 选中集相似度高——重复 H2D 拉取重叠部分是浪费。
- **手段**：跨 decode step 记录哪些选中块已设备常驻（per-layer 的 block-status，decode 前重置为「未驻留」）；命中的块直接复用设备缓冲、**只对未复用块做 H2D**。昇腾侧由 [gather-selection-kv-cache](../../../concepts/kernels/gather_selection_kv_cache.md) 算子承载该跨-step 复用（依 indexer topk 选出参与块、喂 SFA）。
- **收益随相邻步 TopK 重叠率走**：重叠越高、需 H2D 的增量越少（doc 说明性举例：相邻两步各 2048 的 TopK 若 60% 相同，则只 H2D 40%、其余复用设备常驻块）。

## 边界
- 只在 sparse / TopK-selection + offload 的组合下成立；dense / full-attention 无「选中集重叠」可复用。
- 60%/40% 为 doc 说明数字、非受控实测；该复用的独立耗时数字未给，进一步降耗（如跨 layer 预取）仍为 open。

## 参考实现及其约束
- 参考 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md) 的 DeepseekIndexerAttention offload 路径：per-layer `selection_kv_block_status`、decode 前 `reinit_status()` 置 -1、decode 分支 `npu_gather_selection_kv_cache` 调用。block-status 跟踪是该参考实现细节，迁移到其它 DSA 结构时按其 topk 选择粒度重定「块」与状态表。

## 相关经验

- 另见 [ascendc SparseFlashAttention 非 PA(无 block table)decode 路由到未优化模板、慢于 tilelang](../../../runbooks/runtime/ascendc_sparse_flash_attention_non_pa_slow.md)。


## Evidence
- `diff 事实`（@18c1d975c6ec）：`modeling_deepseek.py` decode 分支的 `npu_gather_selection_kv_cache`、per-layer `selection_kv_block_status`、decode 前 `reinit_status()` 置 -1 均为实际 diff；「命中率相似度」机制来自 doc（与代码 block_status 逻辑一致），60%/40% 明标为说明性举例、不作性能数字。
- 溯源下探：[cann-recipes-infer-pr-134-feat-deepseek-v3-2-exp-model-support-kv-cache-offload](https://gitcode.com/cann/cann-recipes-infer/merge_requests/134)
- 相关：长序列 memory-bound decode 沿 S 维切 KV Cache 的另一路见 [kvp-longseq-decode](../../../guides/experience/interventions/kvp_longseq_decode.md)。

<!-- cannbot:related:start -->
## 相关

- [DSA/SFA 长序列服务化：跨步复用 top-k 索引（IndexCache）摊薄 indexer 选择开销换吞吐（GLM-5 W8A8 一次观测）](../benchmark_observations/dsa_indexcache_topk_reuse_throughput.md)（`related`）：每 N 步只重算一次、其余步复用上次缓存的 top-k 索引；跨 decode step 记录哪些选中块已设备常驻。前者通过缓存 TopK 索引减少 indexer 重算，后者基于同一 TopK 选择结果复用设备常驻 KV 块并减少 H2D；两者是 DSA decode 中相邻的两层跨步复用决策。
- [GatherSelectionKvCache](../../../concepts/kernels/gather_selection_kv_cache.md)（`related`）：算子据此判断当前步 TopK 哪些已在设备上、哪些需从 `full_kv_cache` gather，从而实现前后 Token 的 cache 复用。；**手段**：跨 decode step 记录哪些选中块已设备常驻（per-layer 的 block-status，decode 前重置为「未驻留」）；命中的块直接复用设备缓冲、**只对未复用块做 H2D**。昇腾侧由 ［gather-selection-kv-cache］(../../../concepts/kernels/gather_selection_kv_cache.md) 算子承载该跨-step 复用（依 indexer topk 选出参与块、喂 SFA）。。前者给出 block-status 驱动的算子行为，后者把同一行为上升为 offload decode 的跨步复用规则，能直接指导状态表实现与 H2D 减量验证。
- [KV cache 卸载到 Host 内存：设备单层 temp + 专用流 D2H 重叠 + 逐层异步搬算掩盖](../../../guides/experience/interventions/kvcache_offload_host_swap.md)（`related`）：KV offload 机制指出“offload 引入的 H2D 是 decode 新增开销，靠 decode 侧跨-step gather-selection 复用摊薄”；优化卡确认“decode 每步需从 Host 取参与计算的 kv token，**H2D 成为主要新增开销**”，把该风险收敛到 sparse TopK-selection 的跨步常驻块复用。
- [KVCache Offload](../../../concepts/techniques/kvcache_offload.md)（`related`）：**容量型 Offload（DeepSeek-V3.2-Exp）**：把 MLA Full KVCache 卸载到 Host 内存，设备仅留一层 cache，释放 HBM 以容纳更大的 batch 或更长的序列。Decode 阶段借助 Lightning Indexer TopK + `GatherSelectionKvCache` 算子，利用前后 Token 命中率复用设备端 cache，缓解 H2D 带宽压力。；**利用相邻 step 在同一层的 TopK 命中集高度重叠**：稀疏注意力下相邻 token 在**同一层**的 TopK 选中集相似度高——重复 H2D 拉取重叠部分是浪费。。概念卡提出命中率复用以缓解 H2D，规则卡把它落实为同层相邻 step 的设备常驻块复用。
<!-- cannbot:related:end -->
