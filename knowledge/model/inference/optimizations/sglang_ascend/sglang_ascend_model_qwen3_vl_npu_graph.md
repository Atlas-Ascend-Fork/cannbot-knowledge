---
type: Optimization
title: SGLang 昇腾 Qwen3-VL 的 ViT 图与插值一致性
description: 说明 NPU 图入口、精确 attention layout key、CPU 长度及向量化位置插值的模式守卫。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen3_vl.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/graph_runner/vit_npu_graph_runner.py
  role: constraint
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:36:38Z'
platforms: []
---

# SGLang 昇腾 Qwen3-VL 的 ViT 图与插值一致性

## 图入口与静态键

SGLANG_VIT_ENABLE_CUDA_GRAPH 在 NPU 选择 forward_with_npu_graph，名称沿用 CUDA 但执行并非 CUDA graph runner。ViTNpuGraphRunner._create_graph 仅接受 mm attention backend=ascend_attn，其他后端抛 RuntimeError；切换其他多模态 attention backend 时应关闭该图开关。准备阶段先 patch embedding、位置插值和 RoPE，计算完整 cu_seqlens；图调用前长度转 CPU，以 `(tuple(cu_seqlens.tolist()),None)` 为 attention_layout_key，output_indices=None。

图复用不只依赖总 token 数：不同图片长度划分即使总数相等，也必须保留不同 cumulative layout key。普通 eager 分支同样把长度留 CPU，并在层循环前一次准备 metadata；deepstack feature 按指定层收集并与最终 merger 特征拼接。

## 插值与优化守卫

向量化位置插值需显式环境开关和足够图片数量；图准备还要求 align_corners，因向量化实现使用 linspace 坐标，而旧图 fallback 的 precise interpolation 模式可能不同。忽略该守卫会让图片数量改变插值数值，不是单纯性能差异。

启用前分别比较 eager/graph 的位置 embedding、相同总 token 不同 grids、不同图片数、deepstack 输出与模型 logits。图缓存与预处理有额外常驻内存/准备成本，不能只记录 replay 单次时间。关闭该图环境变量并重建 runner 回退；本卡没有真机重放或加速结果，型号范围保持未知。
