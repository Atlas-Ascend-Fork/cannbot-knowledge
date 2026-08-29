---
type: Optimization
title: 强制专家负载均衡（round-robin 覆盖 topk）测 MoE decode 性能上界：仅 profiling、不进精度路径，构造均衡 topk 要列优先
description: 强制专家负载均衡（round-robin 覆盖 topk）测 MoE decode 性能上界：仅 profiling、不进精度路径，构造均衡 topk 要列优先。想知道一个 MoE + EP 部署「在理想专家负载均衡下能跑多快」——即剥离真实路由不均引入的 EP 尾延迟后的纯模型时延上界；或读到一份 benchmark 标了 perfect_eplb/--perfect-eplb/force_eplb 想知道它测的是什么口径时。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/243
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/326
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/205
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 强制专家负载均衡（round-robin 覆盖 topk）测 MoE decode 性能上界：仅 profiling、不进精度路径，构造均衡 topk 要列优先

## 适用场景

想知道一个 MoE + [EP](../../../concepts/parallelism/expert_parallel.md) 部署「在理想专家负载均衡下能跑多快」——即剥离真实路由不均引入的 EP 尾延迟后的纯模型时延上界；或读到一份 benchmark 标了 `perfect_eplb`/`--perfect-eplb`/`force_eplb` 想知道它测的是什么口径时。

## 核心规则

用「强制专家负载均衡」测性能上界：框架用**确定性生成、按并行度均摊到各 EP rank 的 round-robin topk 列表**覆盖真实 gate 路由的 `topk_idx`，得到完美 EPLB 负载分布。开启后 prefill 每次、decode 仅首次生成并缓存 `cur_topk_list` 注入模型，MoE block forward 里 `if force_eplb: topk_idx = cur_topk_list`。

**关键边界（决定它的用途）**：round-robin 索引与真实路由无关 → 每 token 落到确定专家 → 负载完美均衡但**生成结果错误**。所以这是**测量理想负载均衡性能上界的工具开关，不是正确性路径**——不能用于精度业务生成。读该口径 benchmark 时须知它排除了路由不均因素、不代表真实业务时延。

- 前置：模型 `__init__` 须暴露 `num_experts` 与 `num_experts_per_tok`（否则生成合成 topk 时 `raise AttributeError`）。
- rollback：`force_eplb=False` / 不加 `--perfect-eplb`，走真实路由（正确性路径）。

## 构造均衡 topk 的坑：列优先 round-robin，别行优先

要让每个 EP rank 收到相等 token 数、别在 [MC2](../../../concepts/techniques/moe_dispatch_combine_v2.md) 分核发送的细粒度上把 token 聚簇到单卡，合成 topk 的**分配顺序**必须列优先（相邻 token 先在 rank 间轮转）。专家按 rank 连续切块（rank r 持 `[r*step_gap,(r+1)*step_gap)`、`step_gap=n_routed_experts//moe_ep_size`）时：

```python
col = idx % moe_ep_size            # 列 = 目标 EP rank（相邻 token 轮转到下一 rank）
row = idx // moe_ep_size % step_gap  # 行 = 该 rank 内局部专家序号
expert_idx = row + col * step_gap    # 全局 expert id = rank 块起点 + 局部序号
```

于是每个 EP rank 恰分到 `expanded_tokens / moe_ep_size` 个 token（完美均衡）。**行优先**连续编号（前 `step_gap` 个 token 全打 rank 0、下一批全打 rank 1）会破坏 mc2 per-rank 发送均衡、测不出理想均衡性能。要点：**mc2 per-rank 均衡由分配顺序决定，列优先能得均衡、行优先不能**——维护者审查确认过分配顺序须对齐 mc2 分核发送逻辑。

## 何时不适用 / 关联

- 只用于性能测评 / profiling，绝不进精度路径。为测 TPOT 常配的 `perfect_eplb: True` 会影响精度，落地精度评估须关闭。
- 规则适用面限本仓 MoE 建模的合成基准路径（`moe_tp_size>1` 与 prefill 分支不在列优先规则内）。
- 提供跨 MoE 模型可复用的「理想负载均衡性能上界」测量手段，参考实现覆盖 DeepSeek-V3.2-Exp（列优先修复）、Qwen3-MoE/DeepSeek-R1（框架 `force_eplb`）、Qwen3-MoE SGLang（`--perfect-eplb`）。

## 相关经验
- [profile_run 峰值显存低估致运行期 OOM：profiling 未实际走一遍所有影](../../../runbooks/performance/profile_run_peak_memory_underestimate_untraversed_path.md)

- 另见 [纯 EP MoE decode 中 GMM 无条件执行（0 token 也跑）：profiling 里某卡缺 GMM 不能用「该卡没分到 token」解释，用 expert_token_num 诊断](../../../runbooks/validations/moe_ep_gmm_unconditional_zero_token_diagnosis.md)。


## Evidence

- 列优先新公式 vs 行优先旧公式（专家按 rank 连续切块的 EP mc2 路径）：diff/代码事实 @af319f1125bd + 维护者确认（审查追问「跟 mc2 算子确认过分核发送逻辑了嘛」、作者答「已确保 mc2 正常」后合并）；每 rank 均摊为确定性数学推演。溯源下探 [cann-recipes-infer-pr-243-fix-perfect-eplb](https://gitcode.com/cann/cann-recipes-infer/merge_requests/243)。
- `force_eplb` round-robin 覆盖 `topk_idx`、prefill/decode 注入时机、暴露 `num_experts`/`num_experts_per_tok` 前置：diff 事实 @b7a110bd6812；「仅 profiling 非正确性路径」为覆盖机制直接推断。溯源下探 [cann-recipes-infer-pr-326-refactor-mtp-refactor-and-r1-adaptation-framework](https://gitcode.com/cann/cann-recipes-infer/merge_requests/326)。
- `--perfect-eplb` 入参 + `gen_cur_topk_idx` 覆盖 topk、README benchmark 在 forced eplb 下测：diff 事实 @50e41b5b8220。溯源下探 [cann-recipes-infer-pr-205-feat-support-qwen3-moe-sglang](https://gitcode.com/cann/cann-recipes-infer/merge_requests/205)。

<!-- cannbot:related:start -->
## 相关

- [MoE + 投机解码：draft dummy_run 误带 profile-run 语义触发强制随机专家路由，静默拉低 MTP accept rate](../../../runbooks/precision/mtp_draft_dummy_run_in_profile_run_random_experts.md)（`related`）：profiling 时要把 token 负载均摊到各 rank / 各专家、避免堆到单卡造成 OOM 或压不出真实峰值。；想知道一个 MoE + ［EP］(../../../concepts/parallelism/expert_parallel.md) 部署「在理想专家负载均衡下能跑多快」。运行手册限定真正 profile run 中随机专家负载均衡应保留，规则页说明 perfect EPLB 正是测量这种理想均衡上界的口径。
- [MoE 长序列 prefill 峰值显存 / OOM：专家负载不均 + dispatch 中间量放大；分块 / 均衡 / double-routing 处置](../../../runbooks/performance/moe_prefill_oom_peak_memory.md)（`related`）：**专家负载不均 → 个别卡的 grouped_matmul 峰值内存爆**。；用「强制专家负载均衡」测性能上界：框架用**确定性生成、按并行度均摊到各 EP rank 的 round-robin topk 列表**覆盖真实 gate 路由的 `topk_idx`，得到完美 EPLB 负载分布。开启后 prefill 每次、decode 仅首次生成并缓存 `cur_topk_list` 注入模型，MoE block forward 里 `if force_eplb: topk_idx = cur_topk_list`。；OOM 卡定位专家负载不均，目标提供仅用于 profiling 的强制均衡探针来隔离该因素。
<!-- cannbot:related:end -->
