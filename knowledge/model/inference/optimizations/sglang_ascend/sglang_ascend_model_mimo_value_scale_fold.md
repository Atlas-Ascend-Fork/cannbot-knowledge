---
type: Optimization
title: SGLang 昇腾 MiMo V2 的 V scale 向输出权重折叠
description: 说明加载后对未量化 o_proj 折叠 attention_value_scale、关闭运行时乘法与量化层 fallback。
tags:
- task.optimization
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/mimo_v2.py
  role: primary
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:20:03Z'
platforms: []
---

# SGLang 昇腾 MiMo V2 的 V scale 向输出权重折叠

## 场景与机制

当 attention_value_scale 存在且每层 decode 有独立 V multiply 时，MiMo V2 在加载完成后把 scale 乘入浮点 o_proj 权重，并设置 v_scale_folded=True。依据 attention 对 V 的线性关系，未缩放 V 的 attention 输出经过已折叠的 o_proj，表达相同的缩放关系；KV cache 因而存未缩放的 V，所有消费仍经过该层 o_proj。

实现只折叠 FP16、BF16、FP32 权重；量化权重保留运行时 V multiply并告警，不应把量化 payload 当浮点乘 scale，也不能漏更新其 scale 参数。运行时各 attention 路径检查 v_scale_folded，避免重复乘。

## 使用、代价与验证

先确认 checkpoint 原始权重和 attention_value_scale，加载完成检查 folded/skipped 层数及运行时标志，再用浮点参考比较层输出、KV 前缀复用和整模型 logits。浮点舍入可能因乘法位置改变而不同，不能把代数恒等直接写成所有 dtype bitwise 相同。

目标是减少每层 NPU decode 的一次 Muls；加载期原地修改了权重，重入该折叠流程可能重复缩放，所以热重载/重复后处理应先确认原始权重状态。回退从原 checkpoint 重载并恢复运行时乘法。来源没有本次真机计时或精度结果，本卡不报告收益数值。

## 相关机制

- [MiMo-V2-Flash 在 A3 的 PD 与分层 EAGLE 配方](../../guides/models/sglang_ascend/sglang_ascend_doc_mimo_v2_flash.md)
