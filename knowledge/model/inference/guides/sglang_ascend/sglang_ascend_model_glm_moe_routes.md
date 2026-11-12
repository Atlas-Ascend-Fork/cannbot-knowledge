---
type: Guide
title: SGLang 昇腾 GLM MoE 的阶段融合与路由缩放
description: 记录 GLM4 decode QKV 融合、prefill shared overlap、MoELite sigmoid 和 TopK 缩放的不同条件。
tags:
- task.implementation
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/glm4_moe.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/glm4_moe_lite.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/utils.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/forward_mode.py
  role: constraint
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:35:32Z'
platforms: []
---

# SGLang 昇腾 GLM MoE 的阶段融合与路由缩放

## QK 准备

GLM4在NPU调用is_extend_or_draft_extend_or_mixed()时未启用include_draft_extend_v2，因此只有EXTEND、MIXED走split→可选QK norm→RoPE；DRAFT_EXTEND_V2及其他阶段进入split_qkv_rmsnorm_rope融合路径。关闭 QK norm 时 eps、weight、bias 均传 None，起始层刷新 cos/sin。quant tuple 的空行检测读取第一个 payload，不能对整个 tuple 取 shape。

## shared overlap 与缩放

GLM4 DeepEP的NPU shared dual stream要求is_extend()或is_target_verify()且SGLANG_NPU_USE_MULTI_STREAM开启。该快照的is_extend()实际覆盖EXTEND、MIXED、TARGET_VERIFY、DLLM_EXTEND，默认不含DRAFT_EXTEND_V2；普通DECODE也不在该guard中。尾部 wait_share_stream 后依据 routed_scaling_factor 是否已融合到 TopK，决定直接相加还是加权，防止重复缩放。

GLM4MoELite 在 NPU 显式 scoring_func=sigmoid，保留 grouped top-k、correction_bias、norm_topk_prob 与 expert runner 绑定。未量化 MTP 要 Standard TopK output，不能把 target 的 bypassed 输出格式直接复用；shared expert 是否 replicated 取决于对应 backend。

适配时分开记录 GLM4 与 Lite 的 forward mode、score、scale 和 shared 分组。验证 prefill、decode、target_verify、空 rank、带/不带 QK norm，逐级比较 TopK、shared/routed 和最终 logits。回退到单流 native prepare 时仍保留模型路由语义。本卡无整体产品范围或性能测量。
