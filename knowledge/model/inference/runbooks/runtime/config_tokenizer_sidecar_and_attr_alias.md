---
type: Runbook
title: config/tokenizer 侧车与属性约定的 bringup 陷阱：MoE 属性名别名、yaml 布尔透传丢失、tokenizer chat_template 缺失
description: config/tokenizer 侧车与属性约定的 bringup 陷阱：MoE 属性名别名、yaml 布尔透传丢失、tokenizer chat_template 缺失。给新模型做 bringup 时，框架从 HF config / tokenizer / 拉起 yaml 里取值，若模型的属性命名、侧车文件、参数透传写法与框架约定不一致，会在加载/拉起处报错或参数被静默丢弃。对号入座。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.multimodal
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/445
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/356
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# config/tokenizer 侧车与属性约定的 bringup 陷阱：MoE 属性名别名、yaml 布尔透传丢失、tokenizer chat_template 缺失

## 适用场景

给新模型做 bringup 时，框架从 HF config / tokenizer / 拉起 yaml 里取值，若模型的**属性命名、侧车文件、参数透传写法**与框架约定不一致，会在加载/拉起处报错或参数被静默丢弃。对号入座。

## 症状 → 根因 → 修法

### A. MoE 开 EP 时 config 属性名别名 → EPLB/MC2 取不到 top_k

- 信号：给 MoE 模型开 EP，`num_experts_per_tok` 取不到、EPLB 路径抛 `AttributeError` 或 MC2 sizing 取不到 top_k。
- 根因：executor 的 MoE EP 工具按 HF 标准属性名 `num_experts_per_tok` 取每-token 激活专家数；模型 config 用别名（如 `Gemma4TextConfig` 的 `top_k_experts`）时取不到。
- 修法：额外把 `num_experts_per_tok` 暴露为别名（指向该模型的实际字段）。

### B. offline 推理 tokenizer 无 chat_template

- 信号：offline 推理在 `tokenizer.apply_chat_template` 处报错（HF 原始权重 tokenizer 不带 chat_template）。
- 根因：该模型 HF 权重目录里缺 chat_template。
- 修法：把仓内 `chat_template.jinja` 侧车模板拷到权重目录，AutoTokenizer（transformers 5.0+）自动加载，**无需改代码**。

### C. 多模 yaml 的布尔 false 被静默丢弃

- 信号：多模态统一拉起 YAML 里 `model_args` 的布尔 `false`（不加引号）没有生效。
- 根因：不加引号的 `false` 被 `mm_build_args` 直接**丢弃、不追加到命令行**（依赖 argparse 默认）。
- 修法：要显式把字面量 `False`/`True` 透传给 pyrallis/Hydra 类解析器，必须写成带引号字符串 `"False"` / `"True"`。

## 通用先验

- MoE/attention 相关 config 字段名跨模型可能是别名，框架按 HF 标准名取值时要补别名映射；
- offline bringup 报 tokenizer/apply_chat_template 错，先看权重目录缺不缺 chat_template 侧车；
- yaml→命令行透传时，**不加引号的布尔/字面量可能被静默吞掉**，需要真透传就加引号。

## 风险 / 边界

- 别名映射是 per-model config 适配点；chat_template 侧车依赖 transformers 5.0+ 的自动加载约定。

## 相关经验

- transformers 5.0 破坏性升级对 vendored config 的影响见 [transformers-5-breaking-changes-vendored-hf-modeling](../compilation/transformers_5_breaking_changes_vendored_hf_modeling.md)。
- 多模拉起脚本/环境坑见 [multimodal-launch-and-runtime-env-pitfalls](multimodal_launch_and_runtime_env_pitfalls.md)。
- 同属 tokenizer 侧 bringup 适配的 eos_token 注册 / 多 eos 截断坑见 [decode-eos-termination-registration](decode_eos_termination_registration.md)。

## Evidence

- `diff 事实`（@30b4ed2）：MoE EP 按 `num_experts_per_tok` 取值、Gemma4 用 `top_k_experts` 别名需补暴露；gemma-4 offline 缺 chat_template、拷 `chat_template.jinja` 到权重目录。
- `diff 事实`（@d7174ec）：`mm_build_args` 丢弃不加引号的布尔 false，须写 `"False"`/`"True"`。
- 溯源下探：[cann-recipes-infer-pr-445-fix-longcat-flash-lite-gemma-4-readme-and-config-files](https://gitcode.com/cann/cann-recipes-infer/merge_requests/445)、[cann-recipes-infer-pr-356-refactor-unified-inference-script-for-multimodal-models](https://gitcode.com/cann/cann-recipes-infer/merge_requests/356)