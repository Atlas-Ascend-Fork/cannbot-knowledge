---
type: Guide
title: SGLang Ascend mRoPE：多轴位置与文本RoPE回退
description: 区分二维多模态位置的Triton路径、一维文本npu_mrope和宽Q原生回退，保留空输入及融合KV写限制。
tags:
- task.implementation
- topic.attention
- topic.multimodal
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/rotary_embedding/mrope.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/rotary_embedding/base.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/graph_runner/npu_cudagraph_backend.py
  role: implementation
created_at: '2026-11-08T12:08:00Z'
updated_at: '2026-11-08T12:08:00Z'
platforms: []
aliases:
- MRotaryEmbedding.forward_npu
- mrope_section
---

# SGLang Ascend mRoPE：多轴位置与文本RoPE回退

## 路线与输入

MRotaryEmbedding的NPU入口拒绝fused_set_kv_buffer_arg，positions只能为1维或2维，token数0时直接返回Q/K。先匹配cos/sin cache dtype；若positions为2维且有mrope_section，使用forward_triton处理多轴分段，不把它送入文本用的全零section。

一维文本路径在query第二维>4096时回退forward_native；否则按NeoX选择half或interleave，mrope_section=[0,0,0]调用npu_mrope。这个宽度判断针对当前Q布局，不能改写成“head_dim>4096”。

多轴分段、交错及legacy轴映射决定时间/高/宽各段取哪组cos/sin；模型端构造positions与section必须对应。NPUGraph重放还须更新mrope positions，不能只更新普通positions；ViT图里的cos/sin是另一套视觉块输入，二者不共享语义。

## 实施与边界

接入时保留空输入guard，记录positions rank、section配置、query物理宽度及选中的实现。对一维文本、二维多轴、宽Q、空DP rank和多轮位置变化做输出对照。Triton路径存在不构成所有NPU架构/编译器版本的支持证明；本次未编译或运行，也不把文本融合算子的能力泛化到完整多模态模型。
