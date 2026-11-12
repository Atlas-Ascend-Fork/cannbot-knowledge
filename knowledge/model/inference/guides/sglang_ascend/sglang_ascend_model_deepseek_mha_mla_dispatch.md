---
type: Guide
title: SGLang 昇腾 DeepSeek 的 MHA、MLA 与 DSA 模型分派
description: 连接 prefill/decode 模式、NPU prepare/core 配对、CP latent KV 重建和共享专家参数。
tags:
- task.implementation
- topic.attention
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_v2.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_common/attention_backend_handler.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_common/attention_forward_methods/forward_methods.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_common/attention_forward_methods/forward_mha.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_common/utils.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:20:03Z'
platforms: []
---

# SGLang 昇腾 DeepSeek 的 MHA、MLA 与 DSA 模型分派

## 模式到执行方法

ascend handler 对普通 extend（排除 target_verify 与 draft_extend_v2）选择 MHA_NPU；其他阶段选择 MLA_NPU。use_dsa 时两类阶段均选择 DSA_NPU。forward_prepare 和 forward_core 必须按同一 enum 成对调用对应 NPU 实现，不能只替换 prepare 后沿用 GPU core。

空输入的短路要求 o_proj 不需要 all-reduce，否则会使其他 rank 挂起。MLA latent KV 存储在 NPU 直接传 kv_a 和 k_pe 给 pool store，避免额外 split；CP prefill 先写 rank-local latent，再 gather 成完整序列顺序供 Ascend sparse attention 读取。通用 CUDA DCP metadata 函数在 NPU 返回 None，不能据此断言 NPU 不支持 DCP，它使用专属后端 metadata。

## MoE 与权重边界

包含 ascend_ops、ascend_fuseep 的 A2A 路径把未融合 shared experts 设为 replicated，以匹配通信后的 token 布局；有 swiglu_limit 的 NPU Dense/shared MLP 调用 npu_clipped_swiglu，必须保留 alpha=1、bias=0、非交错 gate/up 语义。共享专家融合改变总 expert 数和 TopK 槽数，loader 的 shared-expert remap 必须一致。

验证 prefill、decode、verify 和 CP 四类路径的 enum、KV slot、q/k shape、空 rank 与 logits。AWQ 的 NPU dequant helper 使用 decomposition 版本，不能套 CUDA kernel。底层 attention/quant 卡负责其接口约束，本卡只承载模型分派与状态关系，未运行上游。
