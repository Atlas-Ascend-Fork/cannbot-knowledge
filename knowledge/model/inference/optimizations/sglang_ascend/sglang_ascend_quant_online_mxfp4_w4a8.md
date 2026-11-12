---
type: Optimization
title: SGLang 昇腾在线 MXFP4 W4A8 Dense 与 MoE 回退
description: 说明 950 上在线 FP4 权重与 FP8 激活的真实后端，以及未量化 MoE 回退和 NZ 打包顺序。
tags:
- task.optimization
- topic.compute.quantization
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/npu_mxfp4.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_method_npu.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:36:38Z'
platforms:
- '950'
---

# SGLang 昇腾在线 MXFP4 W4A8 Dense 与 MoE 回退

## 场景与实际格式

`--quantization mxfp_w4a8` 在本版本的 NPU 配置用于 950 在线 Dense 量化：从 BF16/FP16 权重生成 FP4 payload，每字节两个权重，激活使用 E4M3 MXFP8，scale 均按 32 元素粒度。它不要求预先导出 ModelSlim FP4 checkpoint。

Dense kernel 先对 packed `[N,K/2]` 做 NZ 格式转换，再形成转置 view；scale 变成 `[K/64,N,2]`。输入展平后动态量化成 E4M3 与 E8M0，调用 quant matmul，`group_sizes=[0,0,32]`，显式声明 x2 为 FP4；偏置使用 FP32 缓存。

## 配置、代价与回退

仅未跳过的 LinearBase Dense 量化分支在非NPU设备抛 NotImplementedError；ignored LinearBase 在设备检查前返回未量化方法，FusedMoE 也直接告警并回退，不受该设备拒绝分支约束。ignored_layers 同时规范化有无 `model.` 前缀并考虑 fused-module mapping。遇到 FusedMoE 则告警后返回未量化方法：在线 Dense W4A8 不意味着专家也压成 FP4。核对常驻权重和显存时必须分别统计 Dense 与 experts。

加载前启用配置，确认所选 method 与 kernel 的打包布局，再比较全精度、W4A8 两组 logits 和内存峰值。量化与 NZ 转换增加加载成本，并可能改变精度；回退需重新加载未量化 checkpoint。源码中历史 torch_npu 版本问题记录不能替代当前环境的验证，本卡没有实测吞吐收益。
