---
type: Optimization
title: Qwen3-Next A3 Prefill CP+TP：SGLang 分层并行与 PD 边界
description: 固定 Qwen3-Next 实践对 Gated Attention 使用 CP+TP、GDN 保留 TP；记录 SGLang 通信域复用、ZigZag 与 PD 分离限制，区分 README 部署要求和 patch 校验。
tags:
- task.optimization
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage6/0001-support-gdn-cp.patch
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/sgl_kernel_npu_support_gdn_cp.patch
  role: implementation
created_at: '2026-10-20T12:16:14Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      objective:
      - latency
      - ttft
      - memory
      context_length:
      - long_context
      - ultra_long_context
      model_features:
        all_of:
        - moe
      parallelism:
        all_of:
        - cp
        - tp
      deployment_topology:
        all_of:
        - pd_disaggregated
      framework:
      - sglang
---

# Qwen3-Next A3 Prefill CP+TP：SGLang 分层并行与 PD 边界

## 条件与规则入口

本案例补充[长序列 CP 决策](../rules/long_seq_prefill_context_parallel.md)，限定当前选定来源的 Qwen3-Next / Atlas A3 / SGLang Prefill，部署边界按该提交的 PD 分离说明核对。不能继承 DeepSeek/Kimi 的整域 CP 参数。

## 分层切分与布局

官方优化文档对 Gated Attention 使用 CP+TP，将序列分给 CP rank、head 交给局部 TP；GDN 涉及沿序列的卷积，固定实践保留 TP。文档中的 `4CP × 2TP`、64K 输入只是说明例子，不是统一推荐配置。

stage4 patch 使用 CP 通信域与 `dp_size = max(server_args.dp_size, server_args.cp_size)` 等布局逻辑。`CP_USE_ZIGZAG=1` 对应面向长序列单 batch 的负载均衡路径，包含 `linear_to_zigzag_all_to_all`、`zigzag_to_linear_all_to_all` 和 KV 汇聚后的重排。多 batch 的收益需要另行验证，此处不据此断言多 batch 不受支持。只设置环境变量不能证明所有模块或任意负载均获益。

## 部署说明与代码校验分别核对

README 说明：CP 只在 PD 分离场景开启，P/D 卡数相同，P 可增加 CP；要求 `cp_size < tp_size`，并且 CP 与独立 DP 不同时开启，因为 CP 复用了 DP 域。这里的启动参数 `tp_size` 不能与图示中每个 CP rank 内的局部 TP 因子直接混用。

patch 的 `ServerArgs` 在 `cp_size > 1` 且不是 Decode 模式时设置 `enable_dp_attention=True`，并断言 `tp_size % cp_size == 0`。这是内部布局开关，不推翻 README 的 CP 与独立 DP 部署限制；这个断言也没有完整表达 README 的所有要求。不能仅凭通过该断言声称任意 PD 拓扑均受支持。

## 收益与验证边界

文档给出降低激活压力与控制 TTFT 的目标，没有隔离 CP 的独立 before/after。本次只阅读固定 patch 的相关新增函数与入口，没有应用 patch、闭合完整 SGLang 运行调用图或运行模型。验收需检查部署参数、KV 传输、序列与位置重排、Gated Attention/GDN 输出、TTFT、显存及通信耗时。回退按对应版本恢复合法部署配置，不能照搬另一案例的 `cp_size=world_size`。
