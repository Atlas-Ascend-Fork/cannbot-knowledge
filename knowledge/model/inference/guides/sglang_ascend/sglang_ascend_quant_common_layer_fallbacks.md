---
type: Guide
title: SGLang 昇腾公共层的 Norm、激活与输出适配
description: 区分原生 Norm/激活后端、Gemma provider、Embedding/softcap 回退和 HC/残差输出的 dtype 边界。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/layernorm.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/activation.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/vocab_parallel_embedding.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/logits_processor.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attn_residual.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/layernorm/mhc.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/gemm/kimi_k3.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/elementwise/add3.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/elementwise/mla_output_gate.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-08T12:01:09Z'
platforms: []
---

# SGLang 昇腾公共层的 Norm、激活与输出适配

## Norm 与激活

NPU RMSNorm 的 residual 路径调用 npu_add_rms_norm 并返回归一化输出、更新 residual；无 residual 时调用 npu_rms_norm。Gemma RMSNorm 的权重语义是 `1+w`，不能套普通 gamma。目标 provider 优先；旧 wheel fallback torch_npu 在 A2/A3 的可用性不能扩展到 950，源码明确指出 950 可能缺少此旧算子注册。native 环境分支可用于对照输出，应按对应类的实际条件选择。

SiLU 门控使用 npu_swiglu；GeGLU 可按 native 环境开关或 npu_geglu 的 approximate/activate-left 参数执行。SiTU 与普通 SwiGLU 不是同一激活。新增模型应核对公式、gate/up 方向和舍入，不按相似 API 名替换。

## 公共回退与 dtype

NPU 禁用 fused Triton vocab embedding，执行本地 mask→gather→越界分片置零，再在需要时 TP all-reduce；logits softcap 使用 `cap*tanh(logits/cap)` 的 torch 路径，融合 gather+softcap 明确排除 NPU。Kimi K3 tiny GEMM、add3、MLA output gate 的 CUDA fast path 也排除 NPU，不能列为已实现的 NPU 融合。

attention residual mix 在 NPU 调用 sgl_kernel_npu 的 mix_fused，空 T 直接返回。HC pre 的 NPU custom op 不包含后续 input_layernorm，返回 norm_fused=False；y 转回输入 dtype，而 post/comb 保持 FP32，空/idle 批次的 dummy 也要保留 FP32。

验证应覆盖 residual/no-residual、Gemma 权重、empty batch、TP vocab 边界与 softcap，比较层输出和模型 logits。这里是模型集成守卫汇总，没有完整 Device 分析，亦无跨型号或性能收益推断。

## 下层接口参考

- [SGL attention residual 混合接口](../../apis/sgl_kernel_npu/sgl_attn_residual_mix.md)
- [SGL mHC 前后处理接口](../../apis/sgl_kernel_npu/sgl_mhc_pre_post.md)
