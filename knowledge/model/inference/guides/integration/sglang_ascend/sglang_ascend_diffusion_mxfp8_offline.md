---
type: Guide
title: SGLang Diffusion离线MXFP8：scale配对与NPU矩阵方向
description: 说明ModelSlim E4M3权重、E8M0分块scale后处理和动态activation量化的shape/dtype契约。
tags:
- task.implementation
- topic.diffusion
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/quantization/modelslim_mxfp8_scheme.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/sglang-diffusion/quantization.mdx
  role: implementation
created_at: '2026-11-08T12:26:55Z'
updated_at: '2026-11-09T04:32:43Z'
platforms: []
---

# SGLang Diffusion离线MXFP8：scale配对与NPU矩阵方向

## 权重和布局

离线权重为[out,in] E4M3，checkpoint参数名weight_scale表示uint8 E8M0块scale而非inverse scale，分配[out,in/32]。加载后reshape为[out,in/64,2]，调用matmul时权重与scale分别按实现转置；应检查输入维能满足成对块几何，不能把普通逐通道scale套入。

## 前向

activation非FP16/BF16先转BF16，同时将输出dtype设为BF16；FP16/BF16输入保留其dtype，将任意前导维展平二维；npu_dynamic_mx_quant沿最后一维量化，随后npu_quant_matmul使用group_sizes=[1,1,32]，weight及pertoken scale dtype均E8M0。bias转FP32，输出还原前导shape和约定dtype。每次activation量化增加中间payload与scale开销。

先验证权重名、矩阵方向、scale块数，再对比相同checkpoint的浮点参考或校准基线；覆盖多维batch、bias和非BF16输入。硬件与依赖必须按量化专题核对，不能因类可导入证明A2/A3支持MX算子。本次未加载权重或测精度。
