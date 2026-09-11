---
type: Runbook
title: sglang 单卡 tp1 拉起 OOM：关 ACL/NZ 权重格式转换（SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT=1）
description: sglang 单卡 tp1 拉起 OOM：关 ACL/NZ 权重格式转换（SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT=1）。在昇腾上以 sglang --device npu --attention-backend ascend --tp 1 拉起小模型（观测实例 LLaDA2-mini，Atlas A2，--mem-fraction-static 0.9）时 OOM——单卡（tp1，无 TP 切分、单卡承载全权重）拉不起来。
tags:
- task.debugging
- topic.memory
- topic.model_serving
- topic.data_movement.layout_transform
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/284
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# sglang 单卡 tp1 拉起 OOM：关 ACL/NZ 权重格式转换（SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT=1）

## 信号

在昇腾上以 [sglang](../../concepts/frameworks/sglang.md) `--device npu --attention-backend ascend --tp 1` 拉起小模型（观测实例 LLaDA2-mini，Atlas A2，`--mem-fraction-static 0.9`）时 OOM——单卡（tp1，无 TP 切分、单卡承载全权重）拉不起来。

## 触发条件与处置

- **触发**：tp1（单卡承载全权重）+ 昇腾把权重转成 ACL/NZ（fractal）格式的额外显存开销，一起超出单卡容量。
- **处置**：启动前置环境变量 `export SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT=1`（提交说明明确 "to avoid oom with tp1"）。拉起服务与 CI 均在启动前 export 它（CI 在 `setUpClass` 设、`tearDownClass` 还原）。设该变量后 tp1 可正常拉起。
- **机制（推断，非 diff 事实）**：该变量关闭把权重转换成 ACL/NZ 格式（[weight-nz](../../concepts/techniques/weight_nz.md)）的处理，省掉格式转换权重带来的额外显存，从而在 tp1 下不 OOM。

## 可迁移判断

sglang-on-Ascend 单卡 tp1 拉不起、疑似权重格式转换额外占显存时，优先试 `SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT=1`。TP≥2 时权重已被切分、单卡承载减半，通常不需要此规避。

## 参考实现及其约束

参考 cann-recipes-infer 的 LLaDA2.x-sglang 适配（patch 09 引入该 env、README 启动段与 CI 均 export）。归因主语为本仓 sglang 适配。具体显存机制为推断、已标注；未给显存数字。

## Evidence

- `diff 事实`（@8cd85a87af03）：patch 0009 CI `setUpClass` 设 `SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT=1` / `tearDownClass` 还原，提交标题 "introducing the SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT env parameter, to avoid oom with tp1"，README 启动段亦 export。「关闭 ACL/NZ 格式权重转换省显存」为推断。
- 溯源下探：[cann-recipes-infer-pr-284-feat-llada2-x-sglang-ascend](https://gitcode.com/cann/cann-recipes-infer/merge_requests/284)