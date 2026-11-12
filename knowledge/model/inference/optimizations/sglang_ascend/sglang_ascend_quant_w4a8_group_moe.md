---
type: Optimization
title: SGLang 昇腾 W4A8 MoE 的 group scale 与 clip 分支
description: 说明 packed INT4 权重、INT8 激活、per-channel/per-group scale 编码和 activation_use_clip
  的补偿参数。
tags:
- task.optimization
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_w4a8_int8_moe.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_methods.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/modelslim.py
  role: implementation
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:36:43Z'
platforms: []
---

# SGLang 昇腾 W4A8 MoE 的 group scale 与 clip 分支

## 表示与关键分支

这里 W4 是整数 INT4 打包，A8 是 INT8，区别于FP4/MXFP8。下文per-group/clip是后端类的可选构造分支，不代表常规ModelSlim配置入口已接通：get_moe_scheme只用cls(self, weight_group)实例化，group_size=0、activation_use_clip=False沿用独立构造参数默认值，不从quant_config读取，因此该入口实际为per-channel、无clip。w13 以 INT8 存储 `[E,I,H]`、w2 为 `[E,H/2,I]`，对应逻辑输出通道各乘二。per-channel 及 per-group 的 scale、offset 和 bias 必须按逻辑通道加载，不能套 packed N 形状。

无 clip 的 per-group 路径把 channel scale 与 group scale 相乘，经 FP16 舍入再回 FP32，并把 FP32 bit pattern 按 uint32 配对装入 INT64；scale_bias 还按 group 求和。clip 分支使用导出的 bias 等补偿参数，并有不同 scale 形状。把 INT64 编码用普通 float cast 还原，或丢弃 clip 补偿项，会破坏数值。

加载后权重先转置、NZ cast 再按 INT32 view 打包，最后维需可被 4 整除。dispatcher 使用 INT8；收到 scale 后直接使用 payload，只有没有 scale 才动态量化激活。

## 优化验证与回退

目标是降低 expert 权重与通信负担；代价包括解包/布局要求、scale 元数据及量化误差。先核对实际scheme实例的group_size与activation_use_clip及其构造入口；仅修改quant_config描述不能在当前常规加载入口启用group或clip。若由专门适配显式传入可选参数，再分别检查每个 expert 的 scale/bias、GMM 输出和 logits。不能用关闭 clip 来回退同一套导出权重；应重载匹配方案或全精度权重。当前摄入没有测量带宽或吞吐收益，也没有把后端可选group/clip分支当作ModelSlim常规加载能力，也不外推给所有compressed-tensors分支。
