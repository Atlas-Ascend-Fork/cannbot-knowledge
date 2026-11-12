---
type: Guide
title: SGLang 昇腾 MXFP8 专家的离线布局与在线 runner
description: 连接 ModelSlim E4M3/E8M0 权重、在线 MXFP8 expert、NZ 转置和 normal/low_latency 通信约定。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_mxfp8_moe.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_methods.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/online_moe_methods.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/fp8.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-08T12:01:09Z'
platforms: []
---

# SGLang 昇腾 MXFP8 专家的离线布局与在线 runner

## 相同计算后端的两种权重来源

ModelSlim 离线 scheme 对 w13/w2 分别创建 E4M3 `[E,N,K]`、uint8 E8M0 `[E,N,K/32]`，offset 注册为 None；E4M3 dtype 触发只重排分支。在线方法从未量化 BF16/FP16 权重生成相同 MXFP8 表示。两者共用 `NPUMXFP8MoEMethod`，不能给已量化权重再次做在线量化。

权重需先做 NZ cast 再转置，scale 配为 `[E,K/64,N,2]`，二者保留匹配的 transpose flag；随意 contiguous 会改变期望的转置描述。已提供激活 scale 则复用，缺失时动态 MXFP8 量化。

## 激活与通信条件

plain SwiGLU 可走融合 gmm1；正 swiglu_limit 会保留显式 w13→限幅激活→再量化，SiTU 也不能误走 plain SwiGLU 融合。DeepEP 的在线/ModelSlim MXFP8 默认 BF16 dispatch，其余组合可由 kernel 指定 MXFP8，最终还受模式 override 与显式 CLI 优先级控制。

在线 MoE 只接受 auto/ascend runner，GPU FlashInfer 的 w31 权重顺序与这里 w13 不兼容。验证时核对 gate/up 顺序、scale byte、每种通信模式和限幅模型输出；源码性能注释不作为本卡测量结果。具体 950 算子能力不推广为所有 NPU 上整体 MXFP8 特性支持，保留 draft。
