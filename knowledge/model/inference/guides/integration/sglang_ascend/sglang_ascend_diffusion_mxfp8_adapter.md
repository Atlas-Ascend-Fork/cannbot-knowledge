---
type: Guide
title: SGLang Diffusion MXFP8适配器：SRT复用与逐层排除
description: 说明serialized标记、block32与dynamic activation限制，以及NPU复用NPUMXFP8LinearMethod的边界。
tags:
- task.implementation
- topic.diffusion
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/quantization/mxfp8.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/sglang-diffusion/quantization.mdx
  role: implementation
created_at: '2026-11-08T12:26:56Z'
updated_at: '2026-11-08T12:26:56Z'
platforms: []
---

# SGLang Diffusion MXFP8适配器：SRT复用与逐层排除

## 配置和逐层选择

MXFP8Config适配SRT，serialized权重使用weight_block_size=[1,32]，activation_scheme只接受dynamic。MPS直接拒绝；checkpoint按layer标记混合精度时，没有匹配MXFP8标记的层保留unquantized，不能仅凭组件顶层选项把所有Linear量化。

NPU选择NPUMXFP8LinearMethod，复用SRT的native NPU动态量化与matmul；NVIDIA/ROCm可走不同online或Comfy serialized实现，GPU swizzled scale不能直接送入NPU。量化类型相同不表示payload、scale方向与后处理完全相同。

## 接入与验收

先查checkpoint自描述metadata、层名映射与block几何，再确认post-load完成且调用类确为NPU实现。建议同时检查未标记层、混合dtype、组件级覆盖和输出质量；动态activation会产生额外buffer，需记录加载与执行峰值。本次未运行模型，硬件门槛另按MXFP8文档确认，不把adapter可达性当作全模型平台承诺。
