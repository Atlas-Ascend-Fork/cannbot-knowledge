---
type: Guide
title: SGLang Diffusion NPU RoPE：NeoX广播与Flux复数路径
description: 说明NPU rotary_mul条件、BSND位置广播和FLUX/LongCat避免float64的实际模型分支。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/rotary_embedding/base.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/rotary_embedding/utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/dits/flux.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/dits/flux_2.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/dits/longcat_image.py
  role: implementation
created_at: '2026-11-08T12:26:54Z'
updated_at: '2026-11-08T12:26:54Z'
platforms: []
---

# SGLang Diffusion NPU RoPE：NeoX广播与Flux复数路径

## 路线选择

NPU默认借CustomOp回到forward_native；NeoX且rotary_dim<896才考虑npu_rotary_mul，同时要求head<1000与cos/sin行数符合当前序列。BSND的[1,S,1,D]位置表跨batch广播，不能为了复用TND实现把batch简单展平后造成错位。显式positions与默认逐序列位置也需分别核对。

Flux和Flux2生成FP32 cos/sin后组合complex64，进入is_neox=False的Torch复数乘法路径；它们不是npu_rotary_mul融合路线。LongCat在MPS/NPU使用FP32频率、其他平台可用FP64；这是避免NPU float64不支持的模型适配。低精度复数构造、最终输出cast和缓存位置边界都可能影响长序列误差。

先按模型确认旋转配对与缓存格式，再比较多batch、显式位置、非整段rotary和长位置输出。回退Torch通常增加算子数但保留布局语义；不要将任意全宽cos cache交给只接受半宽的helper。本次没有运行数值测试，芯片范围未细分。
