---
type: Runbook
title: 解码不在正确停止符处终止：eos_token 未注册 / 模型多个 eos token 未全处理，输出残留特殊 token
description: 解码不在正确停止符处终止：eos_token 未注册 / 模型多个 eos token 未全处理，输出残留特殊 token。模型 decode 输出不在应停处终止、或结尾残留特殊 token / 重复吐停止符——不是采样/温度问题，而是停止符处理没覆盖该模型的实际 eos 集合。给复用了兄弟模型 runner 的新模型做 bringup 时尤其常见。
tags:
- task.debugging
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/280
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/288
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 解码不在正确停止符处终止：eos_token 未注册 / 模型多个 eos token 未全处理，输出残留特殊 token

## 信号（现象）

模型 decode 输出**不在应停处终止**、或结尾残留特殊 token / 重复吐停止符——不是采样/温度问题，而是停止符处理没覆盖该模型的实际 eos 集合。给复用了兄弟模型 runner 的新模型做 bringup 时尤其常见。

## 触发条件 + 根因（两类）

### A. eos_token 未注册到 tokenizer

kimi-k2-thinking / deepseek-r1 runner（均走 `DeepseekV3ForCausalLM` 路径）若不在 `DeepSeekRunner.init_model` 里把 `<|im_end|>` 注册为 tokenizer 的 `eos_token`，kimi 解码不会在 `<|im_end|>` 处终止、输出重复吐 `<|im_end|>`。

- 修法：`self.tokenizer.add_special_tokens({"eos_token": "<|im_end|>"})`。

### B. 模型有多个 eos token，截断只按单个 eos 切

GLM-5 有三个 eos token（`[154820, 154827, 154829]` = `['<|endoftext|>', '<|user|>', '<|observation|>']`），而 decode 输出截断原先只按单个 `tokenizer.eos_token` 切分；模型若以非主 eos 的停止符收尾则截不掉，输出残留特殊 token / 越过停止点。

- 修法：读 `config.eos_token_id`（列表）→ `convert_ids_to_tokens` → 对每个 eos token 依次 split。

## 通用先验

- 给新模型（尤其复用他人 runner）做 bringup 时，**先核对该模型的完整 eos 集合**（`config.eos_token_id` 可能是列表）并确保：(1) 全部注册进 tokenizer；(2) 解码截断逻辑对**每个** eos token 都生效，而非只按单个 `eos_token`。
- 症状「输出停不下来/结尾有特殊 token」优先查停止符处理，而非模型前向。

## 风险 / 边界

- eos token id 是 per-model 常量，迁移模型时必须换；照搬兄弟模型的单 eos 逻辑是常见坑。

## 相关经验

- 结构同构模型复用他人建模栈/runner 的其它适配点见 [structural-isomorphic-model-reuse-stack](../../optimizations/experience/rules/structural_isomorphic_model_reuse_stack.md)。
- eos 注册属于 tokenizer 侧 bringup 适配；同类 config/tokenizer 侧车与属性约定陷阱（属性名别名 / chat_template 缺失 / yaml 布尔透传丢失）见 [config-tokenizer-sidecar-and-attr-alias](config_tokenizer_sidecar_and_attr_alias.md)。

## Evidence

- `diff 事实`（@ddf40f9）：`init_model` 加 `add_special_tokens({"eos_token": "<|im_end|>"})` 修 kimi 不终止。
- `diff 事实`（@b451d3e）：GLM-5 三 eos token，改读 `config.eos_token_id` 列表逐个 split。
- 溯源下探：[cann-recipes-infer-pr-280-fix-im-end-print-bugfix](https://gitcode.com/cann/cann-recipes-infer/merge_requests/280)、[cann-recipes-infer-pr-288-glm-5-adapt-class-name-and-function-name-support-bf16-fix-bug-caused-by](https://gitcode.com/cann/cann-recipes-infer/merge_requests/288)
