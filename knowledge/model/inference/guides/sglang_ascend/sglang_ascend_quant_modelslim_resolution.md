---
type: Guide
title: SGLang ModelSlim 名称映射与混合投影量化
description: 说明 ModelSlim 配置别名、FLOAT 回退、w13/w2 独立 scheme 与反量化偏置对 RMSNorm 的影响。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/modelslim.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/README.md
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_utils.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:34:34Z'
platforms: []
---

# SGLang ModelSlim 名称映射与混合投影量化

## 从 checkpoint 到 layer

ModelSlim 读取 `quant_model_description.json`，兼容 `block_sparse_moe`/`mlp` 与 `model.language_model`、`language_model`、`visual` 前缀。DeepSeek V4 和 DSpark MTP 命名还有专门重映射；新增别名保留原始 key，但冲突策略不同：block_sparse_moe→mlp 直接赋值，会覆盖原有同名 mlp 配置；DSpark MTP 先合并生成别名、后合并原配置，才保证显式配置优先。不能把任意陌生 checkpoint 名称视为已兼容。

Dense 的直接 fused 配置优先于 packed-module shard 推导。精确 `FLOAT` 或所有 fused shards 都是 `FLOAT` 才回退全精度；同一 fused layer 混合 FLOAT 与量化 shard 会失败。未识别 Dense scheme 可告警后回退；MoE 缺失或不支持的 scheme 则失败，应区分这两类信号。

MoE 从 expert 0 的 gate/up/down 或 w1/w3/w2 配置构造两组 scheme：gate 与 up 必须一致，w13 与 w2 可以采用不同量化方式。先创建两组 kernel，再创建 Ascend runner，防止 runner 过早缓存错误的激活与 scale 约定。

## Norm 偏置与验证

配置出现 `norm.bias` 会启用 RMSNorm 的 NPU 反量化偏置路径：初始化偏置，标记 `ignore_anti=True`；残差路径调用 add-rmsnorm-bias，非残差路径调用 RMSNorm 后加 bias。这里没有因此增加激活量化。

适配新权重先核对 prefix 命中和参数名，再逐项比较 w13/w2 scheme、scale/offset/scale_bias/weight_bias 是否正确加载。回退应重新加载原始全精度 checkpoint，不能删除必要的补偿 bias。Attention 的 Q/KV FP8 scheme 有独立的池和层一致性约束，本卡只承载 Linear、MoE 与 Norm 分派。

## 下层接口参考

- [SGL 残差 RMSNorm 与 bias 接口](../../apis/sgl_kernel_npu/sgl_add_rmsnorm_bias.md)
