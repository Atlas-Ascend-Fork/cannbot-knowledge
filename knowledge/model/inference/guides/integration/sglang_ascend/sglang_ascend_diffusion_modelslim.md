---
type: Guide
title: SGLang Diffusion ModelSlim：逐层识别与量化路由
description: 说明quant_model_description、合并投影一致性、权重名映射和INT8/MXFP8/MXFP4方案选择。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/quantization/modelslim.py
  role: primary
created_at: '2026-11-08T12:26:54Z'
updated_at: '2026-11-09T04:32:54Z'
platforms: []
---

# SGLang Diffusion ModelSlim：逐层识别与量化路由

## 加载顺序

ModelSlim按quant_model_description.json解析每层量化格式，支持INT8权重与FP16/BF16计算等声明，忽略项保留非量化；FLOAT 回退要求未映射的 prefix（融合层为各 shard prefix）直接命中 quant_description 的 FLOAT 声明。is_layer_skipped 不使用 reverse/name_mapper；若 FLOAT 只能在后续 scheme 查找时通过名称映射命中，跳过检查不会命中，随后会因没有 FLOAT scheme 抛 NotImplementedError。融合packed投影的所有分片必须具有一致量化类型，不能将一个量化分片和一个FLOAT分片共享同一实现；name_mapper与reverse映射决定checkpoint名能否匹配实际layer。

## 选择与失败

W8A8、W8A8_DYNAMIC和W4A4_DYNAMIC复用SRT方案；W8A8_MXFP8、W4A4_MXFP4及DUALSCALE进入Diffusion自己的scheme。未知quant_type报错，不静默当浮点。不要以GPU的capability数值判断NPU支持；本配置的NPU路线受算子、元数据和对应scheme约束。

先核对每层声明、packed shard同质性、权重/scale文件和名称映射，再做post-load布局转换。建议对未量化层、缺少metadata和混合packed项设置负例，运行后检查实际kernel类与输出质量。格式自动识别只证明加载分派，不等价于全模型精度通过。本次仅阅读，没有量化或运行模型。
