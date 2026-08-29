---
type: Runbook
title: 多机集合通信 HCCL_BUFFSIZE too SMALL —— 调大且各 rank 一致
description: 多机集合通信 HCCL_BUFFSIZE too SMALL —— 调大且各 rank 一致。昇腾多机多卡推理日志出现关键字： HCCL_BUFFSIZE is too SMALL, ..., NEEDED_HCCL_BUFFSIZE..., HCCL_BUFFSIZE=200MB, ... HCCL 通信缓冲区默认（200MB）不足以承载当前部署所需的 buffer。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/93
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# 多机集合通信 HCCL_BUFFSIZE too SMALL —— 调大且各 rank 一致

## 信号

昇腾多机多卡推理日志出现关键字：

```
HCCL_BUFFSIZE is too SMALL, ..., NEEDED_HCCL_BUFFSIZE..., HCCL_BUFFSIZE=200MB, ...
```

HCCL 通信缓冲区默认（200MB）不足以承载当前部署所需的 buffer。

## 触发条件 / 根因

多机多卡集合通信（大 [EP](../../concepts/parallelism/expert_parallel.md) dispatch/combine、CP 等、长序列）所需 HCCL buffer 超过默认 `HCCL_BUFFSIZE`。根因即环境变量 `HCCL_BUFFSIZE` 设定的通信缓冲区偏小、不满足 `NEEDED_HCCL_BUFFSIZE`。

## 修法

```shell
export HCCL_BUFFSIZE=<实际需要的大小>   # 单位 MB
```

**所有 Rank 上该环境变量须保持一致**。具体所需值视部署（EP 规模 / 序列长）而定，无固定数值；参数含义见昇腾 CANN 环境变量文档 `HCCL_BUFFSIZE`。

## 适用边界

这是昇腾 HCCL 通用失败签名，在 [Kimi-K2-Thinking](../../concepts/models/kimi_k2_thinking.md) 多机（大 EP，Atlas A3 集群，`bash infer.sh` 多节点同步拉起）部署上下文记录，适用面为昇腾多机集合通信，不限该模型。多机/多进程 DP+EP MoE 集合通信一致性对齐见 [multimachine-dp-ep-moe-collective-alignment](../../guides/experience/interventions/multimachine_dp_ep_moe_collective_alignment.md)。

## Evidence

- `diff 事实`（@da13d66）：`models/kimi-k2-thinking/README.md` 附录 FAQ 记录该报错关键字与修法（含"所有 Rank 上该环境变量须保持一致"），为该 PR 新增、由维护者写入。未附具体所需 buffer 数值。
- 溯源下探：[cann-recipes-infer-pr-93-feat-support-kimi-k2-thinking](https://gitcode.com/cann/cann-recipes-infer/merge_requests/93)

<!-- cannbot:related:start -->
## 相关

- [多机/多进程 DP+EP MoE 推理的集合通信一致性对齐（phase 对齐 + 变长换定长）](../../guides/experience/interventions/multimachine_dp_ep_moe_collective_alignment.md)（`related`）：多机大 EP 的 HCCL buffer 不足另见 ［hccl-buffsize-too-small］(../../../runbooks/runtime/hccl_buffsize_too_small.md)。；多机多卡集合通信（大 ［EP］(../../concepts/parallelism/expert_parallel.md) dispatch/combine、CP 等、长序列）所需 HCCL buffer 超过默认 `HCCL_BUFFSIZE`。。部署指南把多机大 EP 的通信缓冲不足明确分流到该运行手册，后者给出容量诊断与各 rank 一致配置步骤。
- [MoE dispatch/combine 算子报错或大 batch 失败：HCCL 通信 buffer 不足，须按模型显式放大 HCCL_BUFFSIZE](moe_dispatch_combine_hccl_buffsize.md)（`same_topic`）：默认 HCCL buffer 对 MoE 全量 dispatch/combine 太小。；根因即环境变量 `HCCL_BUFFSIZE` 设定的通信缓冲区偏小、不满足 `NEEDED_HCCL_BUFFSIZE`。两卡都定位同一通信缓冲不足，MoE 卡补充 dispatch/combine 需求公式与注入路径，通用卡给出多机 rank 一致的处置边界。
<!-- cannbot:related:end -->
