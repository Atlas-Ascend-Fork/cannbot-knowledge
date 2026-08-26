---
type: Runbook
title: LongBench 输入构造 input_max_len < system_prompt 长度 → 负索引尾切静默裁掉正文
description: LongBench 输入构造 input_max_len < system_prompt 长度 → 负索引尾切静默裁掉正文。跑 LongBench / 自定义长序列数据集（dataset != "default"）时，喂给模型的 prompt 正文被大幅裁掉，长序列 case 实际输入远短于预期——但控制台只有一条 logging.info（"The parameter 'input_max_len' should be greater than the length of system_prompt..."），无报错、无中断，极易被忽略。看到这条 info 即代表已越界。
tags:
- task.debugging
- topic.long_context
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/90
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# LongBench 输入构造 input_max_len < system_prompt 长度 → 负索引尾切静默裁掉正文

## 信号（现象）

跑 LongBench / 自定义长序列数据集（`dataset != "default"`）时，喂给模型的 prompt 正文被大幅裁掉，长序列 case 实际输入远短于预期——**但控制台只有一条 `logging.info`**（"The parameter 'input_max_len' should be greater than the length of system_prompt..."），**无报错、无中断**，极易被忽略。看到这条 info 即代表已越界。

## 触发条件

- `executor/utils/data_utils.py` 的 `build_dataset_input`，YAML 的 `input_max_len` **小于**固定 system prompt 的 token 长度。
- 消费面广：基类 `ModelRunner` 与 [deepseek-r1](../../concepts/models/deepseek_r1.md) / [kimi-k2-thinking](../../concepts/models/kimi_k2_thinking.md) / [deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md) / [qwen3-moe](../../concepts/models/qwen3_moe.md) 的 LongBench 跑法**共用同一构造函数**。小 CI 配置为图快把 `input_max_len` 设很小时尤其命中（DeepSeek-R1 的 LongBench config 原 `input_max_len: 32` 即小于该 system prompt 实际 token 数）。

## 根因

`build_dataset_input` 先算固定 system prompt 的 token 数 `system_prompt_len = len(tokenizer(prefix + suffix).input_ids)`，再按 `prompt_inputids[:input_max_len - system_prompt_len]` 截原文预留其预算。当 `input_max_len < system_prompt_len` 时切片上界 `input_max_len - system_prompt_len` 为**负数**，Python **负索引**语义使其从序列**尾部**计数——正文被从末尾大段丢弃，而非报错。

## 修法 / 规避

- 配 LongBench 时保证 `input_max_len >`（固定 system prompt 的 token 数）。system prompt 文本在 `executor/utils/data_utils.py` 内固定，可用 `len(tokenizer(prefix+suffix).input_ids)` 实测其 token 数据此设下界（DeepSeek-R1 config 已从 32 上调到 64 佐证方向）。
- 命中那条 `logging.info` 即代表已越界，须调大 `input_max_len` 或改小 system prompt——不要忽略这条 info。

## Evidence

- **代码事实**（clone `@0002ff4f64c8`）：`build_dataset_input` 的 `system_prompt_len` 计算、`if system_prompt_len > input_max_len: logging.info(...)` 分支、`prompt_inputids[:input_max_len - system_prompt_len]` 切片，及 DeepSeek-R1 config `input_max_len: 32→64`。
- **直接推理**：「预算变负 → 负索引尾切」为对该切片负索引语义的直接推理（32→64 上调佐证）；底层 tokenizer 对该 system prompt 的精确 token 数源未给出。
- 溯源下探：[cann-recipes-infer-pr-90-fix-fix-check-model-cfg-fix-build-dtatset-input](https://gitcode.com/cann/cann-recipes-infer/merge_requests/90)
