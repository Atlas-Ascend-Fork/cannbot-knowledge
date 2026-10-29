---
type: Optimization
title: HunyuanVideo A3 TaylorSeer offload 案例：导数缓存与搬算流水
description: 记录 720p 129 帧的主机内存门槛、预取流水及来源自报观测；区分 PR266 的单卡限制与 PR356 新增的 SP8 配置。
tags:
- task.debugging
- topic.diffusion
- topic.memory
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/266
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/170
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/356
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/366a74296cb54c7f62ecf6565d7f3c91a02bdc5c/models/hunyuan-video/sample_video.py
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/d7174ec0ba19ead0e0be93c44f0e17200e4c0081/models/hunyuan-video/config/sp8_taylorseer.yaml
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-23T09:41:54Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - dit
---

# HunyuanVideo A3 TaylorSeer offload 案例：导数缓存与搬算流水

## 适用场景

视频生成 [dit](../../concepts/modules/dit.md) 用 TaylorSeer（多阶泰勒预测跳步）做 [dit-cache](../../concepts/techniques/dit_cache.md) 加速时，为跳步而缓存所有 block 的所有阶导数，额外内存是 step-level 缓存方法（FBCache / TeaCache）的数万倍。大尺寸 / 长帧规格下这份缓存会把 NPU 内存吃满 OOM，并限制可生成的视频序列长度。TaylorSeer 与 FBCache / TeaCache 的缓存方法选型 / 键控见 [dit-step-cache-fbcache-teacache](../rules/dit_step_cache_fbcache_teacache.md)，本页只管 TaylorSeer 缓存的**显存 offload**。

## 问题信号（内存量级对比）

同为 HunyuanVideo 生成 720p / 129 帧：FBCache 仅缓存约 14.5MB 特征，而 TaylorSeer 需缓存 `(n+1)×81.4GB` 导数（n = 泰勒阶数）。不做 offload 几乎必 NPU OOM。

## 手段 · offload + 预取（搬算并行）

`offload: true` 开启后走 offload 分支，把导数缓存从 NPU 搬到 CPU、并用独立流预取回来与计算并行（[multi-stream](../../concepts/techniques/multi_stream.md)）：

- **计算阶段 NPU→CPU offload**：先在当前流算好各阶导数，再用独立 `copy_stream` 把导数逐项 `.to('cpu', non_blocking=True)`，缓存驻留 CPU。
- **预测阶段 CPU→NPU 预取 + 搬算并行**：用 `copy_stream` 预取、`cal_stream` 计算、`copy_events` / `cal_events` 做流水依赖——在 NPU 计算当前阶导数的同时提前把下一阶导数搬回 NPU，掩盖搬运时间。

效果（doc 披露 profiling、仓自报无独立复测）：用预取后实际计算阶段的 Free 占比（含搬运 + CPU 下发）从 41.7% 降到 11.1%、泰勒预测阶段从 83.81% 降到 31.5%。

## 前置条件 / 何时不适用（Host 内存成新瓶颈）

- offload 把 `(n+1)×81.4GB` 导数搬到 CPU，**主机内存成为新瓶颈**：`720*1280*129` 规格下开启需保证 **≥400GB CPU 内存**（单卡与 8 卡 SP 变体均标注此门槛）。主机内存不足 400GB 时该组合在主机侧撑不住。
- offload 默认 `True`；大样例建议使能规避 TaylorSeer 额外缓存导致的 OOM。
- 来源报告的内存管理取舍：开 DiT-Cache 后若剩余可用内存过低（如不足 100MB），开虚拟内存（`PYTORCH_NPU_ALLOC_CONF=expandable_segments:True`）可能严重掉性能，此时应删掉该环境变量改开 `--cpu-offload`——这是该模型配置的性能建议，不证明两者在所有环境中功能互斥；应分别测量后选择。

## 风险 / rollback

- 风险：offload 依赖大主机内存（≥400GB @ 720p 129 帧）；关掉 offload 则 NPU 需容纳 `(n+1)×81.4GB` 导数、几乎必 OOM。
- rollback：`TaylorSeer.offload` 设 `false` 回到全驻 NPU（仅显存足够的小规格可行），或换回 step-level FBCache / TeaCache / NoCache。

## 参考实现及其约束

参考 cann-recipes-infer 的 HunyuanVideo（`module/dit_cache/cache_method.py` 的 `_offload_derivative_approximation` / `_offload_taylor_formula` / `streams_init` / `events_init`，`sp8_taylorseer.yaml` 的 `offload` 注释，设计文档 `mm_inference_design.md`），Atlas A3。81.4GB / 14.5MB / Free 占比 / 400GB 门槛均为仓自报 doc 披露、无独立复测，限该模型 + 该规格 + offload 开启，不外推其它规格。

## Evidence

- `diff 事实`（@366a74296cb5）：`_offload_derivative_approximation`（copy_stream 搬 NPU→CPU）、`_offload_taylor_formula`（copy/cal stream + copy_events/cal_events 预取流水）、`streams_init` / `events_init` 为新增 diff，`if self.offload:` 分派对上。
- `doc 披露`（@366a74296cb5 / @d7174ec0ba19 / README）：`(n+1)×81.4GB` / 14.5MB、Free 占比 41.7%→11.1% 与 83.81%→31.5%、400GB 门槛为仓自报；README offload 参数由「减少对内存的占用」改为「对 npu 内存」、「400GB 以上的内存」改为「400GB 以上的 CPU 内存」（offload 方向 NPU→CPU 为 diff 事实 + 维护者确认）。
- 溯源下探：
  - [cann-recipes-infer-pr-266-feat-hunyuanvideo-support-taylorseer-offload-prefetch-vae-parallel-rolli](https://gitcode.com/cann/cann-recipes-infer/merge_requests/266)
  - [cann-recipes-infer-issue-170-bug-report-hunyuan-video-readme](https://gitcode.com/cann/cann-recipes-infer/issues/170)
  - [cann-recipes-infer-pr-356-refactor-unified-inference-script-for-multimodal-models](https://gitcode.com/cann/cann-recipes-infer/merge_requests/356)

## 版本与规则入口

缓存方法选择、内存预算与回退统一见 [TaylorSeer 规则](../rules/taylorseer_predictive_dit_cache.md)。PR266 的 `sample_video.py` 会拒绝多卡与缓存同开；PR356 固定提交移除了这一检查，并提供 `sp8_taylorseer.yaml`（world_size=8、ulysses-degree=8、ring-degree=1、offload=true）。后者证明存在该集成入口，不等于多卡质量和性能已由本仓验证。

本案例的验收应覆盖生成质量、Host/NPU 峰值内存和搬算流水；主机容量不足时缩小规格或回退 NoCache，不能只关闭 offload 就认定能够运行。
