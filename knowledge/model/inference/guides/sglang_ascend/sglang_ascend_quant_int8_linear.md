---
type: Guide
title: SGLang 昇腾静态与动态 INT8 Linear
description: 区分 ModelSlim W8A8 静态输入量化、动态 per-token scale、行并行偏置和预量化输入元组。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_w8a8_int8.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_method_npu.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/linear.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_utils.py
  role: implementation
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:35:32Z'
platforms: []
---

# SGLang 昇腾静态与动态 INT8 Linear

## 两种输入量化契约

静态 W8A8/W8A8S 使用 checkpoint 的 input_scale、input_offset 与 quant_bias；加载后权重转置并转换格式，输入scale/offset按转置后[K,N]权重的输入通道K展开；行并行时为本rank的输入通道分片长度，缓存 reciprocal scale。非 INT8 输入经 `npu_quantize` 转 INT8，再执行量化矩阵乘。`quant_bias` 在 RowParallelLinear 的 TP rank 0 才注入，避免各 rank 的结果求和时重复加偏置。

动态 W8A8 必须有 weight_scale。普通输入经动态 per-token 量化；若 MLA prolog 已返回 `(quant_out,dynamic_scale)`，直接使用元组，避免二次量化，此路径的原始输出类型按 BF16 处理。静态 deq_scale 的存储也区分输出参数类型：BF16 对应 FP32，FP16 对应 INT64 编码，不能统一转成数值 FP32。

## 适配与检查

加载时记录权重 INT8 dtype、转置后的 K/N 方向、scale 形状及 TP bias 所在 rank。NPU ReplicatedLinear.weight_loader对INT8 checkpoint检查dtype一致；per-tensor scale若以多元素加载且目标首维为1，仅在torch.allclose判定各元素与首元素一致时压成单值。ColumnParallelLinear/RowParallelLinear的对应weight_loader检查形状后直接copy_，没有相同dtype检查或scale压缩；这些路径的dtype/scale一致性须在适配时主动核对。

验证应分别覆盖普通激活与预量化元组、TP=1 与多 rank、带偏置与无偏置，并与全精度基线比较 logits。静态、动态格式不可只改方法名称互换；需要恢复对应的原始权重与补偿参数。本卡仅记录源码路径，未执行模型精度或吞吐测试。
