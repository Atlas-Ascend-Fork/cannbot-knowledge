---
type: Guide
title: SGLang 昇腾 MXFP8 Dense 的在线量化与 TP scale 对齐
description: 说明 E4M3 权重、32 元素 E8M0 scale、64 元素配对布局及跨 TP 分片的 block 对齐。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_mxfp8.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_method_npu.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/fp8.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-08T12:01:09Z'
platforms: []
---

# SGLang 昇腾 MXFP8 Dense 的在线量化与 TP scale 对齐

## 权重与 scale 的配对

在线路径把加载的 BF16/FP16 权重动态量化为 E4M3 与每 32 个 K 元素一个 E8M0 scale。ModelSlim 离线路径直接创建 E4M3 权重和 uint8 scale，不重新量化已有权重。scale 个数为奇数时补零后成对打包，例如 K=4304 的 135 个 scale 补到 136。

Dense matmul 接收权重的 `[K,N]` 转置 view，scale 由 `[N,K/32]` 配成 `[K/64,N,2]` 转置 view；这里保留 stride，不能随手调用 contiguous 改变底层期望的转置描述。已有输入量化元组可以复用，原始 uint8 scale 通过 dtype view 恢复 E8M0，并配成 pairs。普通输入展平为二维动态 MXFP8 量化，再恢复 batch shape；矩阵乘 group_sizes 为 `[1,1,32]`。

## TP 非整块分片

ModelSlim MXFP8 scale loader 按全局 K 起点计算左右 block padding，相邻 TP rank 可能共享边界 scale。权重与激活须采用相同 padding；此类不对齐分片拒绝预量化输入元组，因为无法安全追加原始激活边界。不能用本地 `K//32` 简单切片替代 loader。

检查每 rank 的 global start、padding、scale byte 与最终 shape；覆盖 aligned/unaligned TP、奇数 scale 数和 tuple 输入。bias 的 FP32 缓存仅在同一 bias 对象复用，动态 bias 仍须转换。型号支持未由这一通用分支完整声明，保留 draft；没有实测收益结论。
