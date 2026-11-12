---
type: Optimization
title: SGLang 昇腾在线 MXFP4 W4A4 的双层 scale 路径
description: 按实际方法选择区分在线双层 MXFP4 与离线单层 MXFP4，避免沿用过时类注释。
tags:
- task.optimization
- topic.compute.quantization
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/npu_mxfp4_w4a4.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_method_npu.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/__init__.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-08T12:01:09Z'
platforms:
- '950'
---

# SGLang 昇腾在线 MXFP4 W4A4 的双层 scale 路径

## 实际方法选择

950 上 `--quantization mxfp4` 的 NPU 配置返回 `NPUDualLevelMXFP4LinearMethod`。部分类描述仍提单层 MXFP4，但当前执行链以 get_quant_method 和 kernel 为准：权重、激活都调用 `npu_dynamic_dual_level_mx_quant`，取得 packed FP4、细粒度 FP8 L0 scale 和粗粒度 L1 scale。

权重做 NZ 转换后保持此双层算子的方向，不再套单层 Dense 的转置规则；L0 scale squeeze 后转置 contiguous。计算调用 `npu_dual_level_quant_matmul(act,weight,act_l0,weight_l0,act_l1,weight_l1)`，应同时检查两级 scale 的形状与含义。此路径仅适用于 950，A2/A3 不提供该双层算子。

## 使用与验证

适用于在线压缩未量化 Dense 权重；ignored layer 保留原方法，FusedMoE 告警并回退全精度。离线 ModelSlim W4A4_MXFP4 是另一套单层 E8M0 格式，不能直接把其 scale 交给双层算子。

加载前选择量化配置，确认 Dense method 类名，比较激活和权重两级 scale、输出 dtype、模型 logits 与全精度基线。压缩收益须扣除 scale、NZ 存储和加载量化成本，当前来源未提供本次实测结果。回退到未量化加载；不能只切运行时标志复用已改布局的权重。
