---
type: Optimization
title: SGLang 昇腾 Qwen MoE 的 shared gate 与 DeepEP 双流
description: 说明 shared sigmoid broadcast、图模式中的 NPU overlap、空 rank collective 和缩放责任。
tags:
- task.optimization
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen2_moe.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/cmo.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:35:53Z'
platforms: []
---

# SGLang 昇腾 Qwen MoE 的 shared gate 与 DeepEP 双流

## shared 与 routed 的分工

Qwen MoE 的 NPU shared expert gate 用 sgl_kernel_npu fused_sigmoid_mul_broadcast，gate 来自独立 projection。普通 forward 的 GPU fused_gate_sigmoid_mul_add 明确排除 NPU；不能把两个融合名称当同一计算流程。

DeepEP 路径在 NPU、SGLANG_NPU_USE_MULTI_STREAM 且 forward_mode.is_cuda_graph 时，将 cloned hidden states 交给 independent shared stream。routed experts 在主路径执行，尾部 wait_share_stream 后才把 shared_output 加入结果。这里的 is_cuda_graph 是框架模式名，在 NPU 仍作为守卫；不能省略图模式条件。

空 DP rank 跳过 gate/shared MLP，但构造 empty TopK 并调用 experts 参加 AllToAll collective。deferred finalize 不接受 M=0，并要求 shared output；这些是更窄路径的前提，不是所有 Qwen 空批次都失败。

## 优化与验证

目标是重叠 shared 计算与 routed 通信/计算；代价是输入 clone、side stream 生命周期及额外事件。先确认实际 graph 模式、shared gate、dtype 与副流等待，再比较开关两边的 logits、空 rank 和端到端尾延迟。诊断 SGLANG_TRACE_QWEN_MOE_DEEPEP_E2E 会同步 stage，只用于定位，不应将该模式时延作为正常性能。关闭多流并重建图可回退；本次未实测加速。

## 相关机制

- [SGL sigmoid 门控的逐元素与逐行广播接口](../../apis/sgl_kernel_npu/sgl_sigmoid_mul.md)
