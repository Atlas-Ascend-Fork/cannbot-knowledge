---
type: Optimization
title: SGLang 昇腾 EPLB 的地址稳定迁移与 staging 流水
description: 说明 TP=EP=WORLD 前提、参与 rank、非 ND/NZ 临时转换、事件限流和权重先于映射提交。
tags:
- task.optimization
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/eplb.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/eplb/expert_location_updater.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/eplb/expert_location_dispatch.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-08T12:01:09Z'
platforms: []
---

# SGLang 昇腾 EPLB 的地址稳定迁移与 staging 流水

## 场景与前提

动态 expert placement 变化时需要搬运已量化、可能为 NZ 格式的 expert 权重，并保持图中引用的参数地址有效。NPU 专用 updater 要求 TP=EP=WORLD；不能把一般 EPLB 支持推断成任意 TP×EP 组合可用。

非 elastic 情况只迁移全局 placement 有变更的 layer，但本 rank 即使本地槽位未变，也可能是其他 rank 的源专家，仍须参与。所有选中 chunk tensor lists 的数量、shape、dtype、device 与是否需要 staging 都必须一致，连跳过实际写入的 rank 也要验证。

## 格式、地址与顺序

非 ND 或非 contiguous 权重先转 ND contiguous staging，搬运后恢复原格式，再 `copy_` 回原 tensor，保留 graph address；不能用新 Parameter 替换。按 layer 释放 ND 暂存，以两层事件队列限制异步排队分配，复用临时 buffer。通用迁移层等待请求完成后才 copy-back，更新权重后再提交 expert_location metadata，避免新映射读到旧权重。

## 验证、成本与回退

检查迁移前后 data_ptr、格式、逐 expert checksum 与逻辑 ID canary；覆盖本地不变但需要发送、跨节点和量化 scale 一起迁移。迁移会占用额外 staging、通信与同步时间，负载均衡收益必须大于这些成本。关闭动态更新并重载稳定 placement 是回退方式；不能把仅更新元数据当成完成迁移。本次未在多 NPU 上执行验证。
