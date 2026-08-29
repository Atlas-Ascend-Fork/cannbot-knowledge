---
type: Guide
title: 多机/多进程 DP+EP MoE 推理的集合通信一致性对齐（phase 对齐 + 变长换定长）
description: 多机/多进程 DP+EP MoE 推理的集合通信一致性对齐（phase 对齐 + 变长换定长）。MoE 模型多机 / 多进程 DP + EP 推理里，单进程组内多个 DP rank 各自持请求、又要在 MoE 层做跨 rank 集合通信。凡相互做 MoE 集合通信的 DP 进程，必须在同一状态下发起集合通信；一旦各进程按各自本地请求独立推进，请求数/token 数不整除进程数时进程会错开 → 集合通信不一致（对不齐 / 挂起）。有两处对齐要做。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/92
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# 多机/多进程 DP+EP MoE 推理的集合通信一致性对齐（phase 对齐 + 变长换定长）

## 适用场景

MoE 模型多机 / 多进程 [DP](../../../concepts/parallelism/data_parallel.md) + [EP](../../../concepts/parallelism/expert_parallel.md) 推理里，单进程组内多个 DP rank 各自持请求、又要在 MoE 层做跨 rank 集合通信。**凡相互做 MoE 集合通信的 DP 进程，必须在同一状态下发起集合通信**；一旦各进程按各自本地请求独立推进，请求数/token 数不整除进程数时进程会错开 → 集合通信不一致（对不齐 / 挂起）。有两处对齐要做。

## 对齐一：跨 DP 进程对齐 prefill/decode 阶段（phase 一致）

失败模式：单 API server + 多进程 DP 下，做 MoE 集合通信的进程必须同处 prefill 或 decode；各进程按本地请求独立推进会错开阶段。

手段（PD 混合单 API server 调度，[PD](../../../concepts/frameworks/online_pd_inference.md)）：
1. **单 server 多进程分发**：用 DP 感知引擎客户端（`DPAsyncMPClient`）替代 manual scaleout 的 `AsyncMPClient`，在引擎内统一控制多进程，不再依赖引擎外 Nginx 路由。
2. **全局 phase 协调**：每轮 busy loop 先经 **DP all-reduce 求全局 phase hint**——只要任一 DP rank 本地有 prefill 请求，全局判为 `prefill`（prefill 优先），否则 `decode`；取不到本地状态时 fallback `decode`。
3. **空闲进程 dummy 参与集合通信**：全局 phase 为 prefill 但本进程无真实 prefill 请求时，跑一次**对齐 shape 的 dummy prefill 前向**（按 pad size 补到 fake_len、零 `input_ids`、attn 置 `PrefillNoCache`），让无请求的进程仍以一致 shape 参与该阶段集合通信；decode 同理。
4. **prefill/decode 分离调度**：有等待中的 prefill 时优先只调度 prefill、跳过调度 running(decode)，避免混调造成阶段冲突。
5. lm_head/embedding 通信随之切换（PD 混合下关闭 parallel lmhead，embedding 走 TP all-gather）。

调用约定：总开关默认关 → 回退原 PD 分离、无行为变化，可安全灰度；PD 分离调度与 chunked-prefill **互斥**（代码 `assert` 强制）。

## 对齐二：多机 DP 变长集合通信不支持，须先对齐长度再走定长

失败模式：MoE prefill 各 DP rank token 数不一致时，变长集合通信算子 `all_gather_v` / `reduce_scatter_v`（先 all_gather 各 rank `n_tokens` 再按变长收集/散射）**在多机场景不支持**，沿用则多机 DP 直接跑不起来。

手段：
1. **对齐 + pad**：prefill 分支用 `all_reduce(local_length, op=MAX)` 求全局最大 token 长度，`F.pad` 把本 rank hidden 补到该长度，各 rank 定长一致。
2. **定长 two-stage all_gather** 取代变长 gather：对 hidden 与 router_logits 走定长两阶段 all_gather，删除"先 all_gather `n_tokens` → 建空 tensor → `all_gather_v` → cat"的变长链路。
3. **reduce 路径统一**：prefill/decode 都走定长 `reduce_scatter`，删除 prefill 专用变长 `reduce_scatter_v`。
4. 配套把切分长度常量下调（`SEQ_SPLIT_LENGTH` 4096→256）以适配 pad 后分块前向。

## 适用边界

证据覆盖单 API server 多进程 DP+EP MoE 推理（vLLM v0.9.0 + OmniInfer v0.5.0，昇腾 A2 四机 32 卡 910B，跑通 [DeepSeek-R1](../../../concepts/models/deepseek_r1.md) W8A8 与 [Qwen3-MoE](../../../concepts/models/qwen3_moe.md)）。作者自评：该规模 PD 混合优于 PD 分离。correctness 仅功能性验证（`curl /v1/completions`），无精度/性能数值。同框架下 DeepSeek-R1 与 Qwen3-MoE 图编译 level 不同（1 vs 0），换模型须按模型调。两条"全局 phase 协调 + dummy 参与"与"变长换定长 + MAX 对齐"原则对同类多进程/多机 DP MoE 部署可迁移。多机大 EP 的 HCCL buffer 不足另见 [hccl-buffsize-too-small](../../../runbooks/runtime/hccl_buffsize_too_small.md)。

## Evidence

- `diff 事实`（@2c45117，`contrib/vllm-pd-hybrid-dp-ep/omni_v0.5.0.patch`）：phase-hint all-reduce / dummy-batch / 分离调度 / chunk-prefill 互斥断言、`qwen3_moe` 的变长 `all_gather_v` 换 `all_reduce(MAX)` pad + two-stage all_gather 均落在合并 diff。"变长算子不支持多机"为该 patch 作者动机说明。
- 溯源下探：[cann-recipes-infer-pr-92-support-pd-hybrid-dp-ep-on-4-a2-machines-for-vllm](https://gitcode.com/cann/cann-recipes-infer/merge_requests/92)

<!-- cannbot:related:start -->
## 相关

- [多机集合通信 HCCL_BUFFSIZE too SMALL —— 调大且各 rank 一致](../../../runbooks/runtime/hccl_buffsize_too_small.md)（`related`）：多机大 EP 的 HCCL buffer 不足另见 ［hccl-buffsize-too-small］(../../../runbooks/runtime/hccl_buffsize_too_small.md)。；多机多卡集合通信（大 ［EP］(../../concepts/parallelism/expert_parallel.md) dispatch/combine、CP 等、长序列）所需 HCCL buffer 超过默认 `HCCL_BUFFSIZE`。。部署指南把多机大 EP 的通信缓冲不足明确分流到该运行手册，后者给出容量诊断与各 rank 一致配置步骤。
- [集合通信参与方逐 rank 对齐：按本地状态决定「是否进入集合通信」导致发散型挂死/超时](../../../runbooks/runtime/collective_participation_per_rank_consistency.md)（`related`）：**凡相互做 MoE 集合通信的 DP 进程，必须在同一状态下发起集合通信**；同一进程组里做**同一次**集合通信的各 rank，参与方必须**逐 rank 完全一致**。干预指南用全局 phase、dummy 参与和定长通信落实运行手册的逐 rank 到达一致性约束。
<!-- cannbot:related:end -->
