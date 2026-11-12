---
type: Guide
title: SGLang Ascend多层MTP：独立runner与逐步图选择
description: 说明de-tied多层Eagle的后端、cache与logits选择，以及NPU坚持每step图和非图post-pad元数据初始化。
tags:
- task.implementation
- topic.speculative_decoding
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/multi_layer_eagle_worker_v2.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/multi_layer_eagle_draft_extend_cuda_graph_runner.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/eagle_worker_common.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/managers/tp_worker.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/kv_cache_configurator.py
  role: implementation
created_at: '2026-11-08T12:08:03Z'
updated_at: '2026-11-09T04:32:43Z'
platforms: []
aliases:
- MultiLayerEagleDraftWorker
- SGLANG_ENABLE_SINGLE_CG_DRAFT
---

# SGLang Ascend多层MTP：独立runner与逐步图选择

## 多层与多步不能混为一个共享后端

多层Eagle为各draft step维护独立runner、backend和KV存储，但共享请求到token的映射；TpModelWorker将同一req_to_token_pool交给各runner，draft extend逐步切换相应KV池与backend。混合模型在draft_owns_state成立时通过clone_with_new_mamba拥有独立卷积/Mamba状态，同时仍共享请求映射，不能将状态池独立解释成请求映射独立。非图路径每步都初始化自己的attention元数据，只有第一个runner曾预计划不足以将整个链标ready。idle round没有真实请求，不做非法空长度规划。

接受后extend根据select_index裁剪所需logits；如果不能裁剪，则从全logits按索引取行。rejection sampling在topk1链生成并保留draft proposal概率，其余路线用softmax+fast_topk；不能把只有token id的草稿当具备概率契约。

## NPU图边界

非NPU可在开关和metadata staging能力满足时采用合并multi-step单图；NPU明确保留每step图，因为长度更新在backend中，合并多步捕获在此未开启。SGLANG_ENABLE_SINGLE_CG_DRAFT不覆盖这一guard。关闭decode图或禁用draft-extend图时直接回eager。

## 检查与代价

检查num_steps与runner数、每步weight/cache对应、accept后旋转输入以及图中length偏移。测试接受长度从0到全宽、request调换、idle rank、图与非图输出及第二轮decode；多层权重与各step图会占额外显存，不能只比较草稿单次前向耗时。本次未执行多层模型或性能测试，NPU路由不等于全型号支持。
