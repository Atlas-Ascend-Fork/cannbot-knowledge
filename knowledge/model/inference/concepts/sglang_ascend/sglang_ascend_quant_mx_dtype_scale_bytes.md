---
type: Concept
title: SGLang 昇腾 MX dtype 与 E8M0 scale 字节解释
description: 说明 torch 与 torch_npu dtype 参数差别、两类 FP32 scale 容器和 E4M3 手动解码的加载边界。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/dtype_utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_method_npu.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_utils.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:30:20Z'
platforms: []
---

# SGLang 昇腾 MX dtype 与 E8M0 scale 字节解释

## dtype 参数不是普通 Tensor dtype

FP4 算子参数优先取 torch_npu 的整数 dtype enum，不能假设传 `torch.float4_*` 对象等价。Grouped matmul 的 E8M0 scale_dtype 也使用 torch_npu enum；Dense matmul 可接受的 dtype 形式不同。这些符号延迟解析，但失败行为不同：`_get_float8_e8m0fnu_dtype` 与 FP4 helper 在符号缺失时允许返回 None；`_require_e8m0_dtype` 才显式抛错。Dense 路径会把前者结果直接传给 matmul，并无 helper 层的缺失即失败保证。调用方需检查对应分支：将 None 传作 scale dtype 可能改变原始 scale bytes 的解释。

## checkpoint scale 的两种表示

FP32 容器可能装的是 0～255 的整数指数码，需转换为相同 uint8 字节；也可能装实际 power-of-two 浮点尺度，需提取 IEEE754 exponent bits。实现按值是否整数码区分，不做 log2 后再次 rebias。uint8 与 E8M0 的 view 是按位解释，不是数值 cast。

加载工具手动解码 E4M3，绕开部分 NPU 上 FP8→FP32 cast 的 561103 路径：subnormal 为 mantissa/512，最大有限数 448，exp=15 且 mantissa=7 为 NaN。该实现服务于加载转换，不应把 NaN 或溢出悄悄当普通权重。

定位 scale 相关异常时记录容器 dtype、原始 byte、目标算子的 dtype enum 和 reshape 前后形状；用已知 power-of-two 样例核对 exponent。只观察 scale 数值打印或统一 `.float()` 会丢失关键证据。本卡不声明不同 torch_npu 版本间无条件兼容。
