---
type: Guide
title: SGLang 昇腾视觉模型的 CPU 长度元数据与 adapter 布局
description: 连接 GLM4V、Qwen2VL、MiniCPM、PaddleOCR 等模型的 CPU cu_seqlens、一次构建复用和局部合并重建。
tags:
- task.implementation
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/glm4v.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen2_vl.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen2_5_vl.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/dots_vlm_vit.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/glm_image_vl.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/idefics2.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/minicpmv_vit.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/paddleocr_vl.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen3_omni_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/kimi_k25.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:20:03Z'
platforms: []
---

# SGLang 昇腾视觉模型的 CPU 长度元数据与 adapter 布局

## CPU 长度与设备激活分开

这些视觉/音频入口在 NPU 把 cu_seqlens 保留或移到 CPU，以满足 unpadded flash attention 的长度参数要求；激活、RoPE 和索引仍按各模型放在设备。Qwen2VL/Dots/GLM Image/Idefics 等在层循环外准备 metadata 并复用，PaddleOCR 直接从 host grids 传 max_seqlen，避免每层 D2H。

GLM4V 一次把 cu_seqlens 转 CPU list，预算 actual_seq_lengths_cpu 与最大长度，所有 ViT blocks 共用。其 spatial adapter 在 NPU 把 kernel=stride 的 Conv2d 改写为 NHWC flatten 的 F.linear，首次按 `[out,h,w,c]` 派生 contiguous 权重缓存，减少 NCHW permute/layout copy；缓存依赖已加载权重，热重载应核对是否失效。源码的参考验证描述不是本次实测。

## 模型专有变化

Qwen2.5VL 有 full/window 两份长度与 metadata，按层选用；MiniCPM 的 2×2 merger 要求 target_sizes 可被2整除、max_seqlen 可被4整除，合并后重建长度并再转 CPU。Qwen3 Omni 音频按 after-CNN chunks 累积 CPU 长度。Kimi K2.5 的 RoPE shape 插值在 NPU 禁 torch.compile，不能把 CUDA 编译收益视作 NPU 已用优化。

验证 metadata 总长度、重复零/空序列、window reverse indices、spatial merge 后 shape 和每层长度复用。不能只改 Tensor device 而忘记更新 merger 后的 metadata；错误长度可能不在最初 reshape 处报错。回退保留 CPU 长度约束，逐步恢复原 adapter 以比较数值。本卡未执行模型或性能测试。
