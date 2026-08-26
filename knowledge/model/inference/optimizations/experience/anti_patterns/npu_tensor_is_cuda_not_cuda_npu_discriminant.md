---
type: Optimization
title: 昇腾适配禁用 tensor.is_cuda 作 CUDA/NPU 判别位：torch_npu 下 NPU 张量 is_cuda 恒为 True
description: '在昇腾 NPU（torch_npu）上适配一份原为 CUDA 编写的框架 / 模型 / 算子链路，代码里出现形如 `if x.is_cuda: 走某条 CUDA 专属路径`（尤其「`if x.is_cuda: 调 torch.ops._C.<some_custom_op>`」按设备门控 custom op）时，本页适用。核对处境：你正在移植上游用 `is_cuda` 分派设备后端的入口，或已在 NPU 上撞到「明明在 NPU 上跑却进了 CUDA-only 分支、调到不存在的 op」的报错。'
tags:
- task.debugging
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/2544
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 昇腾适配禁用 tensor.is_cuda 作 CUDA/NPU 判别位：torch_npu 下 NPU 张量 is_cuda 恒为 True

## 适用场景

在昇腾 NPU（torch_npu）上适配一份原为 CUDA 编写的框架 / 模型 / 算子链路，代码里出现形如 `if x.is_cuda: 走某条 CUDA 专属路径`（尤其「`if x.is_cuda: 调 torch.ops._C.<some_custom_op>`」按设备门控 custom op）时，本页适用。核对处境：你正在移植上游用 `is_cuda` 分派设备后端的入口，或已在 NPU 上撞到「明明在 NPU 上跑却进了 CUDA-only 分支、调到不存在的 op」的报错。

判别位失效的根因是昇腾栈的一个属性：在 torch_npu 下 **NPU 设备张量的 `tensor.is_cuda` 恒为 `True`**（同时 `is_npu=True`）。这一设计是为了让大量上游按 CUDA 写死的路径判断能在 NPU 上直接复用；副作用是 `is_cuda` 无法区分张量真正在 CUDA 还是 NPU。

## 不要做什么

- 不要在昇腾适配代码里用 `if x.is_cuda:` 判断张量是否真在 CUDA 上，进而选择走 CUDA custom-op / CUDA kernel 分支。该判断在 NPU 上恒真、无法区分 CUDA 与 NPU。
- 不要假设「`is_cuda` 为真 ⇒ `torch.ops._C.*` 这类 CUDA custom op 可调」。NPU 侧通常未编译出对应的 `vllm._C`（进程启动会告警 `Failed to import from vllm._C with ModuleNotFoundError("No module named 'vllm._C'")`），一旦进了这条分支就会抛 `AttributeError: '_OpNamespace' '_C' object has no attribute '<op>_'`。

## 为何（机制）

据 torch_npu 源码 `torch_npu/npu/_stream_check.py` L74 的实现，NPU 张量被刻意做成 `is_cuda=True` 且 `is_npu=True`。于是任何「`if logits.is_cuda: 调 torch.ops._C.xxx`」形态的上游代码，在 NPU 上都会进 CUDA 分支，去调 NPU 侧不存在的 custom op，运行时 `AttributeError`。

已知实例：vLLM 的 repetition-penalty 采样入口 `apply_repetition_penalties`。上游 vLLM 引入了按 `is_cuda` 分派 custom-op 的路径后，`apply_repetition_penalties` 中 `if logits.is_cuda and logits.is_contiguous():` 在 NPU 上为真，走进 `apply_repetition_penalties_cuda` → `torch.ops._C.apply_repetition_penalties_(...)`，而 NPU 无 `vllm._C`，栈底报：

```
vllm/model_executor/layers/utils.py:78 apply_penalties -> apply_repetition_penalties(...)
vllm/_custom_ops.py:315 apply_repetition_penalties -> apply_repetition_penalties_cuda(...)
vllm/_custom_ops.py:299 apply_repetition_penalties_cuda -> torch.ops._C.apply_repetition_penalties_(...)
AttributeError: '_OpNamespace' '_C' object has no attribute 'apply_repetition_penalties_'
```

触发前提：采样参数须带 `repetition_penalty != 1.0`（如 `repetition_penalty=1.03`）才会真正走 penalty 路径。旁证——同版本下不带 repetition_penalty 的负载（如 `vllm bench serve`）可正常跑；ais_bench(alsbench) 的 `demo_gsm8k_gen_4_shot_cot_chat_prompt` 因带 `repetition_penalty=1.03` 才命中。降到上游尚无按 is_cuda 分派 custom-op 路径的旧版（vllm v0.9.1 + vllm-ascend v0.9.1rc3）时该负载亦正常（gsm8k accuracy 75.00）。

## 该怎么做（参考实现及其约束）

- **vllm-ascend 的处理**：不去改上游 `is_cuda` 判断，而是在 `vllm_ascend/patch/worker/patch_common/patch_logits.py`（由 `patch_common/__init__` import 生效）里 monkey-patch 掉受影响的入口——把 `vllm._custom_ops.apply_repetition_penalties` 整体替换成强制走硬件无关纯 Torch 参考路径的版本：

  ```python
  from vllm._custom_ops import apply_repetition_penalties_torch

  def apply_repetition_penalties(logits, prompt_mask, output_mask, repetition_penalties):
      apply_repetition_penalties_torch(logits, prompt_mask, output_mask, repetition_penalties)

  vllm._custom_ops.apply_repetition_penalties = apply_repetition_penalties
  ```

  即绕开 `is_cuda` 分派、直接调用与硬件无关的 `apply_repetition_penalties_torch`，不再触碰不存在的 `torch.ops._C`。

- **迁移边界**：这是「NPU 张量 is_cuda=True」这一昇腾栈属性带来的通用陷阱，适用于任何在昇腾上跑、且上游用 `is_cuda` 门控 CUDA custom op 的算子入口。具体命中哪个函数、用 monkey-patch 还是改判断位（例如改成 `is_npu` 优先或显式 device.type 检查），取决于该入口——上例只 patch `apply_repetition_penalties` 是该参考实现的选择，不是本陷阱的唯一解法。

## 适用边界

- 仅当上游确有「按 `is_cuda` 分派设备后端 / 门控 CUDA custom op」的代码路径时才需要处理；不带 `is_cuda` 门控的通用 Torch 路径不受影响。
- penalty 类实例只在采样参数真正触发该路径时暴露（`repetition_penalty != 1.0`），默认参数下可能长期潜伏、换负载才暴露——排查时别被「同版本别的负载能跑」误导。

## Evidence

- torch_npu 源码 `torch_npu/npu/_stream_check.py`（@863b9071）L74：NPU 张量 `is_cuda=True` 且 `is_npu=True` 的实现处。
- vllm-ascend 合并态修复（merge commit `cf96366a`）新增 `vllm_ascend/patch/worker/patch_common/patch_logits.py`，文件顶部注释即陈述该根因并归因于 torch_npu 的 `is_cuda=True`；维护者在 PR 描述中确认修复、issue 报告者确认问题消除。上游引入按 is_cuda 分派 custom-op 的改动为 `vllm/pull/22592`。
- 溯源下探 [vllm-ascend-issue-2544-bug-alsbench-test-failed-due-to-attributeerror-opnamespace-c-object-has](https://github.com/vllm-project/vllm-ascend/issues/2544)

## 相关静态概念

- [torchair](../../../concepts/frameworks/torchair.md) — 昇腾 vLLM/TorchAir 图执行与后端适配栈。
- [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md) — 昇腾侧 NPU 原生融合算子（区别于上游 CUDA `torch.ops._C` custom op），示意 NPU 适配应落到硬件无关或 NPU 原生实现而非误触 CUDA 分支。
