---
type: Guide
title: SGLang ModelSlim 离线 MXFP4 Dense 的 W4A8 与 W4A4
description: 区分同样 packed FP4 权重的两种激活精度、32 元素 scale、TP 打包维度和单层 matmul 参数。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_mxfp4_w4a8.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_mxfp4.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/linear_method_npu.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:35:29Z'
platforms: []
---

# SGLang ModelSlim 离线 MXFP4 Dense 的 W4A8 与 W4A4

## 离线权重契约

ModelSlim 的 W4A8_MXFP 与 W4A4_MXFP4 都加载 uint8 packed FP4 权重 `[N,K/2]`，每字节两个值，uint8 原始 E8M0 scales 为 `[N,K/32]`。parameter 的 input_dim 描述的是已减半的 packed 维度，TP loader 必须按 packed 权重解释分片，不可再除一次 pack factor。

两者的激活不同：W4A8 使用动态 E4M3 MXFP8，权重先 NZ cast 再转置，scale 配成 `[K/64,N,2]`，group_sizes 为 `[0,0,32]`；W4A4 的激活也动态量化成 FP4，单层 scale pairs，显式 x1/x2 dtype 为 FP4，group_sizes 为 `[1,1,32]`。离线 W4A4 不使用在线 mxfp4 配置的双层 L0/L1。

## 适配与验证

先核对 quant_model_description 中的精确 scheme 名、packed uint8 权重和 scale 字节，再交由匹配的 kernel 后处理。比较 TP 分片前后的逻辑 K/N、scale 个数以及首末 block；不能用 FP32 数值转换替换 scale 的 byte view。

W4A8 的 FP4 matmul 还依赖 torch_npu 构建兼容性。来源 NPUMXFP4W4A8OfflineLinearMethod 注释记录较旧版本如 2.10.0.dev20260320 在 prefill 拒绝 NZ 权重（x2 ... nz format, but it is 2），并称 2.10.0.post1.dev20260624 及以后可运行该 FRACTAL_NZ 路径；遇此错误应升级并验证 torch_npu，而不是把权重改成 ND。这是来源版本警示，本次未独立复测，当前环境仍须验证 prefill/实际 NZ 布局兼容性。排查 accuracy 问题时分别锁定激活量化、权重导出和 NZ/transpose 顺序。恢复应重新加载相应离线 checkpoint 及匹配 scheme，不能在 W4A8/W4A4 之间只换方法名。此卡未从通用 NPU 类推全部产品支持范围，保留 draft。
