---
type: Guide
title: SGLang 昇腾 DeepSeek V4 的 RoPE、并行准备与输出投影
description: 记录 DSV4 模型的逐 forward RoPE 缓存、Q/KV 多流、CP 完整 metadata 和 950 MXFP8 wo_a
  守卫。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_v4.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/utils.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/fp8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_utils.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_dsv4_backend.py
  role: implementation
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:35:32Z'
platforms: []
---

# SGLang 昇腾 DeepSeek V4 的 RoPE、并行准备与输出投影

## RoPE 与执行准备

DSV4 NPU 为 RoPE 预建 FP32/BF16 不可变全表，并缓存 Q per-head RMSNorm 的 BF16 ones，避免每次创建 gamma。按 positions gather 的 cos/sin 只在当前 forward memoize；target 与 NextN 可共享全表，却不能按 batch shape 跨步复用已 gather 的结果。非 TBO 模型入口先 prime，同步在分流之前完成。

`SGLANG_NPU_USE_MULTI_STREAM` 且 alt streams 存在、token 数不超过阈值且不是 extend/draft_extend/mixed 时，Q、KV 与 indexer/compressor 分流。KV 写 cache、Q norm/RoPE 和索引压缩有显式 event/stream 等待，不能移除尾部 join。CP路径先gather完整KV，仅indexer的compressor和core compressor在dsv4 CP full metadata上下文中执行；退出上下文会恢复本地metadata与positions，随后indexer的Q/打分阶段在本地metadata下运行，并以skip_compressor=True跳过已完成的压缩。

## 输出投影与加载

NPU 输出先作 inverse RoPE。950 的 arch35 MXFP8 wo_a helper 要求序列化 FP8 checkpoint、128×128 block 且 wo_a_keeps_quant_config 未显式关闭。该分支要求加载后权重与 scale 已按 attention group 转换；动态量化输出后调用 npu_transpose_quant_batchmatmul，group_sizes=(0,0,32)，scale 以 E8M0 view 传递。仍须核对 UE8M0 或 opt-in 重量化路径，不能只因 helper=True 就认定布局正确。GPU DeepGEMM/ROCm fused inverse-RoPE 不适用于此。未选择量化 wo_a 时加载器先反量化，构造与加载判断必须一致；选择量化却收到非 E4M3 权重直接失败。

## 边界与验证

V4.1 vision 需要无 CP、无 PP，A2A 仅允许 none 或 CUDA MegaMoE；NPU 不能借用后者。NPU 跳过 TileLang mHC 预热，热权重替换使用 device module 清缓存并同步。

逐步检查不同 positions 的多次 decode、target/draft 交替、CP、空批次和多流 logits；评估加载内存、量化误差与真实延迟后再启用优化，回退需重建布局/streams。这里没有真机收益或完整 Device 算子分析。

## 相关机制

- [SGLang 昇腾 block FP8 转 MXFP8 的无损与有损边界](../../optimizations/sglang_ascend/sglang_ascend_quant_block_fp8_mx_conversion.md)
- [SGL交错token/batch矩阵乘与显式NZ权重打包](../../apis/sgl_kernel_npu/sgl_batch_matmul_transpose.md)
