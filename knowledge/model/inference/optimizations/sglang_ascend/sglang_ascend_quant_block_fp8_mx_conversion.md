---
type: Optimization
title: SGLang 昇腾 block FP8 转 MXFP8 的无损与有损边界
description: 区分 UE8M0 布局展开和普通 FP32 block scale 的 opt-in 重量化，保留 K 对齐及 DSV4 分组权重约束。
tags:
- task.optimization
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/fp8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/fp8_utils.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/dtype_utils.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/unit/npu/quantization/test_npu_mxfp8_linear.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:36:38Z'
platforms: []
---

# SGLang 昇腾 block FP8 转 MXFP8 的无损与有损边界

## 场景与问题信号

arch35 上需明确 block-FP8 checkpoint 的 scale 格式。把普通 FP32 scale 当成 E8M0 字节解释，会改变模型数值；未确认格式时不能为了调用 MX 内核直接改 dtype。

## 两条转换机制

`scale_fmt="ue8m0"` 表示 checkpoint 以指数尺度量化：把原块尺度沿 K 从 block_k 元素展开到32元素粒度，每原块复制 block_k/32 份（block_k=128 时才是128→32），保持 E4M3 权重字节不变，是布局转换。实现要求 K 可被 64 整除、block-K 可被 32 整除，并核对 checkpoint scale shape。

普通 FP32 block scale 只有显式 `SGLANG_NPU_ARCH35_REQUANT_BLOCK_FP8=1` 才加入 MX 路径：手动解码 E4M3 为 FP32，乘展开后的块尺度，经 BF16 舍入，再动态 MXFP8 重量化；这是有损变化。按 `block_n*max(1,1024//block_n)` 行分块控制加载峰值内存。DSV4 wo_a 的批量权重还需从 `[D,G*R]` 转成 `[G,D,R]`，scale 同步转换，不能仅 reshape 权重。

## 启用、代价与回退

先记录原始 checkpoint 与 scale_fmt，验证默认路径的精度，再仅在重新加载进程前设置 opt-in 环境变量。比较相同输入的 logits、困惑度与实际 prefill/decode 延迟；源码中的布局优化不证明具体模型收益。清除此变量并重新加载原 checkpoint 可回退，不能把重打包后的内存直接交给原 block-FP8 kernel。UE8M0 布局路径和有损 requant 路径应分别测试。
