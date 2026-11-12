---
type: Guide
title: SGLang 昇腾 W8A8 MoE 的 INT8 通信与专家计算
description: 连接 ModelSlim channel scale、INT8 dispatch、双 GMM 动态量化和 FuseEP 权重预处理。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_w8a8_int8_moe.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_methods.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/standard_dispatch.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/utils.py
  role: implementation
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:34:34Z'
platforms: []
---

# SGLang 昇腾 W8A8 MoE 的 INT8 通信与专家计算

## 权重、通信与执行

W8A8 expert 权重为 INT8 `[E,N,K]`，ModelSlim scale/offset 创建为 FP32 `[E,N,1]`，w13 的 N=2I、w2 的 N=H。普通 GMM 路径加载后对权重转置、contiguous；仅满足转换条件时采用 NZ。SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT 开启、CPU/meta 存储或 NZ 对齐不满足时返回原张量、保留 ND；INT8 要求转置后末两维分别16、32对齐。因此 NZ 不是所有加载后权重的必然表示。scale 转 BF16 后 squeeze；这些是加载后的表示，不能要求 checkpoint 本身已采用同一布局。

kernel 声明 INT8 dispatcher 输出，w13 接收 payload 与 per-token scale。已有 scale 时复用量化输入，缺失 scale 时才做动态量化；激活后再次量化供 w2 使用。通信 dtype 由 kernel 与 dispatcher 共同协商，不能因 NPU 默认 BF16 就推断所有 W8A8 通信仍为 BF16。

## 适配步骤与边界

先检查 w13/w2 scale 和 offset 是否随 expert/TP 分片正确加载，再核对 dispatch 输出的 INT8 payload、scale 与 expert counts。FuseEP 后端采用另一套权重重排，一次性 guard 防止 w13/w2 被重复处理；不能把其布局交给普通 Ascend GMM 路径。

验证应覆盖零 token expert、实际 top-k 分布、两次 GMM 和最终 weighted combine，并对同输入全精度结果计算误差。切换通信后端需重新构造 layer 和加载权重，不宜在线改一个 flag 后复用预处理后的存储。型号范围未在本方法整体声明，本卡保持 draft，未作上游测试或性能收益声明。
