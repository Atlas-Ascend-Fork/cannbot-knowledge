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
updated_at: '2026-10-29T15:29:20Z'
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

这是昇腾 HCCL 通用失败签名，在 [Kimi-K2-Thinking](../../concepts/models/kimi_k2_thinking.md) 多机（大 EP，Atlas A3 集群，`bash infer.sh` 多节点同步拉起）部署上下文记录，适用面为昇腾多机集合通信，不限该模型。多机/多进程 DP+EP MoE 集合通信一致性对齐见 [multimachine-dp-ep-moe-collective-alignment](../../optimizations/rules/multimachine_dp_ep_moe_collective_alignment.md)。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/93)（evidence）
