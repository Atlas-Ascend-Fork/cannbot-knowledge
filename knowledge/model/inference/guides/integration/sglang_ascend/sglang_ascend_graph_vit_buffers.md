---
type: Guide
title: SGLang Ascend ViT图：累计边界、共享池与输出克隆
description: 说明视觉block/merger图捕获条件、Qwen3 deepstack、FIA TND累计长度和图输出跨重放的所有权。
tags:
- task.implementation
- topic.graph_execution
- topic.multimodal
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/graph_runner/vit_npu_graph_runner.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/vision.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/multimodal/vit_cuda_graph_runner.py
  role: implementation
created_at: '2026-11-08T12:08:01Z'
updated_at: '2026-11-09T04:32:43Z'
platforms: []
aliases:
- ViTNpuGraphRunner
- FIA TND cu_seqlens
---

# SGLang Ascend ViT图：累计边界、共享池与输出克隆

## 捕获范围

ViT NPU runner只支持ascend_attn，捕获视觉blocks、merger和可选Qwen3 deepstack；其他attention实现直接报错。graph key实际为(x_3d.shape[0], attention_layout_key)；仅当显式attention_layout_key为None时，才由cu_seqlens与cu_window_seqlens生成布局key（NPU后者传None）。调用方提供显式key时必须完整区分分段边界，否则相同总长度、不同cu_seqlens仍可能命中同一图。cos/sin齐备时才真正建立对应graph。

capture先clone输入，因为blocks会原地修改x；workspace按[seq,heads,head_dim]分配并共享graph pool。deepstack索引已配置却无对应merger时应报错，而不是忽略支路。

## 长度与重放

FIA TND接收cu_seqlens[1:]转CPU int32，语义是每段累计结束位置，不是相邻差值。把[0,4,9]变成[4,5]会错误改变序列边界，应传[4,9]。重放copy输入与cos/sin到持久buffer后执行图。

图输出存储归共享pool，下次replay可覆盖。如果有output_indices，用index_select得到选择结果；否则返回clone以保护上层缓存和拆分输出。直接把graph-owned view交给跨轮视觉缓存，会让先前结果随下一图重放变化。

## 验收与代价

检查key覆盖的序列布局、deepstack merger个数和累计长度；以两个shape相同但分段不同的输入及连续两次replay测试输出稳定性。clone带来额外复制成本，但这是跨重放所有权要求；是否开启视觉图应测端到端编码延迟和显存。本次未运行ViT或图测试，也不把视觉图支持推成所有多模态模型可用。
