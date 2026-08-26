---
type: Optimization
title: 量化 MoE 专家 GMM 的 phase-gated bias 跳过：Prefill 去 bias 提速、Decode 保留
description: 量化 MoE 专家 GMM 的 phase-gated bias 跳过：Prefill 去 bias 提速、Decode 保留。在 EP MoE 的量化专家路径里压 prefill 时延，且专家 FFN 用 grouped matmul（torch_npu.npu_grouped_matmul）算 w13 / w2 时。prefill 阶段的两次专家 GMM 原本都传 bias（w13_bias / w2_bias），这是一处可去除的开销。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/432
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 量化 MoE 专家 GMM 的 phase-gated bias 跳过：Prefill 去 bias 提速、Decode 保留

## 适用场景

在 [EP](../../../concepts/parallelism/expert_parallel.md) MoE 的量化专家路径里压 prefill 时延，且专家 FFN 用 grouped matmul（`torch_npu.npu_grouped_matmul`）算 `w13` / `w2` 时。prefill 阶段的两次专家 GMM 原本都传 `bias`（`w13_bias` / `w2_bias`），这是一处可去除的开销。

## 条件 → 优先尝试什么

- **条件**：量化 MoE（观测于 w4a8int4：权重 4bit / 激活 8bit）专家 GMM 的 **prefill** 阶段。
- **动作**：把两次 `npu_grouped_matmul` 的 `bias` 置 `None`（跳过 `w13_bias` / `w2_bias`），换取 GMM 提速。
- **必须 phase-gate**：只 prefill 跳、**decode 必须保留 bias**。实现上给专家 FFN 传一个 `is_prefill` 标志（默认 `False`），仅 prefill 路由调用方显式置 `True`：

```python
is_prefill = kwargs.get("is_prefill", False)
mm1_mm3 = torch_npu.npu_grouped_matmul(
    [x], [self.experts.w13_weight],
    bias=None if is_prefill else [self.experts.w13_bias],
    scale=[...], per_token_scale=[pertoken_scale], group_list=expert_tokens, ...)
out_hidden = torch_npu.npu_grouped_matmul(
    [intermediate_h], [self.experts.w2_weight],
    bias=None if is_prefill else [self.experts.w2_bias],
    scale=[...], per_token_scale=[pertoken_scale], group_list=expert_tokens, ...)
```

prefill 路由侧在量化模式下才追加 `is_prefill=True`（`gmm_args.update({"is_prefill": True})`），走的是 prefill 双路由路径（[double-routing](../../../concepts/techniques/double_routing.md)）。

## 依据 / 收益

prefill GMM 提速「1300μ+」（仓自报，无 baseline / 命令 / 环境、无独立复测）。已合并、human `/lgtm` + `/approve`。

## 反例 / 风险（迁移前务必读）

- **decode 不可跳 bias**：`is_prefill` 默认 `False` 保证 decode 保留 bias。若把该专家 FFN 在 decode 路径复用而未转发真实 `is_prefill`，会静默丢 bias → 计算错误。「使能信号从配置到调用点被某处悄悄截断」是这类 MoE 间接层的通病，见 [moe-optimization-silently-disabled-decode](../../../runbooks/performance/moe_optimization_silently_disabled_decode.md)。
- **「prefill 跳 bias 为何不损精度」参考实现全程未披露**（gap）——机器 review 判「逻辑正确」、human 只 `/lgtm`，无维护者实质解释。**迁移到其它模型 / 量化模式前须先弄清该 correctness 依据**，不可当作「任何 w4a8 GMM 都能省 bias」的通用律。范围限本仓 [DeepSeek-V4](../../../concepts/models/deepseek_v4.md) w4a8int4 建模路径。

## Evidence

- `diff 事实`（@ad3f0a1180801a273b3221baf8e26231fac6c875）：`models/deepseek-v4/models/modeling_deepseek.py` 的 `DeepseekV3MoE`——w4a8int4 门控追加 `is_prefill=True`、`moe_ffn` 读 `kwargs.get("is_prefill", False)`、两次 `npu_grouped_matmul` 的 bias 按 `is_prefill` 置 `None` / 保留（单文件 +5/-3，三处 hunk 逐条对上）。
- `仓自报`：perf「1300μ+」来自 PR 描述、非 diff 事实、无独立复测——仅作上下文，不并入事实面。「跳 bias 不损精度」的 correctness 依据未披露，标 gap、不外推。
- 溯源下探：[cann-recipes-infer-pr-432-feat-w4a8int4](https://gitcode.com/cann/cann-recipes-infer/merge_requests/432)
