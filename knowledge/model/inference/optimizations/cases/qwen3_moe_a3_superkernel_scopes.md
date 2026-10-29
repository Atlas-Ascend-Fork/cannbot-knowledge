---
type: Optimization
title: Qwen3-MoE A3 SuperKernel 案例：分段标记与可关闭上下文
description: 记录固定 SGLang patch 的 attention/MoE scope、sk_forward 整层入口与 FakeContextManager；关闭分支不等于零开销，整模型数据不能单独归因于 SuperKernel。
tags:
- task.optimization
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/50e41b5b8220284f6721223e9f0d3471cd0b0944/models/qwen3-moe-sglang/patches/0009-feat-support-superkernel.diff
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/50e41b5b8220284f6721223e9f0d3471cd0b0944/models/qwen3-moe-sglang/README.md
  role: constraint
created_at: '2026-10-20T12:18:12Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      objective:
      - latency
      - tpot
      model_features:
        all_of:
        - moe
      execution_mode:
      - ge_graph
      framework:
      - sglang
---

# Qwen3-MoE A3 SuperKernel 案例：分段标记与可关闭上下文

## 条件与规则入口

本案例补充[SuperKernel 决策](../rules/superkernel_decode_ge_graph_fusion_scope.md)，证据固定 `50e41b5b8220284f6721223e9f0d3471cd0b0944`，范围为 Qwen3-MoE / Atlas A3 / SGLang 的 Decode GE 实践。README 记录 SGLang 基底 `2aec8b6e1b588f025ad5e25e2682a44b41a6cdbd` 与一组 patch；本次未恢复基底或应用 patch，不将局部 diff 当作运行时验证。

## 分段与整层入口

`0009-feat-support-superkernel.diff` 在 decoder 中分别以 `scope_<layer_id>_attn`、`scope_<layer_id>_moe` 包裹 attention 与 MLP，同时新增以 `scope_<layer_id>_layer` 包裹 forward 的 `sk_forward`。这证明 patch 提供了这些代码入口；本次没有闭合 `sk_forward` 的真实调用链，不能声称它总会执行，也不能规定唯一合法融合粒度。

`superkernel_scope(enable, scope, options)` 开启时返回 `tng.scope.super_kernel`，关闭时返回带空 `__enter__` / `__exit__` 的 `FakeContextManager`。这样复用同一 `with` 调用形式；对象构造与 Python 上下文调用仍存在，没有“关闭态零开销”的测量证据。

## 配置与收益边界

README 的公开开关为 `--enable-superkernel`。报告的整模型 benchmark 同时启用了专家强制负载均衡与 GE 图缓存，不能用其单点时延作为 SuperKernel 独立收益。本次没有确认任意配置键的静默回退；运行时应核对有效参数和进入的图路径。

验收依照规则卡检查开关传递、实际 scope 与编译结果、输出和时间线。恢复开关后仍需核对缓存与图；本次未执行性能、正确性或回退实验，未新增 `verified`。
