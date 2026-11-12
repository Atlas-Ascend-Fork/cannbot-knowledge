---
type: Guide
title: SGLang 昇腾 LLaDA2 的路由与 QKV 融合限制
description: 说明 NPU 禁止 expert_capacity block routing、关闭重复 renorm，以及带可选 bias 的位置缓存融合。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/llada2.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/overrides.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/topk.py
  role: implementation
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:35:32Z'
platforms: []
---

# SGLang 昇腾 LLaDA2 的路由与 QKV 融合限制

## NPU 路由守卫

LLaDA2 在 NPU 强制 norm_topk_prob=False：源码注释以先norm后scale避免再次renorm作为动机，但实际须区分NPU TopK分支：无分组且无correction_bias的softmax快路径不传递或应用routed_scaling_factor；另一npu_moe_gating_top_k分支才传入该缩放（受apply_routed_scaling_factor_on_output控制）。不能把该动机推广为所有NPU路由已完成缩放的保证。expert_capacity 非空会启用 block routing，但 NPU 明确抛 ValueError，要求 unset；不能把通用 block routing 的 group/capacity 检查通过等同于 NPU 支持。

模型只接受 SiLU，仅在显式设置score_function（非None）时校验score/bias组合为softmax+无bias或sigmoid+有correction_bias；默认None不执行这项组合断言；grouped top-k 和 shared expert 的 backend 分组仍独立处理。NPU 将 routed scale 融合标志与实际 experts 的需要关联，避免后续重复缩放。

## Attention 准备与验证

NPU 且融合符号存在时，split_qkv_rmsnorm_rope_pos_cache_half 读取 positions 和 cos_sin_cache，按 use_qk_norm 传 eps/weight/bias，保留 rotary_dim，并标记不能再融合 set KV。否则显式 split/norm/RoPE，只有符合条件的另一条路径才自行写 KV，attention 的 save_kv_cache 要对应。

配置应先去除 NPU 不支持的 expert_capacity，再检查最终 DLLM attention backend 的解析结果；算法 required backend 优先于一般 fallback ascend。验证 diffusion step 的 TopK weights、QK/bias、KV 保存次数和完整 logits，回退到明确 unfused 准备但保留 norm/scale。当前卡未执行 diffusion 推理或报告吞吐结果。
