---
type: Guide
title: SGLang Ascend Eagle草稿worker：分阶段后端与图回退
description: 说明draft decode/extend使用独立attention backend和NPU图runner，及动态阶段能力、内存统计和CPU长度依赖。
tags:
- task.implementation
- topic.speculative_decoding
- topic.graph_execution
- topic.attention
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/eagle_worker_v2.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/draft_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_dsv4_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/graph_runner/npu_cudagraph_backend.py
  role: implementation
created_at: '2026-11-08T12:08:03Z'
updated_at: '2026-11-09T04:32:43Z'
platforms: []
aliases:
- EagleDraftWorkerV2
- Device2ExtendCudaGraphRunner
---

# SGLang Ascend Eagle草稿worker：分阶段后端与图回退

## Worker与后端

Eagle draft worker由target worker及draft模型共同构造，decode和draft extend可持有不同attention backend。只有speculative_num_steps>1时，NPU draft decode才选AscendAttnMultiStepDraftBackend，V4选专用DeepseekV4AscendMultiStepDraftBackend；步数≤1时create_decode_backend直接返回None，draft extend再通过注册的Ascend/V4 backend创建。不能以target支持某后端推断draft各阶段复用同一实例。

每个step需要live长度偏移和对应cache写窗口。静态num_tokens_per_req决定图buffer几何，实际每轮可见长度由SpecInput/ForwardBatch传递，不能只修改调度参数而不调整捕获宽度。

## NPU图入口

draft decode阶段也只在speculative_num_steps>1时选择图runner；单步模式不创建这些多步decode backend、不捕获该阶段图，None是正常缺省。worker的draft extend按平台选择Device2ExtendCudaGraphRunner，NPU是显式分支；CUDA才懒加载FlashAttention/FlashMLA，避免NPU环境导入GPU依赖。draft-extend图还受SGLANG_DISABLE_DRAFT_EXTEND_CUDA_GRAPH与是否有可用backend/runner控制；未捕获时回到eager，需重新初始化正确元数据。

capture时间和前后可用内存差分别统计为specialized graph成本，不代表线上每步耗时。NPU图长度更新由独立backend完成；多step的payload和host镜像不能被CUDA通用图假设覆盖。

## 验收与边界

接入时分别记录draft decode、extend、target verify实际backend/runner，检查fallback是否走预期阶段。验证图开关、变batch、request重排、draft步数和DP空rank，比较接受后下一轮cache与logits。本次仅源码阅读，无捕获显存、接受率或吞吐测试；具体芯片范围未逐路线证明。
