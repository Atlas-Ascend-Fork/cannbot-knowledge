---
type: Runbook
title: NPU fused_topk 默认先归一化再按 routed_scaling_factor 缩放：保留 norm_topk_prob=True 会二次归一化破坏路由缩放语义
description: NPU fused_topk 默认先归一化再按 routed_scaling_factor 缩放：保留 norm_topk_prob=True 会二次归一化破坏路由缩放语义。把一个带 routed_scaling_factor（对路由专家结果缩放）的 MoE 用 NPU 融合 topk（fused_topk_npu()）适配到昇腾上，若沿用上层默认 norm_topk_prob=True，路由专家的缩放语义被破坏——routed_scaling_factor 被再归一化一遍（renorm），MoE 输出不对。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/284
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/7573
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/issues/495
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# NPU fused_topk 默认先归一化再按 routed_scaling_factor 缩放：保留 norm_topk_prob=True 会二次归一化破坏路由缩放语义

## 信号（现象）

把一个带 `routed_scaling_factor`（对路由专家结果缩放）的 MoE 用 NPU 融合 topk（`fused_topk_npu()`）适配到昇腾上，若沿用上层默认 `norm_topk_prob=True`，路由专家的缩放语义被破坏——`routed_scaling_factor` 被再归一化一遍（renorm），MoE 输出不对。

## 触发条件 / 根因

NPU 的 `fused_topk_npu()` **默认「先归一化、再按 `routed_scaling_factor` 缩放」**。如果上层还置 `norm_topk_prob=True`，等于对已归一化并缩放过的 `routed_scaling_factor` 又归一化一次，破坏缩放。这是 `fused_topk_npu` 的**固有行为**（与具体 PR 无关）：谁把带 `routed_scaling_factor` 的 MoE 接到这个融合 topk 上、又保留 `norm_topk_prob=True`，都会撞到。

## 修法

NPU 上强制关闭 topk 归一化，把缩放交给融合 moe runner：

```python
# fused_topk_npu() by default conduct norm before scale with routed_scaling_factor
# norm_topk_prob=True will renorm the routed_scaling_factor thus need to keep norm_topk_prob=False
if _is_npu:
    self.norm_topk_prob = False
```

同时把 `routed_scaling_factor` 传入 fused_topk 配置与 experts 配置，由融合 moe runner 施加缩放（而不是在 Python 层手动 `mul_`/`add_`）。

## 边界 / 关联

范围限带 `routed_scaling_factor` 的 MoE 在 NPU fused_topk 路径（参考实现 LLaDA2.x-sglang，带 `correction_bias` 的 sigmoid 路由 gate）。收益 = 保持路由专家缩放语义正确，无 benchmark。同 NPU 适配里共享专家输出并入 [fused MoE finalize/combine](../../concepts/techniques/moe_dispatch_combine_v2.md) 的取舍见 [moe-shared-expert-decode-dual-stream](../../optimizations/experience/rules/moe_shared_expert_decode_dual_stream.md)；MoE 路由/分发的阶段选型见 [moe-ep-dispatch-path-by-stage](../../optimizations/experience/rules/moe_ep_dispatch_path_by_stage.md)。

## 更一般的规律：路由权重 / 归一化在昇腾融合 MoE 里只加一次

上面「二次归一化破坏缩放」是同一条通用规律的一个实例。昇腾融合 MoE 把「打分归一化」和「路由权重加权」拆到多个环节：门控 top-k 算子（内建 renorm / norm_type）、专家输入端、以及专家输出合并算子（`npu_moe_finalize_routing` 的 `scales`）。**这些环节里，同一份归一化或同一份路由权重只能被应用一次**——多个环节各自默认「我来做」时就会重复应用，破坏语义。适配一个模型到融合 MoE 路径时，必须先盘清「归一化在哪一环做、路由权重在哪一环加」，把其余环节显式关掉（置默认值 / 传恒等 scales）。

判断落在本规律上的处境：把一个上层框架（vLLM / SGLang / 自定义 gate）的 MoE 接到昇腾融合算子，且模型带有以下任一语义时——`routed_scaling_factor` 路由缩放、softmax 打分后要求按 top-k 权重和重归一、或「路由权重作用在专家输入上」（`apply_router_weight_on_input`）。这些语义都跨越了「门控算子 / 输入端 / finalize 端」的加权点，需要人为在框架侧对齐，融合算子不会自动只做一次。

### 参考实现及其约束 — A5 门控 top-k：算子固定 `renorm=0` + Python 侧补重归一

在 vllm-ascend 上把 MoE 门控 top-k 从自定义算子切到 A5(ascend950) 的 `torch_npu.npu_moe_gating_top_k` 时，该 torch_npu 算子的 `renorm` 入参**不覆盖**「softmax 打分（`norm_type==0`）后按 top-k 权重和重归一」这一语义。做法是给算子**硬编码 `renorm=0`**（不透传外部 `renorm`），把重归一挪到框架 Python 侧显式做：

```python
topk_weights, topk_ids, out = torch_npu.npu_moe_gating_top_k(
    x, k=k, bias=bias_opt, k_group=k_group, group_count=group_count,
    group_select_mode=group_select_mode,
    renorm=0,                 # 固定 0，不透传入参 renorm
    norm_type=norm_type, routed_scaling_factor=routed_scaling_factor, eps=eps,
)
if norm_type == 0 and renorm == 1:
    topk_weights = topk_weights / topk_weights.sum(dim=-1, keepdim=True)
return topk_weights, topk_ids.to(torch.int32), out
```

对比非 A5 基类：直接把 `renorm` 透传给自定义 `_C_ascend.moe_gating_top_k`、无 Python 侧补做。两版共同细节：返回的 `topk_ids` 统一 `.to(torch.int32)`（id dtype 归一）；`bias_opt` 在 torch_npu 版作 `bias=` 传入。约束：这条系于 `torch_npu.npu_moe_gating_top_k` 在 ascend950 上的具体 renorm 语义（参考实现自报 CI + Ascend950DT E2E 通过，无独立精度/性能数据）；换算子的人别指望入参 `renorm` 覆盖该重归一，须固定 0 + 框架侧补做。

### 参考实现及其约束 — `apply_router_weight_on_input`：输入端加权则 finalize 端 scales 置全 1

模型语义要求「路由权重直接作用在专家输入上」时（`apply_router_weight_on_input`，如 Llama4/mllama4 路由后 topk=1 的 shared/routed 专家形态），vllm-ascend 融合 MoE 默认仍把路由权重通过 `npu_moe_finalize_routing` 的 `scales` 在专家输出合并阶段乘一次——同一份权重被乘两遍，结果错误。参考实现在 `fused_experts` 新增 `apply_router_weight_on_input: bool` 形参，两处落实「只加一次」：

```python
# 入口：前置校验并把 topk_weights 预乘进输入
if apply_router_weight_on_input:
    assert topk_weights.dim() == 2, "`topk_weights` should be in shape (num_tokens, topk)"
    _, topk = topk_weights.shape
    assert topk == 1, "Only support topk=1 when `apply_router_weight_on_input` is True"
    hidden_states = hidden_states * topk_weights.to(hidden_states.dtype)

# finalize：既已在输入端乘过，把 scales 置全 1，合并阶段不再乘一次
scales = torch.ones_like(topk_weights) if apply_router_weight_on_input else topk_weights
final_hidden_states = torch_npu.npu_moe_finalize_routing(..., scales=scales, ...)
```

昇腾抓手：`torch_npu.npu_moe_finalize_routing` 的 `scales` 入参决定专家输出合并阶段是否再乘一遍权重——「输入端加权 vs finalize 端加权」二选一是这条算子契约特有的加权点问题。约束：参考实现里 `topk==1` 是断言硬约束（该实现的限制，非技术本身上限），选输入端加权就必须把 finalize 的 `scales` 置全 1；参考实现无数值指标，功能性验证为 Llama-4-Scout-17B 起服务后正确图文问答。

## Evidence

- NPU 强制 `norm_topk_prob=False` + 注释根因（fused_topk_npu 先归一化再缩放）、`routed_scaling_factor` 传入 fused_topk/experts 配置：最终合并态 diff 事实 @8cd85a87af03（同 PR 内曾试 `router_dtype=bf16` 已被回退、不纳入）。溯源下探 [cann-recipes-infer-pr-284-feat-llada2-x-sglang-ascend](https://gitcode.com/cann/cann-recipes-infer/merge_requests/284)。
- A5 门控 top-k 固定 `renorm=0` + Python 侧对 `norm_type==0 & renorm==1` 补重归一、`topk_ids→int32`：合并态 diff 事实 @d452d04656eabc0bf719e1d07093973274eebd6e（`device/device_op.py` A5 override + `ops/fused_moe/experts_selector.py` 分发）。溯源下探 [vllm-ascend-pr-7573-a5-bugfix-fix-fused-moe-a5-mxfp8-scale-normalization-load-balance-routin](https://github.com/vllm-project/vllm-ascend/pull/7573)。
- `apply_router_weight_on_input`（topk==1 断言 + 输入端预乘 + finalize `scales=ones_like` + `forward_oot` 透传）：合并态 diff 事实 @e56447033889ca95df512208cab22ef832bfdf07（`ops/fused_moe.py::fused_experts` + `ops/common_fused_moe.py::forward_oot`）。溯源下探 [vllm-ascend-issue-495-bug-notimplementederror-custom-routing-function-is-not-supported-now](https://github.com/vllm-project/vllm-ascend/issues/495)。
