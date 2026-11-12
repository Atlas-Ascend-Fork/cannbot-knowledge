---
type: Optimization
title: SGLang 昇腾原生 G-B block FP8 Dense 路径
description: 保留 128×128 checkpoint 权重与 FP32 scale，通过原生块量化和 G-B matmul 避免默认 MX 重量化。
tags:
- task.optimization
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/gemm/npu_block_fp8.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/fp8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/gemm/__init__.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:36:43Z'
platforms: []
---

# SGLang 昇腾原生 G-B block FP8 Dense 路径

## 适用守卫

Dense 的 `use_npu_block_fp8` 只在 arch35、FP8 序列化 checkpoint、非 MXFP8、非 FP4 experts、weight_block_size 为 `[128,128]`、scale_fmt 非 ue8m0 且未启用 MX requant 时成立。仅看到`fp8`配置名不足以判断走这条路径。加载还默认执行validate_block_quant_shapes（create_weights的skip_block_quant_check=False）：行并行按TP切输入时input_size_per_partition须能被block_k=128整除；列并行按TP切输出或合并权重时，各output_partition_size须能被block_n=128整除，否则ValueError。只有调用方显式传skip_block_quant_check=True才跳过这些检查并告警；跳过不证明布局有效。满足分派守卫和激活batch非空仍不足以保证TP配置可加载。

权重保持 checkpoint 的 `[N,K]` 与 FP32 block scales；输入 BF16/FP16 展平二维并 contiguous，经 `npu_dynamic_block_quant(row_block_size=1,col_block_size=128)` 得 E4M3 payload 和行块尺度。`npu_quant_matmul` 接收权重、scale 的转置 view，`group_sizes=[1,128,128]`，结果恢复原 batch 维和输入 dtype。G-B 模式不在 matmul 内加 bias，源码在矩阵乘后加转换后的 bias。

## 优化判断与验证

场景是希望使用原生 block-FP8 计算而保留已有 checkpoint 数值；机制避免加载时再量化成 MX，不等于无量化误差或已证明加速。检查 kernel 选择、FP32 scale 和 `[N,K]` 存储，分别测量带 bias、多维输入与 TP 部署。此 TP 路径要求激活 batch 非空，不能据此推断 grouped matmul 的每个 expert 也必须非空。

如果切换 MX requant，应把加载成本与精度变化计入比较；回退时撤销 opt-in 并重新加载。本卡记录 arch35 分支，未把整体安装支持范围扩展到每个芯片型号，保留 draft。
