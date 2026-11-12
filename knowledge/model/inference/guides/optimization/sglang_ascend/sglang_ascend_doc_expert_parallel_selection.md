---
type: Guide
title: SGLang 昇腾 EP 模式与分轮通信配置的文档边界
description: 按混部和PD角色选择DeepEP/fuseep，保留融合范围、EPLB、EP/TP和缓冲公式的适用限制。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/expert_parallelism.mdx
  role: primary
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/advanced_features/expert_parallelism.mdx
  role: primary
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-08T12:09:58Z'
platforms: []
---

# SGLang 昇腾 EP 模式与分轮通信配置的文档边界

## 选择通信与计算路径

两仓NPU专节建议混部DeepEP auto，PD P端normal、D端low_latency；ascend_fuseep把dispatch到combine之间的MoE计算通信融合。页面仍写fuseep仅用于PD decode，但同快照MiniMax等最佳实践在混部启用fuseep，所以该限制不能推广为所有当前实现。来源同时将moe-runner-backend视作无需配置；实际量化、LoRA和runner组合应按固定实现核对。

当前通用EP段将DeepEP/fuseep限制为EP=TP，EP<TP只有none；旧文档只对DeepEP/Mooncake作此声明。不要把none基于allreduce/allgather的路径和真正all-to-all视为相同成本。支持矩阵又指出fuseep与EPLB不兼容，单项EPLB支持不证明此组合可用。

## 分轮 dispatch/combine

NPU专节用per-round-tokens和round控制长序列dispatch，combine另有独立enable开关，不能因dispatch分轮就假设combine也分轮。来源默认8192 token、1轮、combine关闭，建议大于8192时评估两阶段分轮；这些是该文档快照值，不是全部sgl-kernel-npu版本的默认契约。

其HCCL buffer估算在分轮时含两倍(102MB+4MB+round_tokens×3×hidden_size×routing_topk)再加padding，不分轮时用total_seq×2×hidden_size×topk，建议padding≥20。公式混用MB与元素乘积，且未完整交代dtype/对齐；只能当历史配置提示，**不能直接当字节正确的通用预算公式**。应依据实际kernel版本、workspace/dispatch容量与HBM分配重新计算，避免把DEEPEP_HCCL_BUFFSIZE和普通HCCL_BUFFSIZE混为一池。

两页只称NPU，没有具体产品支持证据，因此本卡draft空平台。本次没有运行通信或测收益。已有DeepEP源码文档卡可用于生命周期和句柄核对；本卡只保留SGLang使用者的选型与来源冲突。

## Evidence

- [sglang：docs/docs/advanced_features/expert_parallelism.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/expert_parallelism.mdx)（primary）
- [sgl_docs：docs/advanced_features/expert_parallelism.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/advanced_features/expert_parallelism.mdx)（primary）
