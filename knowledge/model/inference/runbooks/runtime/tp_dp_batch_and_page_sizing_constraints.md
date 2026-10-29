---
type: Runbook
title: TP+DP 非打包推理的 batch 整除约束 + DLLM paged 注意力 page_size≤block_size
description: TP+DP 非打包推理的 batch 整除约束 + DLLM paged 注意力 page_size≤block_size。在昇腾 executor 上配 TP+DP 或调 batch/显存时，主流程直接 ValueError 或稀疏注意力被守护回落——症状是「配置本身被拒」，不是算子/精度问题。
tags:
- task.debugging
- topic.parallelism
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/54
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/300
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/284
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:43:19Z'
platforms:
- agnostic
---

# TP+DP 非打包推理的 batch 整除约束 + DLLM paged 注意力 page_size≤block_size

## 信号（现象）

在昇腾 executor 上配 TP+DP 或调 batch/显存时，主流程直接 `ValueError` 或稀疏注意力被守护回落——症状是「配置本身被拒」，不是算子/精度问题。

## 触发条件 + 约束（对号入座）

### A. 非打包（BSH/BSND）路径的 batch 整除链

TP+DP 离线推理、`attn_dp_size > 1`、输入非打包（`packed_sequence=False`）时，`executor/infer.py` 强制两条整除：

- 全局 `batch_size % attn_dp_size == 0`（其中 `attn_dp_size = world_size // attn_tp_size`）；
- 每 DP-rank 的 `batch_size_per_rank = batch_size // attn_dp_size` 必须能被 `attn_tp_size` 整除。

任一不满足即 `ValueError`。**打包（TND）格式按 token 数切分、不受此约束**。

### B. 省显存把 batch 降到 1 的连锁约束

为省显存把 `batch_size` 调到 1 时：若 `attn_tp_size=1`（此时 `attn_dp_size=world_size`）则 `batch_size % attn_dp_size` 不成立、直接 `ValueError`。要真正把 batch 降到 `attn_dp_size` 以下须**同时增大 `attn_tp_size`**——所引用 check_parallel_settings 分支还限制 `attn_tp_size>1` 与 `oproj_tp_size>1` 的组合；该限制只适用于实际执行该校验的模型与版本。三个旋钮相互牵制，调一个要连带检查另两个。

### C. DLLM（LLaDA2.x）paged 注意力 page_size ≤ block_size

在昇腾跑 DLLM paged 注意力时，KV `page_size` 不得大于 DLLM `block_size`。参考实现在 scheduler 初始化处加守护：当 `dllm_config.block_size < page_size`（默认 page_size 128）时告警并把 `page_size` 回落到 `block_size`。配置时直接令 `page_size ≤ block_size` 避免回落。

## 修法 / 手段

- 命中 A/B：要么让 `batch_size` 满足整除链，要么**切到 TND 打包路径**（按 token 切分、免整除约束）——这也是仓的默认方向，见下「相关经验」。
- 命中 C：设 `page_size ≤ block_size`。

## 风险 / 边界

- 整除约束系于 executor 当前非打包路径实现，TND 路径不适用；迁移前确认走的是哪条布局。
- `attn_tp>1` 与 `oproj_tp>1` 互斥只属于所引 check_parallel_settings 分支，不能推广全仓。固定 LongCat 的 check_longcat_parallel_settings 允许两者均大于 1 且要求相等，须核对模型自己的校验入口。

## 相关经验

- TND packed-sequence 统一布局（免整除约束的默认路径）见 [tnd-packed-sequence-standard-and-bsnd-shim](../../optimizations/rules/tnd_packed_sequence_standard_and_bsnd_shim.md)。
- DP-attention + TP-oproj/MLP 混合（`oproj_tp` 语义）见 [dp-attention-tp-oproj-mlp-hybrid](../../optimizations/rules/local_tp_memory_heavy_projections.md)。

## Evidence

- `diff 事实`（@2c45117）：`check_parallel_settings` 强制 `batch_size % attn_dp_size==0`、该入口内 `attn_tp>1` 与 `oproj_tp>1` 的互斥校验，不适用于采用其他模型校验器的所有路径。
- `diff 事实`（@628e400）：`executor/infer.py` 双整除约束、TND 免除。
- `diff 事实`（@8cd85a8）：DLLM scheduler 守护 `page_size` 回落到 `block_size`。
- 溯源下探：[cann-recipes-infer-issue-54-bug-report-deepseek-v3-2-exp-w8a8c8-8p-16](https://gitcode.com/cann/cann-recipes-infer/issues/54)、[cann-recipes-infer-pr-300-refactor-support-tp-dp-inference-for-qwen3-moe-with-offline-mode](https://gitcode.com/cann/cann-recipes-infer/merge_requests/300)、[cann-recipes-infer-pr-284-feat-llada2-x-sglang-ascend](https://gitcode.com/cann/cann-recipes-infer/merge_requests/284)