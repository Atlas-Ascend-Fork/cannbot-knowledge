---
type: Guide
title: SGLang Ascend DSpark循环：提案、预算验证与状态提交
description: 闭合DSpark从固定gamma草稿到compact/static验证、接受与target hidden注入的NPU模型循环，保留图折叠与线性状态边界。
tags:
- task.implementation
- topic.speculative_decoding
- topic.kv_cache
- topic.graph_execution
- topic.attention
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dspark_components/dspark_worker_v2.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dspark_components/dspark_verify.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_hybrid_linear_attn_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_kda_backend.py
  role: implementation
created_at: '2026-11-08T12:08:04Z'
updated_at: '2026-11-08T12:08:04Z'
platforms: []
aliases:
- DSparkDraftWorker
- commit_target_mamba_states_after_verify
---

# SGLang Ascend DSpark循环：提案、预算验证与状态提交

## 循环与宽度

DSpark先分配verify窗口，再生成gamma个draft proposal，加root形成gamma+1宽的verify ids。预算planner根据confidence和token budget生成每请求verify长度，选择compact ragged或static路线。target hidden返回后只按commit长度注入草稿KV，不能把全部候选hidden提交为历史。

draft scope与target并行域分开，DP attention下通信不能越过正确attention-TP组。NPU豁免某些GPU MoE draft的attn_tp==1限制，但仍受参数hook与实际backend约束；PD prefill不允许盲目捕获decode图。

## 图折叠guard

graph epilogue可在compact或受支持static模式创建，NPU是显式允许的平台分支。fold_eligible还要求proposal已折叠、全greedy、logits调整为no-op、无grammar，以及模拟bonus路径满足相应条件。非贪心即使draft proposal已入图，也回eager accept，不能把折叠贪心结果当采样输出。

compact target输出需scatter回[bs*verify_width,...]才应用每请求logits调整与grammar mask。target graph能否运行以最终ForwardBatch结果为准，提前规划的eligibility不能作为实际重放结果。未来relay、接受tail和deferred commit也各有条件，不能由总开关推导全接入。

## GDN/KDA状态提交

target包含线性状态时，last_correct_step=commit_lens-1，并按prefix track网格选择额外跟踪步，随后调用update_mamba_state_after_mtp_verify同时恢复SSM/conv。NPU若CPU前缀镜像证明本轮最大可能接受宽度都不会跨跟踪边界，可省掉track索引及无意义conv self-copy；未知时不能跳过。

建议逐阶段记录proposal宽、verify budget、layout、fold_eligible/actual graph、commit长度和下一轮状态，覆盖greedy/采样、grammar、DP idle和跨track边界。模拟接受长度只用于实验，不应写成真实接受率。本次没有执行模型、统计或性能测试，芯片兼容保持未知。
