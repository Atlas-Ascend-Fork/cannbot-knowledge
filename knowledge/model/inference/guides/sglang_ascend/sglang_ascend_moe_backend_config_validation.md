---
type: Guide
title: SGLang 昇腾 MoE 后端参数的有效组合与拒绝条件
description: 说明 ascend_ops JSON、主模型与 speculative draft 一致性、Waterfill 冲突和未实现 fused_op
  的失败边界。
tags:
- task.implementation
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/moe_hook.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/utils.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/fused_moe_triton/layer.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/moe_runner/runner.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-08T12:01:09Z'
platforms: []
---

# SGLang 昇腾 MoE 后端参数的有效组合与拒绝条件

## 可复用的启动配置

`--moe-a2a-backend ascend_ops` 仅用于 NPU。配置示例为 `--moe-ascend-ops-config '{"prefill":"alltoallv","decode":"low_latency"}'`；默认 prefill=alltoallv、decode=low_latency，MC2 dispatch 算法为 fullmesh_v1、combine 为默认空字符串。prefill 可改 allgather，但还需满足其 TP/EP 和 expert 布局约束。

JSON 必须是对象，仅允许 prefill、decode、ll_dispatch_alg、ll_combine_alg，未知键和无效模式失败。虽然 choices 包含 fused_op，当前 __post_init__ 明确拒绝它尚未实现，因此不能把该值作为可部署优化。

## 跨参数关系

只有 main 或 speculative backend 采用 ascend_ops 才能提供对应 JSON；非 NPU 失败。main 选择 ascend_ops 会把 speculative draft 同步为 ascend_ops，main 非 ascend_ops 时不允许 draft 单独选择它。Waterfill 与显式 ascend_ops 冲突，在 backend override 前失败，避免重写隐藏用户不兼容配置。

通信 backend 与 runner 也是独立参数。none 无 A2A 路径要求完整 expert，普通 EP>1 会失败；DeepEP v2 需要 DeepGEMM runner，不能强迫已经选择 Ascend 的量化层接收其布局。

排查启动失败时保留解析后的最终参数和具体异常，先恢复默认合法组合，再逐个改变 prefill、dtype 与算法字符串。验证要覆盖 target/draft、EP=1/多 rank 和实际分派 shape；通过参数校验仅证明配置约束成立，不代表通信执行、精度或收益已验证。
