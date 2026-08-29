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
updated_at: '2026-08-25T06:41:27Z'
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

为省显存把 `batch_size` 调到 1 时：若 `attn_tp_size=1`（此时 `attn_dp_size=world_size`）则 `batch_size % attn_dp_size` 不成立、直接 `ValueError`。要真正把 batch 降到 `attn_dp_size` 以下须**同时增大 `attn_tp_size`**——但 `attn_tp_size>1` 又与 `oproj_tp_size>1` 互斥。三个旋钮相互牵制，调一个要连带检查另两个。

### C. DLLM（LLaDA2.x）paged 注意力 page_size ≤ block_size

在昇腾跑 DLLM paged 注意力时，KV `page_size` 不得大于 DLLM `block_size`。参考实现在 scheduler 初始化处加守护：当 `dllm_config.block_size < page_size`（默认 page_size 128）时告警并把 `page_size` 回落到 `block_size`。配置时直接令 `page_size ≤ block_size` 避免回落。

## 修法 / 手段

- 命中 A/B：要么让 `batch_size` 满足整除链，要么**切到 TND 打包路径**（按 token 切分、免整除约束）——这也是仓的默认方向，见下「相关经验」。
- 命中 C：设 `page_size ≤ block_size`。

## 风险 / 边界

- 整除约束系于 executor 当前非打包路径实现，TND 路径不适用；迁移前确认走的是哪条布局。
- `attn_tp>1` 与 `oproj_tp>1` 互斥是本仓约束，与 DP-attention+TP-oproj 混合并行相关（见相关经验）。

## 相关经验

- TND packed-sequence 统一布局（免整除约束的默认路径）见 [tnd-packed-sequence-standard-and-bsnd-shim](../../optimizations/experience/rules/tnd_packed_sequence_standard_and_bsnd_shim.md)。
- DP-attention + TP-oproj/MLP 混合（`oproj_tp` 语义）见 [dp-attention-tp-oproj-mlp-hybrid](../../optimizations/experience/rules/dp_attention_tp_oproj_mlp_hybrid.md)。

## Evidence

- `diff 事实`（@2c45117）：`check_parallel_settings` 强制 `batch_size % attn_dp_size==0`、`attn_tp>1` 与 `oproj_tp>1` 互斥。
- `diff 事实`（@628e400）：`executor/infer.py` 双整除约束、TND 免除。
- `diff 事实`（@8cd85a8）：DLLM scheduler 守护 `page_size` 回落到 `block_size`。
- 溯源下探：[cann-recipes-infer-issue-54-bug-report-deepseek-v3-2-exp-w8a8c8-8p-16](https://gitcode.com/cann/cann-recipes-infer/issues/54)、[cann-recipes-infer-pr-300-refactor-support-tp-dp-inference-for-qwen3-moe-with-offline-mode](https://gitcode.com/cann/cann-recipes-infer/merge_requests/300)、[cann-recipes-infer-pr-284-feat-llada2-x-sglang-ascend](https://gitcode.com/cann/cann-recipes-infer/merge_requests/284)

<!-- cannbot:related:start -->
## 相关

- [attention 走 DP 时对 o_proj / dense-MLP 单独 TP：DP→TP→DP 边界通信省单卡内存与权重搬运](../../optimizations/experience/rules/dp_attention_tp_oproj_mlp_hybrid.md)（`related`）：在昇腾 executor 上配 TP+DP 或调 batch/显存时，主流程直接 `ValueError` 或稀疏注意力被守护回落——症状是「配置本身被拒」，不是算子/精度问题。；此时 attention 与 MLP 并行域不同，需在边界插通信做 DP↔TP 域转换。；运行手册给出非打包 TP+DP 的 batch 整除失败条件，优化规则解释 attention DP 与 o_proj/MLP TP 之间必须显式转换并行域，二者用于配置同一混合并行链。
- [昇腾推理统一 TND packed-sequence 布局：为何是标准、BSND/packed-1D shim 的等长约束与变长崩溃](../../optimizations/experience/rules/tnd_packed_sequence_standard_and_bsnd_shim.md)（`related`）：executor-core 把 TND（packed sequence）定为 attention 的**默认且唯一**布局——prefill 与 decode 两阶段、dense 与 MoE 模型统一走 TND，原 `packed_sequence` 开关被删除、非打包/BSH 路径不再保留。；任一不满足即 `ValueError`。**打包（TND）格式按 token 数切分、不受此约束**。。前者说明默认迁移方向，后者给出采用 TND 可绕开的非打包 TP+DP 整除失败。
<!-- cannbot:related:end -->
