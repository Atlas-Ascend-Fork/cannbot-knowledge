---
type: Concept
title: 长度感知重采样（Length-Aware Resampler：按历史 response 长度的 rollout 重排）
description: On-policy RL 训练的 rollout（generate）阶段普遍存在 response 长尾：不同 prompt 的生成长度差异极大，而一个 generation batch 内往往同时混入极长与极短样本。这带来两个直接问题——同批次内短样本很快结束、长样本持续占用推理资源，整体吞吐被少量长尾样本拖慢；某些 batch 的生成长度远高于平均值，放大 step 时间抖动。长度感知重采样（length-aware resampler）是在 verl 的 RL 数据采样路径上新增的 LengthAwareEpochSampler：它利用上一轮 rollout 收集到的 response 长度统计，在下一轮 epoch 开始时对样本顺序重排，把预估长度接近的 prompt 尽量放到邻近 batch，从而在 batch 级别减少长短样本混排。
tags:
- task.optimization
- topic.reinforcement_learning
- topic.data_pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 长度感知重采样（Length-Aware Resampler：按历史 response 长度的 rollout 重排）

## Summary

On-policy RL 训练的 rollout（generate）阶段普遍存在 **response 长尾**：不同 prompt 的生成长度差异极大，而一个 generation batch 内往往同时混入极长与极短样本。这带来两个直接问题——**同批次内短样本很快结束、长样本持续占用推理资源，整体吞吐被少量长尾样本拖慢**；**某些 batch 的生成长度远高于平均值，放大 step 时间抖动**。长度感知重采样（length-aware resampler）是在 [verl](../frameworks/verl.md) 的 RL 数据采样路径上新增的 `LengthAwareEpochSampler`：它利用**上一轮 rollout 收集到的 response 长度统计**，在下一轮 epoch 开始时对样本顺序重排，把预估长度接近的 prompt 尽量放到邻近 batch，从而在 batch 级别减少长短样本混排。

`LengthAwareEpochSampler` 用历史统计 + EMA 长度估计 + 分桶重排 + 稳定样本 id 回写解决长尾混排，并提供 `response_max_tokens_cap` 动态裁剪作为可选长尾保护。它与 [rollout-rebalance](rollout_rebalance.md)（推理引擎内动态迁移任务）互补：长度感知重采样在**数据采样侧**事前重排、Rebalance 在**vLLM 内部**事中迁移，两者都为同一个 rollout 长尾问题服务。

## 为什么 rollout 长尾会拖慢训练

RL 同步训练里，一个 generation batch 内的所有样本必须**全部生成完毕**才能进入 ref / update 阶段。当 response 长度呈长尾分布时，短样本早早退出、长尾样本独占推理资源，形成「木桶效应」——短任务所在的 DP 组完成后只能闲置等待，直到长尾任务也结束才能同步进入下一轮。下图（qwen3-235B 2K 推 32K 实践）展示了 response 长度的实际长尾分布：DeepScalar 数据集一次推理中绝大多数样本在 5K~10K 早期退出，仅少数长尾样本逼近最大长度。

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image7.png" width="55%">
<sub>图：单个 DP 域内 256 条回复的 response 长度分布——多数样本在早期退出、少数长尾样本逼近最大长度，正是长度感知重排要利用的统计规律（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B RL 优化文档（图源）</a>·§1 简介 / response 长尾）</sub>

长尾样本与短样本混排时，整批 generation 被最长那条样本拖住；下图把这种「木桶效应」可视化：同一组 NPU 上各样本生成长度参差，最短的那些核早早完成却必须等齐最长样本，才能一起进入 ref prefill / reward&adv / policy update。

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image15.png" width="55%">
<sub>图：长尾 response 的木桶效应——同批内短样本（短条）完成后空等长尾样本（长条），全批对齐后才进入 ref/reward/update（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B RL 优化文档（图源）</a>·rollout 长尾负载不均）</sub>

长度感知重采样的核心思路：**目标不是精确预测每条样本的输出长度，而是在 batch 级别减少长短样本混排**——把预估长度相近的 prompt 聚到邻近 batch，使每个 generation batch 内长度更齐整，缩短「木桶」的桶板差。

## `LengthAwareEpochSampler` 实现机制

新增的 `LengthAwareEpochSampler` 继承 `AbstractCurriculumSampler`，核心做法是「**用上一轮 rollout 统计驱动下一轮 epoch 的样本重排**」：

> 1. 每个样本维护一个 response 长度估计值。
> 2. 在训练 step 完成后，通过 `response_mask.sum(-1)` 统计真实 response 长度。
> 3. 将统计结果按样本 id 聚合，并使用 EMA 更新样本的长度估计。
> 4. 在下一轮 epoch 开始时，依据估计长度排序，并按 batch block 做可选打散。

排序是两级的——`np.lexsort((tie_break, est, bucket))`：先按 `floor(est/bucket_size)` 粗分桶、桶内再按精确估计长度 `est`、同长度用随机 `tie_break` 打散。`bucket_size` 正是控制分桶粗细的承重旋钮：调大则分桶越粗、桶内允许的长度跨度越大、越倾向保留批间随机性；调小则分桶越细、批内长度越齐整（极端到 1 即退化为纯按精确长度排序）。`shuffle_batch_blocks` 再在排好序的 batch block 之间整体打散，避免长样本永远集中在 epoch 尾部。

三个工程细节保证重排稳定可用：

- **稳定样本 id 回写**：为把 rollout 统计稳定回写到 dataset，`RLHFDataset.__getitem__` 返回的样本新增 `dataset_item_idx` 字段，使用 dataset 内部样本索引——保证**不同 epoch 间能回到同一条原始样本**，EMA 长度估计才不会错位。
- **训练集按完整 batch 对齐**：训练集样本数向下截断到 `gen_batch_size` 的整数倍；在 `drop_last=True` 前提下，每个 epoch 看到固定的 prompt 集合，**避免尾部零散样本在 epoch 切换时扰乱长度统计**。
- **EMA 平滑**：`ema_decay`（默认 0.7）让长度估计兼顾历史与最新一轮，抵抗单轮采样波动。

## 可选长尾保护：rollout 动态下发 response cap

即便做了长度重排，仍可能存在极个别 batch 的 response 长度远超平均值。为此特性提供了一个**可选的 `max_tokens` 动态裁剪**。当 dataloader sampler 为 `AbstractCurriculumSampler` 时，trainer 在生成前读取当前 batch 的历史长度估计，算出一个 `response_max_tokens_cap`，再在 vLLM rollout 侧通过覆写 `SamplingParams.max_tokens` 把该 cap 下发给本批次生成请求。裁剪逻辑：

```text
cap = min(response_length, max(min_tokens, factor * expected_len))
```

其中 `expected_len` 为当前 batch 样本在历史统计中的平均 response 长度估计值。这一保护有两个特点：

> 1. 不修改全局 rollout `response_length` 配置，只对当前 batch 生效。
> 2. 如果计算得到的 cap 不小于原始 `response_length`，则保持原行为不变。

控制裁剪强度的环境变量：

```bash
export VLLM_ROLLOUT_EARLY_STOP_ENABLE=1
export VLLM_ROLLOUT_EARLY_STOP_FACTOR=2.0
export VLLM_ROLLOUT_EARLY_STOP_MIN_TOKENS=10000
```

> ⚠️ `response_max_tokens_cap` 是保守的长尾保护机制：若任务对完整长响应有强依赖，应谨慎设置 `factor` 和 `min_tokens`，避免过早截断有效推理。

## 配置与启用

特性以 Git Patch 交付，文件位于 `llm_rl/qwen3/patches/verl/0019-verl-feature-length_aware_resampler.patch`；在 `llm_rl/qwen3/` 目录下执行 `bash apply_all_patches.sh` 应用全部 patch。应用后通过 Hydra 配置启用 sampler：

```bash
data.sampler.class_path=pkg://verl.experimental.dataset.length_bucket_sampler
data.sampler.class_name=LengthAwareEpochSampler
+data.sampler.bucket_size=1024
+data.sampler.ema_decay=0.7
+data.sampler.shuffle_batch_blocks=True
data.dataloader_num_workers=0
data.shuffle=False
```

建议保持训练 dataloader 的 `drop_last=True`，当前 qwen3 样例的训练 dataloader 默认即按该方式构建。配套最小可复现脚本 [`llm_rl/qwen3/internal/train_grpo_qwen3_resampler_example.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen3/internal/train_grpo_qwen3_resampler_example.sh) 用环境变量驱动同一组开关（与 [qwen3-rl](../../guides/recipes/qwen3_rl.md) 的 16 卡 GRPO 样例兼容）：

```bash
# Per-epoch auto regrouping by previous rollout response lengths.
export VLLM_EPOCH_LENGTH_REGROUP_ENABLE=1
export VLLM_EPOCH_LENGTH_REGROUP_BUCKET_SIZE=1024
export VLLM_EPOCH_LENGTH_REGROUP_EMA_DECAY=0.7
export VLLM_EPOCH_LENGTH_REGROUP_SHUFFLE_BLOCKS=1
# Rollout long-tail guard (default on)
export VLLM_ROLLOUT_EARLY_STOP_ENABLE=1
export VLLM_ROLLOUT_EARLY_STOP_FACTOR=2.0
export VLLM_ROLLOUT_EARLY_STOP_MIN_TOKENS=10000
# llm_rl/qwen3/internal/train_grpo_qwen3_resampler_example.sh
```

切回 eager baseline 且关闭 resampler 用 `export VLLM_EAGER_BASELINE_NO_RESAMPLE=1`（此时 sampler 置 null）。脚本默认开启 `LengthAwareEpochSampler` + rollout 长尾保护、保持 `data.dataloader_num_workers=0`、默认不保存 checkpoint（`SAVE_CKPT_ENABLE=1` 开启）。

> 注意：使用 curriculum sampler 时**务必设置 `data.dataloader_num_workers=0`**，避免 dataloader worker 持有过期 sampler 状态。

## 收益与适用场景

适用场景：prompt 长度相近但 response 长度差异很大的 RL 数据集；rollout 阶段存在明显长尾 batch、step 时间抖动大；关注 generation 吞吐稳定性、希望减少「极长样本拖慢整批」。在这类场景下通常能降低 generation batch 内长短样本混排程度、减少极端长尾 batch 出现频率、提升 rollout 吞吐稳定性并改善 step 时间分布。

收益与数据分布、`n`、`gen_batch_size`、`response_length` 等配置强相关。实测在 n=16, gen_batch_size=32, response_length=16384 场景下，qwen30b-a3b-moe 模型的 rollout 阶段吞吐量能够提升约 **20%**。

建议结合以下指标实际观测：`timing_s/generate_sequences`、`perf/throughput`（或 rollout 吞吐相关指标）、`rollout/response_max_tokens_cap`。若数据集 response 长度分布本身较为集中，该特性收益可能有限。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/features/length_aware_resampler.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/features/length_aware_resampler.md)（§1 response 长尾两大问题；§2.1 patch 位置 / `apply_all_patches.sh`；§2.2 Hydra 配置 `LengthAwareEpochSampler` + bucket_size/ema_decay/shuffle_batch_blocks；§2.3 长尾保护 cap 公式 + 三个 `VLLM_ROLLOUT_EARLY_STOP_*` 环境变量；§3.1 EMA 长度估计 4 步；§3.2 `dataset_item_idx` 稳定回写；§3.3 按 `gen_batch_size` 整数倍截断；§3.4 rollout 动态下发 `response_max_tokens_cap`；§4 n=16/gen_batch_size=32/response_length=16384 下 rollout +20%；§5 注意事项）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/qwen3/internal/train_grpo_qwen3_resampler_example.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen3/internal/train_grpo_qwen3_resampler_example.sh)（16 卡 GRPO 最小可复现脚本：`VLLM_EPOCH_LENGTH_REGROUP_*` / `VLLM_ROLLOUT_EARLY_STOP_*` / `VLLM_EAGER_BASELINE_NO_RESAMPLE` 环境变量驱动 sampler 开关；`SAMPLER_CLASS_PATH=pkg://verl.experimental.dataset.length_bucket_sampler`）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/qwen3/patches/verl/0019-verl-feature-length_aware_resampler.patch`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen3/patches/verl/0019-verl-feature-length_aware_resampler.patch)（特性以 Git Patch 形式交付到 veRL）
- 图源：[`docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md) 的 response 长度分布图与长尾木桶效应图（qwen3-235B 2K 推 32K 实践）
- [verl](https://github.com/volcengine/verl) — veRL 上游代码仓（`LengthAwareEpochSampler` 落于 `verl.experimental.dataset.length_bucket_sampler`）

## Links

- [verl](../frameworks/verl.md)（本技术挂载的框架：RL 数据采样路径 + RLHFDataset，sampler 即 veRL 的可插拔入口）
- [rollout-rebalance](rollout_rebalance.md)（互补技术：vLLM 推理引擎内动态感知并迁移任务，事中缓解同一 rollout 长尾木桶效应；本技术在采样侧事前重排）
- [qwen3-rl](../../guides/recipes/qwen3_rl.md)（承载实践：Qwen3 GRPO/DAPO RL，patch 体系与最小可复现脚本来源、20% rollout 吞吐收益数据点）
- [grpo-dapo](grpo_dapo.md)（本技术服务的 on-policy RL 算法，rollout 长尾问题在 GRPO/DAPO 同步采样下尤为突出）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — 长度感知重采样特性文档 + qwen3 RL recipe