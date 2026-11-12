---
type: Concept
title: SGLang 昇腾 TopK 的物理专家映射与 padding 统计
description: 说明 NPU router 分支、biased selection/unbiased weight、共享槽保留及 padding 对通信容量和
  EPLB 的影响。
tags:
- task.implementation
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/topk.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/topk.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/hash_topk.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/eplb/expert_distribution.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/eplb/expert_location_dispatch.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:30:33Z'
platforms: []
---

# SGLang 昇腾 TopK 的物理专家映射与 padding 统计

## 路由选择与模型语义

NPU sqrtsoftplus router 使用 norm_type=2；bias 参与 expert 选择但权重来自未加 bias 的分数。排除 sqrtsoftplus 后，优先判断无分组且无 bias：满足时直接走 gating_top_k_softmax，即使配置 sigmoid 或存在 padding 元数据也不改变这一优先级。只有未命中该分支、且存在 bias、sigmoid 或 num_token_non_padded 时才走 npu_moe_gating_top_k；分组、无 bias、softmax 且无 padding 元数据时回退 select_experts（torch-native）。renormalize 与 routed_scaling_factor 必须按模型配置处理，不能重复缩放。

逻辑→物理映射只作用于 routed expert 槽，末尾 shared slots 保留其独立语义。无 A2A 的复制路由需要各 rank 一致选择 physical replica；dynamic/fake 算法在 rank_invariant=True 时使用 token-row modulo replicas，False 时使用随机副本。static 算法直接查预先计算的映射表，不做逐 token 取模。

## padding 与统计

NPU 对图 padding 行保留有效 expert IDs 并把权重清零；强行把 IDs 全改零会集中占用 expert 0 容量。给 EPLB recorder 的副本单独把 padding IDs 置 -1，确保统计只含有效 token；在排除 per_token 和 stat_approx 等先行分支后，NPU DeepEP normal、LL、auto 使用 masked TopK 统计。stat_approx 且 DeepEP normal 先选 _DeepepNormalSinglePassGatherer，使用 dispatch counts，不享有这里按 masked TopK 排除 padding 的保证。HashTopK 还把权重转 FP32，并在共享槽/Waterfill 修改后再次清 padding 权重。

验证实际 dispatch 的 ID 有效性、padding 权重全零、shared slots 是否被误映射，以及 recorder 的有效路由总和。EPLB 的 fake 算法只有经过 select_experts 中 transform_select_experts_inputs 的路径才会改写 logits/bias；通常的 NPU forward 直接调用 fused_topk_npu，其融合分支不调用该变换，回退到 select_experts 时才会执行。fake 是诊断工具，不能作为线上优化开关。性能和负载均衡结论需真实请求分布验证，本卡未执行相关实测。
