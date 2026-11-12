---
type: Guide
title: SGLang 昇腾 Dense 模型的 RoPE、ALiBi 与 QK 布局差异
description: 按 Baichuan、Llama、Llama4、StableLM 与 Gemma2 区分位置编码 dtype、融合分派和分类模型特例。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/baichuan.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/llama.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/llama4.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/stablelm.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/gemma2.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:20:03Z'
platforms: []
---

# SGLang 昇腾 Dense 模型的 RoPE、ALiBi 与 QK 布局差异

## 模型差异不能只靠公共层替换

Baichuan ALiBi 在 npu 分配按 TP head 范围切片的 slopes，并以 slopes 参数传给 attention；RoPE 模型则走另一分支。总 Q/KV heads 与 TP 的整除或复制关系在构造阶段检查。

Llama 只有 NPU、RoPE 提供 get_cos_sin_with_position 且不是 extend 时才走融合 split/RoPE；起始 layer 刷新按 positions 索引的 cos/sin。不能把 decode 融合无条件用于 prefill。Llama4 的 NPU RoPE 返回新 q/k，需 cat 重建 qk；其 QK norm 在 contiguous BF16 视图上执行，CUDA 原地 view 更新的假设不成立。

StableLM 的 NPU RoPE cache 和计算使用 FP32，完成后 q/k 转回原 dtype，rotary_dim 仍由 partial factor 决定。Gemma2 仅 NPU 的 Gemma2ForSequenceClassification 特例指定 FP32 RoPE 且 attention logit_cap=0；不能扩展为所有 Gemma2 的默认 softcap 语义。

## 适配检查

核对模型架构名、position embedding 类型、partial rotary width、TP head 数和返回值是否原地更新；用 prefill/decode、长 positions、分类与生成两类模型分别比较 q/k 和 logits。回退到各模型的 native 路径应保留其 dtype/softcap 条件，不能统一删除精度提升。来源仅展示软件分支，未声明整组型号或实测加速。
