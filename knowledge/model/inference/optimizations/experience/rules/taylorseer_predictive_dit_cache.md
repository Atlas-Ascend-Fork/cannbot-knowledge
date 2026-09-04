---
type: Optimization
title: DiT 跳步缓存想更激进跳步且精度损失更小 — TaylorSeer 预测式缓存（记特征导数泰勒外推，代价：全阶导数显存需 offload + 仅单卡）
description: DiT 跳步缓存想更激进跳步且精度损失更小 — TaylorSeer 预测式缓存（记特征导数泰勒外推，代价：全阶导数显存需 offload + 仅单卡）。单机单卡 dit 视频生成去噪循环，已在用残差复用型跳步缓存（FBCache / TeaCache），但跳步一多精度就明显下滑，想用更小的精度损失换更激进的跳步。此时考虑 TaylorSeer——它与 FBCache/TeaCache 是同一 dit-cache 公共缓存框架下的另一种键控/复用方法。残差复用型的键控与阈值权衡见 dit-step-cache-fbcache-teacache；CFG 串行双分支下的缓存分槽见 dit-step-cache-cfg-branch-slotting。
tags:
- task.optimization
- topic.kv_cache
- topic.diffusion
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/266
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# DiT 跳步缓存想更激进跳步且精度损失更小 — TaylorSeer 预测式缓存（记特征导数泰勒外推，代价：全阶导数显存需 offload + 仅单卡）

## 适用场景

单机单卡 [dit](../../../concepts/modules/dit.md) 视频生成去噪循环，**已在用残差复用型跳步缓存（FBCache / TeaCache），但跳步一多精度就明显下滑，想用更小的精度损失换更激进的跳步**。此时考虑 **TaylorSeer**——它与 FBCache/TeaCache 是同一 [dit-cache](../../../concepts/techniques/dit_cache.md) 公共缓存框架下的另一种键控/复用方法。残差复用型的键控与阈值权衡见 [dit-step-cache-fbcache-teacache](dit_step_cache_fbcache_teacache.md)；CFG 串行双分支下的缓存分槽见 [dit-step-cache-cfg-branch-slotting](dit_step_cache_cfg_branch_slotting.md)。

## 规则：预测优于复用

- **FBCache / TeaCache = 复用**：直接把历史时间步的特征差值当作下一步差值复用，跳步越多误差累积越大。
- **TaylorSeer = 预测**：在实算步用 `derivative_approximation` 记录特征的各阶导数，跳步时用泰勒展开 `Σ (1/i!)·factorᵢ·xⁱ`（`taylor_formula`）从记录的导数**预测**该 step 的特征，`_get_step_type` 判当前是实算步还是预测步。预测比复用精度损失更小，因而能支持"算 1 步跳 2 / 算 1 步跳 4"的更激进跳步（"算 1 跳 2/4""精度损失更小"为优化文档定性披露，非定量事实）。

**旋钮按原则调、不抄配置**：跳步强度由"两实算步之间用预测跳过的步数"控制（越大越激进、精度风险越高）；预测精度由泰勒阶数控制（阶数越高越准、显存/内存开销越大）；另有 warmup（前几步只实算不预测）与 cutoff（后几步只实算不预测）保护首尾关键步。

## 选它前必须确认的两条硬约束

### 1. 仅单机单卡 —— 与多卡序列并行互斥

TaylorSeer / 当前所有 DiT-Cache 与多卡互斥：`WORLD_SIZE > 1` 且启用非 NoCache 缓存会**直接抛异常**（`sample_video.py:main` 硬 raise）。要多卡就别指望 DiT-Cache，改走序列并行 / VAE 并行那条路（[ulysses](../../../concepts/parallelism/ulysses.md) 等，长序列视频 DiT 序列并行见 [video-dit-ulysses-sequence-parallel](video_dit_ulysses_sequence_parallel.md)）。

### 2. 显存必配 offload —— 缓存全 block 全阶导数

TaylorSeer 缓存全 block 全阶导数，额外内存是 step-level 残差缓存的数万倍量级（参考实现同规格下：FBCache 仅缓存 14.5MB 特征，TaylorSeer 需 (n+1)×81.4GB 导数，n 为泰勒阶数）——**不开 offload 几乎必 OOM**；开了 offload 又把瓶颈转到主机内存（offload 机制见 [kvcache-offload](../../../concepts/techniques/kvcache_offload.md)）。选 TaylorSeer 前先确认主机内存能承受该 offload 门槛。

## 何时不适用

- 多卡推理（与 DiT-Cache 互斥）——回到序列并行 / VAE 并行。
- 显存紧且无法承受 offload 的主机内存门槛时——退回 step-level FBCache / TeaCache 或 NoCache。

## 风险 / 参考实现边界

- 收益是"更小精度损失下更激进跳步"，但源的 PR 性能表未给 TaylorSeer 的定量 speedup / 精度行，"算 1 跳 2/4"为 doc 定性披露，不并入定量事实面。
- 上述阶数/warmup/cutoff/offload 门槛为参考实现（cann-recipes-infer 复用 dit_cache 框架的 [hunyuan-video](../../../concepts/models/hunyuan_video.md) 等模型）当前形态；可迁移的是"预测式缓存优于残差复用、代价是全阶导数显存"这一判断，具体旋钮按模型标定。

## Evidence

- **diff 事实**（clone `@366a74296cb5`）：`module/dit_cache/cache_method.py` 的 `TaylorSeer`（`derivative_approximation` 记导数 / `taylor_formula` 泰勒展开 / `_get_step_type` 判实算 vs 预测步）、`BaseCache.taylor_formula`、`sample_video.py:main` 的 `WORLD_SIZE > 1` + 非 NoCache 互斥 raise，逐项对上。
- **doc 披露**（clone `@366a74296cb5`）："算 1 跳 2/4""精度损失更小"为优化文档定性描述，PR diff 性能表未给 TaylorSeer speedup/精度行——未并入定量事实面。归因主语为 cann-recipes-infer 该集成，非上游模型厂商。
- 溯源下探：[cann-recipes-infer-pr-266-feat-hunyuanvideo-support-taylorseer-offload-prefetch-vae-parallel-rolli](https://gitcode.com/cann/cann-recipes-infer/merge_requests/266)

<!-- cannbot:related:start -->
## 相关

- [DiT Cache (FBCache / TeaCache / TaylorSeer)](../../../concepts/techniques/dit_cache.md)（`related`）：TaylorSeer 机制以“预测时 `taylor_formula` 按泰勒级数 `output += (1/i!) · 导数因子 · x^i`”定义 TaylorSeer，预测式缓存选型进一步说明“预测比复用精度损失更小，因而能支持"算 1 步跳 2 / 算 1 步跳 4"的更激进跳步”；两者形成机制定义到选型与旋钮边界的直接链路。
- [DiT 步间缓存与多卡序列并行共存（数据相关判据须跨卡取一致决策，样例默认互斥）](dit_cache_with_sequence_parallel.md)（`related`）：TaylorSeer 固定 step 计划天然跨卡一致，但当前样例仍将所有 DiT-Cache 与多卡互斥；使用时需区分实现限制与判据机制是否需要同步。
- [DiT 采样步残差缓存（FBCache / TeaCache）键控、阈值权衡与 TeaCache 属性名 bug](dit_step_cache_fbcache_teacache.md)（`related`）：FBCache / TeaCache 的键控与阈值决定残差复用的跳步行为；当跳步增多导致精度明显下降时，可评估 TaylorSeer 预测式缓存，并核对其额外存储与部署边界。
- [视频 DiT TaylorSeer 特征缓存 NPU OOM：offload 到 Host + 预取搬算并行；Host 内存成新瓶颈](../../../guides/experience/interventions/video_dit_taylorseer_cache_offload.md)（`related`）：“`offload: true` 开启后走 offload 分支，把导数缓存从 NPU 搬到 CPU、并用独立流预取回来与计算并行”给出搬算实现；“**不开 offload 几乎必 OOM**”给出 TaylorSeer 的容量决策门槛，二者直接连接是否启用与如何实现。
<!-- cannbot:related:end -->
