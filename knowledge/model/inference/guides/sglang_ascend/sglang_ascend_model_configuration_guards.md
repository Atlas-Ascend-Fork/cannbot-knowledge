---
type: Guide
title: SGLang 昇腾模型默认后端与量化配置守卫
description: 记录 DSV4 BF16 KV、DSA 跳过 GPU 选择、MXFP8 MoE 保留 Ascend runner 及 DLLM 后端优先级。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/overrides.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/model_overrides/deepseek_v2.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/model_overrides/deepseek_v4.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/fp8.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/online_moe_methods.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/fused_moe_triton/layer.py
  role: implementation
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:34:34Z'
platforms: []
---

# SGLang 昇腾模型默认后端与量化配置守卫

## 启动时解析的真实结果

DeepseekV4ForCausalLM 的通用 KV 默认先设 fp8_e4m3，但 device=npu 会强制改成 bfloat16；这覆盖用户原先的 dtype 选择。DSV4 NPU 保留设备感知的 dsv4 attention backend，prefill/decode 均设 dsv4，page_size=128，不能套其他 NPU 模型默认 ascend 的页布局。

DSA 的 KV dtype 默认和 split-backend resolution 在 NPU 直接返回，跳过 CUDA capability、FlashMLA/TRTLLM 等 GPU 选择；不能把 GPU DSA 默认 FP8 cache 移植到 NPU。

MXFP8 MoE 的 GPU runner 重写也明确排除 NPU。NPU 应保留 auto，由量化方法选 Ascend；固定快照的 NPUMXFP8OnlineMoEMethod.create_moe_runner 只接受 auto/ascend，在模型构造、权重加载之前就拒绝 flashinfer_trtllm 等不兼容 runner。只有绕过该守卫，才存在 loader 交换 w1/w3、装反 gate/up 的潜在风险；intermediate_size_per_partition 的128对齐也仅在尚未对齐时执行，不能描述为每次必然重排。NVFP4 online 仍有 NVIDIA Blackwell 专属守卫，不能因 MXFP4 已有 NPU 分支而泛化。

## DLLM 与验证

DLLM 先遵守算法声明的 supported/required attention backend；未满足这些更高优先级条件时，NPU fallback 设 ascend。部署应记录解析后的 backend、KV dtype、page_size 和实际 quant_method，先用默认合法组合验证 logits，再改变单个参数。参数解析通过不等于模型执行或性能验证；回退需按原配置重新加载权重和 KV 池。本卡未获得整组机制的型号范围，保留 draft。
