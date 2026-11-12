---
type: Guide
title: SGLang 昇腾 LoRA 的 SGEMV、批次元数据与图边界
description: 说明 Ascend LoRA shrink/expand、融合投影、adapter 元数据、Embedding 限制和 DP/prefill
  graph 排除条件。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/lora/backend/ascend_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/lora/backend/lora_registry.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/lora/backend/base_backend.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/lora/lora_manager.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/moe_runner/runner.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/lora/lora_moe_runner_marlin.py
  role: implementation
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:35:29Z'
platforms: []
---

# SGLang 昇腾 LoRA 的 SGEMV、批次元数据与图边界

## 执行链与输出累加

LoRA registry 中 `ascend` 延迟加载 AscendLoRABackend。shrink 调用 `torch.ops.npu.sgemmv_shrink`，创建清零 FP32 中间结果，按 adapter 的 rank、scale、indices 与 sequence seg_lens 计算；expand 把输入转 FP32，已有 base_output 时原地累加，否则按输入 dtype 分配零结果。QKV 三段和 gate/up 两段共享完整 FP32 中间缓冲，通过输出 offset 分片展开；本集成没有采用 SGEMMC。

Embedding LoRA 不支持 extra_embeddings/新增 token；input IDs clamp 到原 vocab 范围，每 sequence 的 adapter index 依 seg_lens 展开到 token，再按 rank mask 和 scaling 处理。不能据此向 adapter 提供额外词表 token。

## 元数据与图执行

decode 图捕获预分配 max-bs 的静态元数据：INT32 seg_lens/indices/ranks 与 FP16 scalings，固定每 request token 数；每批从 pinned CPU buffer 非阻塞拷贝。eager extend 使用真实 sequence 长度，并从 CPU 元数据推导最大长度，避免额外 D2H。批量 adapter 切换必须先刷新元数据再使用 graph。

继承的 supports_prefill_cuda_graph 与 supports_dp_attention 均为 False，Ascend backend 没有覆盖；manager 因此拒绝相应 DP attention 组合，不能宣称 prefill graph 可用。公共 MoE runner 的 LoRA hooks 除 Triton 外，还在 marlin 且 lora_enabled 时创建 MarlinLoraRunnerCore，并通过 DispatchMoeRunnerCore 传入 hooks，实际执行 after_gate_up/after_down。Ascend expert runner 当前未接入，不能用其他 runner 的 hooks 支持推断 Ascend MoE LoRA 已接通。

验证单/多 adapter、不同 ranks、seg_lens、base_output 累加及 decode replay；模型级结果应与逐请求 LoRA 参考比较。图元数据、FP32 scratch 和拷贝都有成本；回退可重建为 eager 或禁用 adapter。具体芯片范围没有完整证据，保留 draft，未执行真机测试。

## 下层接口参考

- [SGL LoRA shrink 接口](../../apis/sgl_kernel_npu/sgl_lora_shrink.md)
- [SGL LoRA expand 接口](../../apis/sgl_kernel_npu/sgl_lora_expand.md)
