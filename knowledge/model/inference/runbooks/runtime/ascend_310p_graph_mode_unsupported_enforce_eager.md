---
type: Runbook
title: Ascend 310P 不支持图模式：aclgraph capture 抛 ACL_MODEL_RI_CAPTURE_STATUS_ACTIVE INTERNAL ASSERT，须加 --enforce-eager
description: 'Ascend 310P（310I 系 / 300I Duo）当前不支持 NPU 图模式（graph mode / aclgraph capture，等价 CUDA graph 的 npugraph_ex 捕获路径）。在 310P 上用 vllm-ascend 起服务、未加 --enforce-eager 时，模型权重加载与 torch.compile 图编译均成功，但引擎在 capture_model 阶段做 aclgraph 图捕获时崩溃：栈落在 piecewise_backend.py 的 with torch.npu.graph(aclgraph, pool=...) → torch_npu/npu/graphs.py capture_begin，抛 RuntimeError: status == aclmdlRICaptureStatus::ACL_MODEL_RI_CAPTURE_STATUS_ACTIVE INTERNAL ASSERT FAILED。报错文案虽写 please report a bug to PyTorch，但根因是 310P 平台能力边界（310I 系仅支持 eager 模式），非通用 torch_npu bug。修法：启动命令加 --enforce-eager 强制 eager 执行、跳过整条 aclgraph 捕获路径。部署纪律：310P 上默认预期图模式不可用，不依赖 aclgraph piecewise 捕获加速。边界严格限于 310P，A3/A2 支持图模式不适用。与 310P 无 Triton kernel 支持并列为同一批 300I Duo bringup 的平台能力缺口。复现环境 vllm-ascend:v0.9.2rc1-310p 镜像、Seed-X-PPO-7B（Llama）、float16、max_model_len 4096、TP1，维护者 collaborator 确认。'
tags:
- task.debugging
- topic.graph_execution
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/2176
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- 310p
---

# Ascend 310P 不支持图模式：aclgraph capture 抛 ACL_MODEL_RI_CAPTURE_STATUS_ACTIVE INTERNAL ASSERT，须加 --enforce-eager

## 信号（现象）

在 **Ascend 310P（310I 系）** 上用通用昇腾推理后端（如 vllm-ascend）起服务时，模型权重加载与 `torch.compile` 图编译均已成功，但引擎在 `capture_model` 阶段做 **aclgraph 图捕获**时崩溃并抛出：

```
RuntimeError: status == aclmdlRICaptureStatus::ACL_MODEL_RI_CAPTURE_STATUS_ACTIVE
INTERNAL ASSERT FAILED at ".../torch_npu.dir/compiler_depend.ts":162,
please report a bug to PyTorch.
```

崩溃栈落在 `torch.npu.graph(aclgraph, pool=...)` 上下文的 `capture_begin`：

```
worker_v1.py compile_or_warm_up_model → model_runner_v1.py capture_model → _dummy_run(num_tokens)
... 模型 forward ...
compilation/piecewise_backend.py __call__
    with torch.npu.graph(aclgraph, pool=self.graph_pool):
torch_npu/npu/graphs.py __enter__ → capture_begin → super().capture_begin(...)
→ RuntimeError: ACL_MODEL_RI_CAPTURE_STATUS_ACTIVE INTERNAL ASSERT FAILED
```

崩溃发生在**图捕获启动**（`capture_begin`），不是权重加载、不是 torch.compile 的 Dynamo bytecode 转换（那两步均已完成）；报错文案虽写「please report a bug to PyTorch」，但根因是 310P 的平台能力边界，**不是通用 PyTorch bug**，不应据此向上游报 bug，也不应按普通断言去 debug torch_npu。A2/A3 上的图捕获断言另有成因，不适用本约束。

`aclgraph`（等价于 CUDA graph 的 NPU 图捕获，属 [NPU 图模式](../../concepts/techniques/npu_graph_mode.md) 的 npugraph_ex 捕获路径）在 310P 上一律不可用；无论具体模型（本次为 Seed-X-PPO-7B / Llama 架构，单卡 TP1，float16），只要在 310P 上未关闭图模式就会撞到同一断言。

## 触发条件

- 硬件为 **Ascend 310P（310I 系）**；
- 后端启用了图模式 / aclgraph piecewise 捕获（vllm-ascend 默认在 `capture_model` 阶段对 decode 走 aclgraph 捕获），**未加 `--enforce-eager`**；
- 与模型架构、dtype、`max_model_len`、并行度无关——只要图捕获路径被触发即复现。

## 根因

**310P（310I 系）当前不支持图模式（graph mode / aclgraph capture）。** 昇腾平台仅在 A2/A3 等代际支持 NPU 图模式；310P 只支持 eager 模式。故引擎进入 `torch.npu.graph(...)` 的 `capture_begin` 时即被 `ACL_MODEL_RI_CAPTURE_STATUS_ACTIVE` 的 INTERNAL ASSERT 拦下——断言拦住的正是 310P 本就不支持的能力。因此这是**固有平台限制**，不是可以靠改代码在 310P 上修好的 bug。

## 修法

在启动命令中加 **`--enforce-eager`**，强制 eager 执行、跳过整条 aclgraph 图捕获路径，从而绕过 `capture_begin` 断言：

```
# 310P 上起 vllm-ascend 服务，显式关闭图模式
... --enforce-eager ...
```

部署纪律（可迁移）：**在 310P 上部署时默认预期图模式不可用**——不要依赖 aclgraph / piecewise graph 捕获带来的 host 下发降开销加速，warm-up 与 capture 一律走 eager。加 `--enforce-eager` 后复现环境（`vllm-ascend:v0.9.2rc1-310p` 镜像、Seed-X-PPO-7B、float16、`max_model_len 4096`、TP1）问题解决。eager 模式下的吞吐 / 时延水位缺可复用数据，本条不对其做承诺。

## 边界

- 范围严格限于 **310P 无图模式支持**这一平台约束；不外推到「所有硬件都要 `--enforce-eager`」。支持图模式的 [Atlas A3](../../concepts/platforms/atlas_a3.md) / A2 不受此约束，在那些平台上 `--enforce-eager` 反而会放弃图模式加速。
- 这是与 [310P 不支持 Triton kernel](ascend_310p_no_triton_kernel_eager_fallback.md) 并列的另一条 310P 平台能力缺口：一个是无图模式（修法=关图模式跑 eager），一个是无 Triton（修法=补 Triton-free host 等价路径）。二者同为 310P 平台能力缺口，可在 310P bringup 中分别遇到。
- 官方对该平台的支持口径以 300I 单机部署教程为准（vllm-ascend 300I 单机教程）。

## 相关经验

- [Ascend 310P 不支持 Triton kernel：走 Triton 的算子须补纯 host/eager 等价路径](ascend_310p_no_triton_kernel_eager_fallback.md)——同为 310P 固有平台能力缺口下的「回退到 eager / host 等价路径」修法。
- [是否/何时启用图模式：按 host 下发占比与 profiling 决策](../../optimizations/rules/graph_mode_enable_decision_profiling.md)——图模式开关的正向决策；本页是该开关在 310P 上被硬约束为「必须关闭」的一端。
- [bringup 报错根因常在环境/驱动/平台层](bringup_error_root_cause_env_driver_platform.md)——同属「报错文案指向通用 bug、真因在平台/环境层」的排查取向。

## Evidence

- 报错栈：`piecewise_backend.py` 中 `with torch.npu.graph(aclgraph, pool=self.graph_pool)` → `torch_npu/npu/graphs.py` `capture_begin` → `RuntimeError: status == aclmdlRICaptureStatus::ACL_MODEL_RI_CAPTURE_STATUS_ACTIVE INTERNAL ASSERT FAILED`，发生在 `compile_or_warm_up_model → capture_model → _dummy_run` 之后的图捕获阶段（权重 14.0 GB 已加载、KV cache 已算出 184,448 tokens）。
- 维护者确认：collaborator 明确「currently, for 310I series, only eager mode is supported. plz add --enforce-eager option」，并附官方 300I 单机部署教程作为该平台支持口径；另一条评论「310p does not support graph mode currently. Try to add --enforce-eager」。根因（310P 无图模式）由维护者归因，属固有平台限制而非配置 workaround。
- 复现环境：`vllm-ascend:v0.9.2rc1-310p` 镜像、`ascend 310p*1`、Seed-X-PPO-7B（Llama 架构）、`--dtype float16`、`--max_model_len 4096`、TP1；加 `--enforce-eager` 后解决、条目关闭。
- 耐久性：只要 310P 系图模式未被支持，任何在 310P 上不加 `--enforce-eager` 起 vllm-ascend 的用户都会撞到同一 aclgraph capture 断言。
- 溯源下探：[vllm-ascend-issue-2176-bug-ascend310p3-encountered-an-exception-while-running-seed-x](https://github.com/vllm-project/vllm-ascend/issues/2176)