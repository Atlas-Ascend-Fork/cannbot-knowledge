---
type: Guide
title: SGLang 昇腾 MTP 的量化配置与通信隔离
description: 连接 DeepSeek、Qwen3-Next、Qwen3.5、Qwen4 和 GLM NextN 的 BF16 draft、临时通信 override
  与恢复。
tags:
- task.implementation
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_nextn.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen3_next_mtp.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen3_5_mtp.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen4_exp_mtp.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/glm4_moe_nextn.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/glm4_moe_lite_nextn.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/utils.py
  role: implementation
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:35:29Z'
platforms: []
---

# SGLang 昇腾 MTP 的量化配置与通信隔离

## target 的量化不等于 draft 的量化

Qwen3-Next、Qwen3.5 和 GLM NextN 的 NPU 构造在未显式指定 speculative_draft_model_quantization 时清空 draft quant_config。Qwen3.5 还区分 ModelOpt 序列化 MTP 的 BF16、modelopt_mixed 是否列出 mtp.*，以及 Quark 是否连 routed experts 也排除；不能仅看到一个 MTP excluded Dense 层就把全部 experts 设 BF16。

当 target 已量化但 draft 实际未量化时，相关 forward 用 ExitStack 临时打开 SGLANG_DEEPEP_BF16_DISPATCH，并关闭 DEEP_NORMAL_MODE_USE_INT8_QUANT；finally/with 退出后恢复，在 dispatcher dtype 为 auto、解析会消费这些旧环境变量时，防止 draft 误继承 target 的 INT8 wire 格式或污染下一次 target forward。非 auto 的显式 deepep_dispatcher_output_dtype 优先于 BF16 环境变量，因此显式 int8 不会被该临时 override 覆盖，仍须核对 draft 实际通信格式。

## 模型状态细节

DeepSeek NextN 可从模型目录 rot.safetensors 读取 rot.weight 作用于前一步 hidden states；NPU draft 与 target 共用模型路径时 decoder prefix 改为目标层数后的 layer。Qwen3-Next 对配置做 deepcopy，shared expert fusion 只允许一个槽。Qwen3.5 处理 multimodal last-token embedding 和 target hidden 与 padded embedding 高度差；idle 时避开空 GemmaRMSNorm。draft 区域禁用 expert distribution 统计，避免污染 target EPLB 观测。

检查实际 draft parameter dtype、wire dtype、临时 env 恢复、shared slot 与输入高度，交替执行 target/draft、idle、multimodal 与异常退出路径比较 logits。回退需重建匹配 draft 权重与缓存，不能只更改 target 量化参数。本卡无 speculative 收益实测。

## 相关机制

- [SGLang 昇腾 DeepEP 的通信 dtype 协商与状态生命周期](sglang_ascend_moe_deepep_wire_compatibility.md)
