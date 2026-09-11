---
type: Optimization
title: DiT 采样步残差缓存（FBCache / TeaCache）键控、阈值权衡与 TeaCache 属性名 bug
description: DiT 采样步残差缓存（FBCache / TeaCache）键控、阈值权衡与 TeaCache 属性名 bug。dit / 扩散式生成模型（如 hunyuan-video 文生视频，生成 5s 720p / 129 帧、3D full attention 序列长约 119k、attention 占端到端 81% / DiT 占 95%）在 Atlas A2 上的推理加速：DiT 采样步间存在时序冗余（相邻去噪 step 输出高度相关）。用 step-level 残差缓存跳过整段 DiT block 前向可得约 2x DiT 加速。缓存机制的 canonical 说明见 dit-cache，本页给运行时的键控选择与阈值权衡。
tags:
- task.optimization
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/229
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# DiT 采样步残差缓存（FBCache / TeaCache）键控、阈值权衡与 TeaCache 属性名 bug

## 条件 → 优先尝试

[dit](../../../concepts/modules/dit.md) / 扩散式生成模型（如 [hunyuan-video](../../../concepts/models/hunyuan_video.md) 文生视频，生成 5s 720p / 129 帧、3D full attention 序列长约 119k、attention 占端到端 81% / DiT 占 95%）在 Atlas A2 上的推理加速：DiT 采样步间存在**时序冗余**（相邻去噪 step 输出高度相关）。用 **step-level 残差缓存**跳过整段 DiT block 前向可得约 **2x** DiT 加速。缓存机制的 canonical 说明见 [dit-cache](../../../concepts/techniques/dit_cache.md)，本页给运行时的键控选择与阈值权衡。

## 两种可复用键控（同一 DiT 上二选一）

复用时 `reuse_cache()` 返回 `previous_residual + ori_latent`，`post_cache_update` 以 `latent - ori_latent` 更新残差。差别在「何时判定可复用」：

- **FBCache** — 键控**第一个 DiT block 的输出**：算完第一个 block 后取其相对上次的均值 L1 相对差 `diff_ratio = mean|cur-prev| / (mean|cur| + 1e-8)`，`diff_ratio < 阈值` 即判可复用（默认阈值 0.05）。
- **TeaCache** — 键控**第一个 img modulated 输入**：对 modulated 输入的相对 L1 经多项式 `np.poly1d(coefficients)` 放缩后**累加**，`accumulated_rel_l1 < 阈值` 即跳过并继续累加、否则清零（默认阈值 0.1；`coefficients` 为模型相关拟合系数）。

**阈值语义**：越大越激进（跳更多 step）、精度损失越大——是性能/精度权衡旋钮，**非越大越好**。默认 `NoCache` 不改数值行为，须显式选键控才生效。

## ⚠️ 已知失败：合并版 TeaCache 阈值属性名 bug（第二步起崩）

本 PR 合并进库的公共模块 `module/dit_cache_step/cache_step.py` 中 **TeaCache 不可用**：
- `TeaCache.__init__` 把阈值存进 `self.rel_l1_thresh_fbcache`（从 FBCache 复制而来），
- 而 `TeaCache.should_cache` 读的是从未被赋值的 `self.rel_l1_thresh_teacache`（`TeaCache` / 基类 `StepCache` / 任何 `__getattr__` 均无定义）。

时序：`should_cache` 首次调用 `prev_judge_input is None` 先 `return False`，**第二个去噪 step 起**才走到读 `rel_l1_thresh_teacache` 的分支 → 运行时抛 `AttributeError: 'TeaCache' object has no attribute 'rel_l1_thresh_teacache'`（Python 属性解析静态确定的必然结果）。FBCache 两处均用 `self.rel_l1_thresh_fbcache`、一致，**不受影响**。

- **规避**：`cache_config.json` 设 `cache_forward: "FBCache"`（单卡实测 2.09x，可用）。
- **修复**：把 `TeaCache.__init__` 的 `self.rel_l1_thresh_fbcache = tea_cache_config['rel_l1_thresh']` 改成 `self.rel_l1_thresh_teacache = ...`，与 `should_cache` 读取名对齐。

因此当前**稳妥选择是 FBCache**；TeaCache 需先打上述补丁才可用。

## Outcome / Atlas A2 优化基准

`hunyuan_video_optimization.md` 优化总览表（Atlas A2，CANN `8.5.0.alpha002`；各行 DiT speedup 均相对同一单卡「开箱/只替换FIA接口」基线）：

| NPU数量 | 优化方案 | DiT time(s) | E2E time(s) | DiT speedup |
| --- | --- | :---: | :---: | :---: |
| 单卡 | 开箱（只替换FIA接口） | 3907.32 | 4081.82 | -（基线） |
| 单卡 | RMSNorm+Rotary 融合算子 | 3787.61 | 3953.28 | 1.03x |
| 单卡 | FBCache | 1869.50 | 2024.07 | 2.09x |
| 单卡 | TeaCache | 1645.26 | 1819.26 | 2.37x |
| 8卡 | [Ulysses](../../../concepts/parallelism/ulysses.md) 序列并行 | 480.20 | 698.97 | 8.13x |
| 8卡 | [Ring Attention](../../../concepts/parallelism/ring_attention.md) 序列并行 | 706.07 | 866.60 | 5.53x |

- 这些是**并列备选**（单卡 FBCache / TeaCache 二选一；8 卡 Ulysses / Ring Attention 二选一），**非逐行累乘**，也不外推「越多越快」。报告点中 8 卡 Ulysses（8.13x）优于 Ring Attention（5.53x），仅单点对比。长序列视频 DiT 的序列并行做法见 [video-dit-ulysses-sequence-parallel](video_dit_ulysses_sequence_parallel.md)。
- ⚠️ **TeaCache 2.37x 无法直接复现**：该数应采自本 PR **删除的**旧独立实现 `models/HunyuanVideo/hyvideo/cache/teacache.py`；合并进库的公共模块 TeaCache 有上述属性名 bug，未打补丁时选 TeaCache 会崩。FBCache 2.09x 不受影响。

## 适用范围 / 风险

- 证据覆盖 DiT 视频生成（HunyuanVideo）；键控策略与阈值权衡对 DiT/扩散式生成的 step 缓存通用，具体 `coefficients` / 阈值需按模型标定。
- benchmark 为仓自报、无独立复测；数字口径部分缺失（无完整命令 / 逐样本 correctness）；TeaCache 阈值 doc 表注 0.15 与 `cache_config.json` 默认 0.1 不一致（benchmark 采集用 0.15）。

## Evidence

- **代码事实**（clone `@c3782f8bfb96`）：键控与阈值判据（`FBCache/TeaCache.should_cache`）、`reuse_cache()` 的 `previous_residual + ori_latent`、`post_cache_update` 残差更新出自公共模块 `module/dit_cache_step/cache_step.py`。
- **代码事实**（clone `@c3782f8bfb96`）：TeaCache bug — `TeaCache.__init__` 写 `_fbcache`、`should_cache` 读未定义的 `_teacache`（全文件 `rel_l1_thresh_teacache` 仅 `should_cache` 出现一次、无赋值）；`AttributeError` 为静态确定推断、未实机执行。
- **仓自报**（clone `@c3782f8bfb96`）：基准表出自 `hunyuan_video_optimization.md#优化总览` / `#优化背景`，无独立复测。
- 溯源下探：[cann-recipes-infer-pr-229-feat-hunyuanvideo-support-fbcache-npu-rmsnorm-add-dit-cache-step](https://gitcode.com/cann/cann-recipes-infer/merge_requests/229)