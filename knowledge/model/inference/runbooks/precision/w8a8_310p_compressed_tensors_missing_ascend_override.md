---
type: Runbook
title: 310P 上加载 compressed-tensors 格式 W8A8 模型在 load 阶段崩溃：该平台缺 Ascend override 注册，落回 vLLM 原生 int8 kernel 查表失败——须改 ModelSlim 格式 + --quantization ascend
description: '在 Ascend 310P（Atlas 300I Duo，vLLM 平台枚举 `PlatformEnum.OOT`）上，用 vllm-ascend 加载一个 **W8A8 整数量化模型**，且该模型的量化格式是 **`compressed-tensors`**（config 中 `quant_method: compressed-tensors`，典型来自 **LLM-Compressor** 工具链），在 **model load 阶段直接崩溃**，报错栈大致为 `get_model` → `initialize_model` → 建模型 → `make_layers` → offloader `wrap_modules` 展开 layer 时抛出。'
tags:
- task.debugging
- topic.precision
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/9129
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- 310p
---

# 310P 上加载 compressed-tensors 格式 W8A8 模型在 load 阶段崩溃：该平台缺 Ascend override 注册，落回 vLLM 原生 int8 kernel 查表失败——须改 ModelSlim 格式 + --quantization ascend

## 信号（现象）

在 Ascend 310P（Atlas 300I Duo，vLLM 平台枚举 `PlatformEnum.OOT`）上，用 vllm-ascend 加载一个 **W8A8 整数量化模型**，且该模型的量化格式是 **`compressed-tensors`**（config 中 `quant_method: compressed-tensors`，典型来自 **LLM-Compressor** 工具链），在 **model load 阶段直接崩溃**，报错栈大致为 `get_model` → `initialize_model` → 建模型 → `make_layers` → offloader `wrap_modules` 展开 layer 时抛出。

判据核对：命中本页的处境是「310P + compressed-tensors 格式的 W8A8 + 加载即失败」。**同一模型在 910/910B 上正常加载**、仅 310P 失败，是本页的关键鉴别特征——若两平台都失败，问题不在此。若量化格式已经是 ModelSlim 而非 compressed-tensors，也不是本条。

## 触发条件

- 平台是 Ascend 310P（`PlatformEnum.OOT`），而非 910 系 Ascend 路径。
- 权重是 `compressed-tensors` 量化格式的 **W8A8**（weight int8 + activation int8），典型由 LLM-Compressor 产出。
- 用默认加载路径（未显式指定 `--quantization ascend` 走 ModelSlim 适配）。

## 根因

vllm-ascend 通过为不同量化格式注册各自的 **Ascend override config** 来在 vLLM 原生量化逻辑之前接管路由：

- 910/910B（非 310P 的 Ascend 路径）会注册 `AscendCompressedTensorsConfig`，因此 `compressed-tensors` 格式被 **override** 到 Ascend 自己的 W8A8 实现，正常运行。
- 310P 分支当前**只注册了 ModelSlim 格式的 override（`AscendModelSlimConfig310`）**，**没有**为 `compressed-tensors` 注册 310P 侧的 Ascend 适配。
- 因缺 override，`compressed-tensors` 模型继续落到 **vLLM 原生 `CompressedTensorsW8A8Int8`** 逻辑，最终进入 vLLM 原生 linear int8 kernel selector。维护者推断的最终触发点是：该 selector 的候选表 **`_POSSIBLE_INT8_KERNELS` 只含 `CPU` / `CUDA` / `ROCM`**，没有 `OOT`/Ascend 条目——310P 属 `OOT`，查表命不中而报错（这一细粒度触发点为维护者推断，见「风险 / 边界」与 Evidence）。

归因边界：这**不**说明「`compressed-tensors` 格式本身有害」。同一格式在 910B 因注册了 `AscendCompressedTensorsConfig` 而正常。真正的缺口是 **310P 平台分支尚未补齐 `compressed-tensors` 的 Ascend override 注册**，属平台/后端能力覆盖不完整，不是格式缺陷、也不是权重错误。

## 修法（规避式，维护者给出）

310P 上部署 W8A8 时，**不要用 LLM-Compressor 产出的 `compressed-tensors` 格式**，改用：

1. 用 **ModelSlim** 对模型做 W8A8 量化，产出 ModelSlim 量化格式的权重。
2. 加载时显式传 **`--quantization ascend`**，使其进入 vllm-ascend 310P 当前**已适配**的 Ascend 量化路径（`AscendModelSlimConfig310`）。

即：310P 侧当前的 W8A8 支持面 = ModelSlim 格式（经 `--quantization ascend`），**不含** compressed-tensors。这是**操作约束而非代码修复**——上游 issue 被 triage/resolved 但没有修复 PR，`compressed-tensors` 的 310P override 缺口仍在。等到 310P 补齐 `compressed-tensors` 适配之前，只能走 ModelSlim。

## 风险 / 边界

- 「310P 未注册 compressed-tensors override、须改 ModelSlim + `--quantization ascend`」是维护者的明确路由结论；其中「最终触发点在 `_POSSIBLE_INT8_KERNELS` 查表」这一细粒度归因是维护者的推断，但与「910B 正常 / 310P 失败」的现象自洽。
- 覆盖面随 vllm-ascend 版本变化：一旦 310P 分支补上 `AscendCompressedTensorsConfig` 类的适配，本约束即失效——以目标镜像/commit 的实际注册链为准（本条基于 `quay.io/ascend/vllm-ascend:v0.18.0rc1-310p`）。
- 本条只约束 **310P 上 compressed-tensors W8A8** 这一格式×平台组合，不外推为「310P 不能跑量化」或「compressed-tensors 在所有 Ascend 平台都失败」。

## 相关经验

- compressed-tensors 加载器自身的方案识别门控陷阱（激活量化假设、MX vs fp8、AWQ int4→W4A16）见 [compressed-tensors-scheme-gating-pitfalls](compressed_tensors_scheme_gating_pitfalls.md)。
- 量化格式随 dtype / 平台 / CANN 版本的门控差异见 [quant-format-dtype-platform-cann-version-gating](quant_format_dtype_platform_cann_version_gating.md)。
- W8A8 量化概念与 Ascend 实现见 [w8a8c8](../../concepts/quantization/w8a8c8.md)。
- 本失败为 310P（Atlas 300I Duo）平台专有——量化后端覆盖是逐平台注册的，310P 分支的 Ascend quantization 路径当前只含 ModelSlim（`AscendModelSlimConfig310`），compressed-tensors 的覆盖缺口即源于此平台代际的适配尚未补齐。310P 平台见 [ascend-310p](../../../embodied/concepts/platforms/ascend_310p.md)；[atlas-a3](../../concepts/platforms/atlas_a3.md) 仅用于对照 A3/A2 代际，不覆盖本页 310P 处境。

## Evidence

- `维护者确认`：collaborator 明确答复 compressed-tensors W8A8 未在 310P override、310P 须用 ModelSlim + `--quantization ascend`；另一 collaborator 指出 `_POSSIBLE_INT8_KERNELS`（linear int8 kernel 候选）仅含 CPU/CUDA/ROCM，无 OOT/Ascend。issue 无修复 PR、无 diff，故为维护者确认级别、结论为操作约束。
- 环境：`quay.io/ascend/vllm-ascend:v0.18.0rc1-310p`，Atlas 300I Duo / Ascend 310P，模型 Qwen3-ASR-1.7B 经 LLM-Compressor W8A8 量化。
- 溯源下探：[vllm-ascend-issue-9129-bug-llm-compressor-w8a8-310p](https://github.com/vllm-project/vllm-ascend/issues/9129)
