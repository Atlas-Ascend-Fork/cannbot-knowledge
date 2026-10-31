---
type: Optimization
title: W4A8 Prefill 跳过 bias 规则已停用
description: 最新 V4 的 W4A8 专家两次 GMM 均保留 bias；停用旧 Prefill 跳过 bias 建议，避免遗漏量化补偿。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
status: deprecated
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: primary
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:17:34Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      model_features:
        all_of:
        - moe
---

# W4A8 Prefill 跳过 bias 规则已停用

## 当前结论

最新 V4 的 `experts_w4a8int4` 在两次 `npu_grouped_matmul` 中分别显式传入 `w13_bias` 和 `w2_bias`，不再读取 `is_prefill` 来省略 bias。Prefill 双路由和 Decode 专家计算均不能依据本条历史规则去掉量化补偿项。

## 迁移检查

保留当前权重和 bias 配对，检查实际调用的量化方法与 GMM 参数；比较修改前后的输出精度后再测性能。旧 PR 的加速观测不代表当前实现的收益，本条不再提供可执行的跳过 bias 配方。当前模型与量化条件见[部署流程](../../guides/models/deepseek_v4_deployment.md)及[整数量化](../../concepts/quantization/int8_int4_hybrid.md)。

## Evidence

- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py)（primary）
