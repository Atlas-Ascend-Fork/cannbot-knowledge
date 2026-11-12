---
type: Optimization
title: SGLang 昇腾 GGUF 的加载反量化与显存预估
description: 解释 GGUF 在 NPU 上加载到全精度驻留权重、fused shard 顺序和专家隐藏维 all-gather 的代价。
tags:
- task.optimization
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/gguf.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/standard_dispatch.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/activation.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/fused_moe_triton/layer.py
  role: implementation
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:35:53Z'
platforms: []
---

# SGLang 昇腾 GGUF 的加载反量化与显存预估

## 文件量化与驻留精度

NPU GGUF 支持 Linear、Embedding 与 FusedMoE，但此实现不是 GPU 的量化 GEMM：量化 payload 分支在加载时拷到 CPU，通过 gguf reference dequantize，再把目标 params_dtype 权重搬回 NPU；Linear 缓存 dequantized_weight 并删除 qweight/qweight_type。若 GGML 类型为 F32/F16/BF16 且 qweight 已为浮点 Tensor，则直接令 dequantized_weight 引用 qweight 后返回，不执行 CPU 反量化、不转 params_dtype，也不删除这两个属性；推理执行 `x @ weight.T`。Embedding 同样读取反量化后的权重。

fused QKV 必须按 q、k、v 的逻辑输出顺序拼接，各 shard 可能有独立 GGML 类型、byte offset 和 block size；不能按 checkpoint 到达顺序盲目拼接。MoE 逐 expert 反量化为常驻权重并格式转换，使用 NPUUnquantMoEMethod。moe_tp_size>1 时 w1/w3/w2 均沿输出轴分片：本地 w1/w3 拼成 w13，其中间输出维已分片；w2 保留完整中间输入维并分片隐藏输出维。activation 的 TP all-gather 用于恢复供 w2 消费的中间激活，finalize 的额外 hidden-dim all-gather 恢复隐藏输出；不能按完整 w13 中间维估算每卡权重。

## 场景、成本与验证

适用于希望直接加载 GGUF 文件并复用 reference 格式支持的场景。若出现“文件很小但 NPU OOM”或启动时间长，检查 CPU 反量化、临时副本、全精度常驻权重与额外 all-gather；不要按 GGUF 文件大小估算推理显存。

验证导出类型、各 shard 的 logical shape/offset、目标 dtype 与全精度结果；分别记录启动峰值和稳态显存、TP 通信时间。更换真正的 NPU 量化推理格式需重新导出并匹配其 scheme，不能仅替换 GGUF 类名。当前摄入不把 reference 实现的正确性描述等同于本模型实测通过。
