---
type: Optimization
title: 量化 MoE 专家 GMM 的 phase-gated bias 跳过：Prefill 去 bias 提速、Decode 保留
description: 固定 DeepSeek-V4 W4A8int4 的 EP MoE Eager Prefill 双路由路径中，按阶段跳过专家 GMM 的 w13/w2 bias，Decode 保留；省略 bias 的正确性依据仍需核实，图执行迁移需独立验证。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/432
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/ad3f0a1180801a273b3221baf8e26231fac6c875/models/deepseek-v4/models/modeling_deepseek.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-26T03:49:31Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      model_features:
        all_of:
        - moe
---

# 量化 MoE 专家 GMM 的 phase-gated bias 跳过：Prefill 去 bias 提速、Decode 保留

## 适用场景

在 [EP](../../concepts/parallelism/expert_parallel.md) MoE 的量化专家路径里压 prefill 时延，且专家 FFN 用 grouped matmul（`torch_npu.npu_grouped_matmul`）算 `w13` / `w2` 时。prefill 阶段的两次专家 GMM 原本都传 `bias`（`w13_bias` / `w2_bias`），这是一处可去除的开销。

本页记录的是固定 DeepSeek-V4 W4A8int4 的 **Eager Prefill 双路由路径**。来源 `moe_infer_double_routing` 明确限定仅支持 Eager；将该 Prefill 路径迁到图执行时，须另行核对成图、算子支持和精度。这是该函数的执行边界，不能用整网部署中的 Decode 图模式配置推断 Prefill 也在图中运行。

## 条件 → 优先尝试什么

- **条件**：固定 DeepSeek-V4 w4a8int4（权重 4bit / 激活 8bit）专家 GMM 的 **Eager Prefill 双路由**路径。
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

该参考实现仅在 `gmm_quant_mode == "w4a8int4"` 的 Prefill 专家路径追加 `is_prefill=True`（`gmm_args.update({"is_prefill": True})`），走的是上述 Eager Prefill 双路由路径（[double-routing](../../concepts/techniques/double_routing.md)）。

## 依据 / 收益

prefill GMM 提速「1300μ+」（仓自报，无 baseline / 命令 / 环境、无独立复测）。已合并、human `/lgtm` + `/approve`。

## 反例 / 风险（迁移前务必读）

- **decode 不可跳 bias**：`is_prefill` 默认 `False`，缺省调用会保留 bias。只有把 Decode 错标为 `is_prefill=True` 才会在该分支丢掉 bias；反过来，Prefill 未传入 `True` 会保留 bias、失去所述优化。调用链必须转发真实阶段，相关使能信号检查见 [moe-optimization-silently-disabled-decode](../../runbooks/performance/moe_optimization_silently_disabled_decode.md)。
- **「prefill 跳 bias 为何不损精度」参考实现全程未披露**（gap）——机器 review 判「逻辑正确」、human 只 `/lgtm`，无维护者实质解释。**迁移到其它模型 / 量化模式前须先弄清该 correctness 依据**，不可当作「任何 w4a8 GMM 都能省 bias」的通用律。范围限本仓 [DeepSeek-V4](../../concepts/models/deepseek_v4.md) w4a8int4 建模路径。

## Evidence

- `diff 事实`（@ad3f0a1180801a273b3221baf8e26231fac6c875）：`models/deepseek-v4/models/modeling_deepseek.py` 的 `DeepseekV3MoE`——w4a8int4 门控追加 `is_prefill=True`、`moe_ffn` 读 `kwargs.get("is_prefill", False)`、两次 `npu_grouped_matmul` 的 bias 按 `is_prefill` 置 `None` / 保留（单文件 +5/-3，三处 hunk 逐条对上）。
- `固定实现边界`：同文件 `forward` 在 `is_prefill` 时调用 `moe_infer_double_routing`，该函数说明为 `pure ep strategy, for prefill stage mainly, only support eager mode`；此处只确认来源中的 Eager 路径，不代表其他后端的图兼容性或设备复测结果。
- `仓自报`：perf「1300μ+」来自 PR 描述、非 diff 事实、无独立复测——仅作上下文，不并入事实面。「跳 bias 不损精度」的 correctness 依据未披露，标 gap、不外推。
- 溯源下探：[cann-recipes-infer-pr-432-feat-w4a8int4](https://gitcode.com/cann/cann-recipes-infer/merge_requests/432)
