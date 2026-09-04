---
type: Optimization
title: DiT 步间缓存与多卡序列并行共存（数据相关判据须跨卡取一致决策，样例默认互斥）
description: DiT 步间缓存与多卡序列并行共存（数据相关判据须跨卡取一致决策，样例默认互斥）。视频/图像生成 DiT 想在多卡序列并行（Ulysses / Ring）下再叠加 DiT 步间缓存（FBCache / TeaCache / TaylorSeer 跳 DiT step 提速）。缓存单卡使能与阈值权衡见 dit-step-cache-fbcache-teacache。多卡下二者能否共存取决于缓存类型，且不少样例把它写成了默认互斥。
tags:
- task.optimization
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/340
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/221
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/240
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/29
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# DiT 步间缓存与多卡序列并行共存（数据相关判据须跨卡取一致决策，样例默认互斥）

## 适用场景

视频/图像生成 [DiT](../../../concepts/modules/dit.md) 想在多卡序列并行（[Ulysses](../../../concepts/parallelism/ulysses.md) / [Ring](../../../concepts/parallelism/ring_attention.md)）下再叠加 [DiT 步间缓存](../../../concepts/techniques/dit_cache.md)（FBCache / TeaCache / TaylorSeer 跳 DiT step 提速）。缓存单卡使能与阈值权衡见 [dit-step-cache-fbcache-teacache](dit_step_cache_fbcache_teacache.md)。多卡下二者能否共存取决于缓存类型，且不少样例把它写成了默认互斥。

## 核心规则：数据相关判据须跨 SP 组取一致决策

复用判据分两类：

- **数据相关（FBCache / TeaCache）**：跳 step 的判据是逐 step 算出的**本地统计标量**（FBCache 的 `diff_ratio = mean_diff/(mean_current+1e-8)`、TeaCache 的 `rel_l1 = abs_diff.mean()/(prev_input.abs().mean()+1e-8)` 比阈值）。序列并行下每卡只持序列分片、本地统计不同 → 各卡可能得到**不同**的 skip/compute 决策 → DiT 前向路径在卡间分叉 → SP 的集合通信/注意力对不齐 → **挂死或结果错乱**。
- **固定 step 计划（TaylorSeer）**：各卡决策本已一致，**无需**同步。

**手段**：数据相关缓存要与 SP 共存，各卡本地算出判据标量后，在 SP 通信组上 `all_reduce(SUM)` 再除以 `sp_world_size` 得平均值，用该平均标量比阈值——各卡拿到相同标量 → 相同决策，前向不再分叉。配套两点：
1. 同步组取 `ulysses_group`（同时覆盖"纯 Ulysses"与"Ulysses + Ring 混合"）；缓存管理器在建 cache_method 前后各透传一次 `sp_group/world_size/rank`，注册顺序无关。
2. **缓存未命中的重算路径也要走 SP 注意力**：cache-miss 时的 attention 不能退回本地 flash attention，混合 SP 场景须改走 SP 版 `parallel_attention`（传 `cu_seqlens_q/kv`），否则重算路径与 SP 布局不一致、同样对不齐。

## 反例 / 边界：很多样例默认把 DiT-Cache 与多卡写成硬互斥

在打通前（或未做上述同步的样例里），DiT-Cache 与多卡（`world_size > 1`）被设成互斥，且**两种失败形态都要认得**：

- **静默降级**（[Wan2.2-I2V](../../../concepts/models/wan2_2_i2v.md) `generate.py`）：`world_size > 1` 时把 `cache_step` 覆盖成 `NoCache`，仅一条 INFO 日志"Cannot enable both Multi-NPU and DIT-Cache. DIT-Cache has been disabled"——缓存**不生效、拿不到跳步加速**，易被忽略。
- **硬失败**（[HunyuanVideo](../../../concepts/models/hunyuan_video.md) `sample_video.py`）：`world_size > 1` 且 cache 非 NoCache 时**直接 `raise Exception("Cannot enable both Multi-NPU and DIT-Cache")`**，启动即中止。
- **RFC 显式放弃**：HunyuanVideo 早期 RFC 把"TeaCache + 序列并行"条目划掉，注"为避免与其他并行方案冲突，暂时放弃"；TeaCache 是对**整段 DiT forward 输出残差**的复用，与逐卡序列切分/集合通信每步同步不相容（此机理为推断，源未展开）。

结论：不要在多卡下盲目期望 DiT-Cache 生效——遇到 INFO 静默 NoCache 或 `raise Exception` 要知道这是成文约束；要用数据相关缓存 + SP 就得走上面的判据标量同步路径，或单卡跑缓存。

## 相关经验

- 另见 [CFG 类生成模型用与 TP 正交的样本级并行摊平每步两次前向](../../../guides/experience/interventions/cfg_parallel_sample_level_diffusion.md)。


## Evidence

- `diff 事实`（@1e9d6f9290d6，共存手段）：`BaseCache._sync_scalar_for_sp`（`all_reduce(SUM)/sp_world_size`）、FBCache/TeaCache 比阈值前调用它、`set_sp_group` 用 `ulysses_group`、cache_block full-compute 走 `parallel_attention`；TaylorSeer 未调用同步。溯源下探：[cann-recipes-infer-pr-340-feat-hunyuanvideo-support-dit-cache-in-sequence-parallel-scenario](https://gitcode.com/cann/cann-recipes-infer/merge_requests/340)
- `diff 事实`（@e3954a04，Wan2.2 静默 NoCache）：`generate.py` 的 `world_size>1 ... -> NoCache` 守卫。溯源下探：[cann-recipes-infer-pr-221-feat-wan2-2-fb-cache](https://gitcode.com/cann/cann-recipes-infer/merge_requests/221)
- `diff 事实`（@79de4ef9，HunyuanVideo 硬失败）：`sample_video.py` 的 `world_size>1 ... -> raise Exception`；Wan2.2 守卫简化为纯 `if world_size>1`。溯源下探：[cann-recipes-infer-pr-240-feat-hunyuanvideo-wan2-2-step-level-cache-cfg](https://gitcode.com/cann/cann-recipes-infer/merge_requests/240)
- `diff 事实` + `RFC 披露`（@5d15b2598ffa）：README「TeaCache 单机单卡」+ `models.py` 整段 forward 残差缓存；"放弃 Cache+并行"取自 RFC，冲突机理为推断。溯源下探：[cann-recipes-infer-issue-29-rfc-hunyuanvideo-model-inference-support](https://gitcode.com/cann/cann-recipes-infer/issues/29)

<!-- cannbot:related:start -->
## 相关

- [CFG 类生成模型用与 TP 正交的样本级并行摊平每步两次前向](../../../guides/experience/interventions/cfg_parallel_sample_level_diffusion.md)（`related`）：CFG 只是"同一网络吃两份无依赖的输入"，因此可分到两组设备并行，且这条轴与 ［TP］(../../../concepts/parallelism/tensor_parallel.md) 正交：；数据相关缓存要与 SP 共存，各卡本地算出判据标量后，在 SP 通信组上 `all_reduce(SUM)` 再除以 `sp_world_size` 得平均值，用该平均标量比阈值——各卡拿到相同标量 → 相同决策，前向不再分叉。。前者建立 CFG 与 TP/SP 可正交组合的拓扑，后者给出其中数据相关缓存判据在 SP 组内保持一致的同步约束，二者共同决定 CFG+SP 推理链的正确执行。
- [DiT Cache (FBCache / TeaCache / TaylorSeer)](../../../concepts/techniques/dit_cache.md)（`related`）：SP 缓存同步要求指出“多卡 SP 下，各 rank 的 l1 loss 差异会导致跳步判断不同步；需要一次 all_reduce 取均值”，运行时同步规则将其细化为“数据相关缓存要与 SP 共存，各卡本地算出判据标量后，在 SP 通信组上 `all_reduce(SUM)`”；后者补齐通信组、cache-miss 路径和失败形态。
- [DiT 跳步缓存想更激进跳步且精度损失更小 — TaylorSeer 预测式缓存（记特征导数泰勒外推，代价：全阶导数显存需 offload + 仅单卡）](taylorseer_predictive_dit_cache.md)（`related`）：TaylorSeer 固定 step 计划天然跨卡一致，但当前样例仍将所有 DiT-Cache 与多卡互斥；使用时需区分实现限制与判据机制是否需要同步。
- [DiT 采样步残差缓存（FBCache / TeaCache）键控、阈值权衡与 TeaCache 属性名 bug](dit_step_cache_fbcache_teacache.md)（`related`）：“**数据相关（FBCache / TeaCache）**：跳 step 的判据是逐 step 算出的**本地统计标量**”说明多卡接入前提；“第二个去噪 step 起**才走到读 `rel_l1_thresh_teacache` 的分支”指出 TeaCache 单卡实现先要修复的确定性故障。
<!-- cannbot:related:end -->
