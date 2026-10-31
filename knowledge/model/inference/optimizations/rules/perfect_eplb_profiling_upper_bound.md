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
updated_at: '2026-10-29T15:32:47Z'
platforms:
- agnostic
---

# 强制专家负载均衡（round-robin 覆盖 topk）测 MoE decode 性能上界：仅 profiling、不进精度路径，构造均衡 topk 要列优先

## 适用场景

想知道一个 MoE + [EP](../../concepts/parallelism/expert_parallel.md) 部署「在理想专家负载均衡下能跑多快」——即剥离真实路由不均引入的 EP 尾延迟后的纯模型时延上界；或读到一份 benchmark 标了 `perfect_eplb`/`--perfect-eplb`/`force_eplb` 想知道它测的是什么口径时。

## 核心规则

用「强制专家负载均衡」测性能上界：框架用**确定性生成、按并行度均摊到各 EP rank 的 round-robin topk 列表**覆盖真实 gate 路由的 `topk_idx`，得到完美 EPLB 负载分布。开启后 prefill 每次、decode 仅首次生成并缓存 `cur_topk_list` 注入模型，MoE block forward 里 `if force_eplb: topk_idx = cur_topk_list`。

**关键边界（决定它的用途）**：round-robin 索引与真实路由无关 → 每 token 落到确定专家 → 负载完美均衡但**生成结果错误**。所以这是**测量理想负载均衡性能上界的工具开关，不是正确性路径**——不能用于精度业务生成。读该口径 benchmark 时须知它排除了路由不均因素、不代表真实业务时延。

- 前置：模型 `__init__` 须暴露 `num_experts` 与 `num_experts_per_tok`（否则生成合成 topk 时 `raise AttributeError`）。
- rollback：`force_eplb=False` / 不加 `--perfect-eplb`，走真实路由（正确性路径）。

## 构造均衡 topk 的坑：列优先 round-robin，别行优先

要让每个 EP rank 收到相等 token 数、别在 [MC2](../../concepts/techniques/moe_dispatch_combine_v2.md) 分核发送的细粒度上把 token 聚簇到单卡，合成 topk 的**分配顺序**必须列优先（相邻 token 先在 rank 间轮转）。专家按 rank 连续切块（rank r 持 `[r*step_gap,(r+1)*step_gap)`、`step_gap=n_routed_experts//moe_ep_size`）时：

```python
col = idx % moe_ep_size            # 列 = 目标 EP rank（相邻 token 轮转到下一 rank）
row = idx // moe_ep_size % step_gap  # 行 = 该 rank 内局部专家序号
expert_idx = row + col * step_gap    # 全局 expert id = rank 块起点 + 局部序号
```

当 expanded_tokens 可被 moe_ep_size 整除时，每个 EP rank 恰分到 `expanded_tokens / moe_ep_size` 个 token；否则各 rank 数量至多相差 1，例如 10 个 token、4 rank 时为 3/3/2/2。**行优先**连续编号（前 `step_gap` 个 token 全打 rank 0、下一批全打 rank 1）会破坏 mc2 per-rank 发送均衡、测不出理想均衡性能。要点：**mc2 per-rank 均衡由分配顺序决定，列优先能得均衡、行优先不能**——维护者审查确认过分配顺序须对齐 mc2 分核发送逻辑。

## 何时不适用 / 关联

- 只用于性能测评 / profiling，绝不进精度路径。为测 TPOT 常配的 `perfect_eplb: True` 会影响精度，落地精度评估须关闭。
- 规则适用面限本仓 MoE 建模的合成基准路径（`moe_tp_size>1` 与 prefill 分支不在列优先规则内）。
- 提供跨 MoE 模型可复用的「理想负载均衡性能上界」测量手段，参考实现覆盖 DeepSeek-V3.2-Exp（列优先修复）、Qwen3-MoE/DeepSeek-R1（框架 `force_eplb`）、Qwen3-MoE SGLang（`--perfect-eplb`）。

## 相关经验
- [profile_run 峰值显存低估致运行期 OOM：profiling 未实际走一遍所有影](../../runbooks/performance/profile_run_peak_memory_underestimate_untraversed_path.md)

- 另见 [纯 EP MoE decode 中 GMM 无条件执行（0 token 也跑）：profiling 里某卡缺 GMM 不能用「该卡没分到 token」解释，用 expert_token_num 诊断](../../runbooks/validations/moe_ep_gmm_unconditional_zero_token_diagnosis.md)。


## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/243)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/326)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/205)（evidence）
