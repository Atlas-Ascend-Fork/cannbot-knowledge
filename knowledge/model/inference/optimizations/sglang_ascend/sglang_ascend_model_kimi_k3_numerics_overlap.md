---
type: Optimization
title: SGLang 昇腾 Kimi-K3 的数值守卫与细粒度 shared overlap
description: 说明 K3 保留 MXFP4 scheme、禁用非等价 QK 融合、latent MoE 空 rank 和 shared expert 流事件依赖。
tags:
- task.optimization
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/kimi_k3.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/model_overrides/kimi_k3.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:36:43Z'
platforms: []
---

# SGLang 昇腾 Kimi-K3 的数值守卫与细粒度 shared overlap

## 格式与数值前提

加载compressed-tensors MXFP4 checkpoint时，Kimi-K3在NPU保留该配置，选择NPU W4A8 MXFP4 MoE，不转换为GPU Mxfp4Config，加载时也保留weight_packed名称；其他quant_config原样传给专家，不能将这条分支推广为所有NPU K3量化格式（A3 ModelSlim W4A8与950 MXFP4配方不同）。w1/w3 为非交错 gate/up，SiTU 的 beta/linear_beta 随配置传入专家。模型显式禁用 Ascend fused split+QK norm，理由是与 K3 数值不等价；不能以其他 MLA 模型已用融合为由重新打开。

NPU 跳过 GPU KDA merged b/f_a、fused decode 准备及相应 GPU kernel precompile；dense MLP 可按 enable_dense_mlp_attn_tp 在 attention-TP replica 内分片，而不是照搬 GPU 全 TP 的布局。

## 细粒度重叠机制

SGLANG_NPU_FINE_GRAINED_MOE_DUAL_STREAM 仅在 NPU、有 shared overlap/TP communication、latent MoE、非空 token、DeepEP 且 dispatcher 为 MaybeTboDeepEPDispatcher 时生效，并排除 breakable/piecewise 图断点。side stream 先排 shared AllGather；pre-dispatch hook 等 gate/TopK/latent down-proj 后执行 shared MLP；post-dispatch hook 排 ReduceScatter，routed GMM 只等 shared compute，尾部才等 shared 完整事件。hook 在 finally 移除，不能泄露到下一批。

latent MoE 的空 rank 跳过不支持空激活的量化 matmul，创建 shape-only 结果，但仍参与 experts collective；combine 后空结果也避开 norm/up-proj。

## 代价、验证与回退

检查实际 TP 分组、gate/up、hook 次序和 record_stream 生命周期；比较 overlap 开关两侧的逐层输出、idle rank、多步 decode 与请求尾部延迟。重叠增加 stream/event 与存储生命周期复杂度，收益依赖通信/计算比例；关闭变量并重建执行图回退。本次未测量速度或证明所有 K3 变体已可运行。

## 相关机制

- [SGLang 昇腾 compressed-tensors 的可用 scheme 与限制](../../guides/sglang_ascend/sglang_ascend_quant_compressed_tensors.md)
- [SGL SiTU 浮点激活与分组有效前缀](../../apis/sgl_kernel_npu/sgl_situ_and_mul.md)
