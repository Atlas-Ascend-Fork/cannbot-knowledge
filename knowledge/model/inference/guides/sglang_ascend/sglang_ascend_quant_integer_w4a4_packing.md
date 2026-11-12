---
type: Guide
title: SGLang 昇腾整数 W4A4 的新旧 packing 与分片
description: 区分整数 W4A4 与 MXFP4，说明 packing 环境变量、Dense/专家参数形状及 scale 位编码。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_w4a4_int4_moe.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_w4a4_int4.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_methods.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_method_npu.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/linear.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:35:29Z'
platforms: []
---

# SGLang 昇腾整数 W4A4 的新旧 packing 与分片

## 新旧打包是加载契约

整数 W4A4 使用 INT4 权重和 quint4x2 激活，不是 OCP MXFP4。`SGLANG_NPU_W4A4_NEW_PACKING` 同时改变权重创建、loader 的 pack_factor 和 kernel 后处理。新方案会压缩相应权重维度，Dense parameter 标记 input_dim=1、output_dim=0、pack_factor=2，并没有设置 packed_dim；MergedColumnParallelLinear 在新 packing 环境变量分支使用 pack_factor 调整 TP shard offset/size，这与另一个读取 packed_dim 的分支不同。

MoE 后处理对 scale 作 FP32 bitcast 到 unsigned32，再存入 INT64 容器，offset squeeze；权重经对应 nibble packing、transpose/NZ 和 INT32 view。Dense 也根据同一变量选择直接 INT32 view 或 `npu_convert_weight_to_int4pack`。环境变量与导出布局不一致时，即使元素总数可 reshape 也不证明权重正确。

## 使用与验证

expert dispatch 保持 BF16，GMM 内本地动态量化成 quint4x2；不要因为 W4A4 就请求 INT4 wire format。先核对 checkpoint 打包格式，再在加载前固定环境变量，分别检查 w13/w2、Dense fused shards 的逻辑 K/N 和 scale bit pattern。

验证 TP=1 与多 TP 的完整层输出及模型 logits，尤其关注 gate/up 分片边界；回退必须重载旧格式匹配的 checkpoint 或全精度权重，不能在已后处理 layer 上翻转变量。该机制有存储压缩与精度/加载成本取舍，来源没有本次实测收益；产品范围未知，保留 draft。
