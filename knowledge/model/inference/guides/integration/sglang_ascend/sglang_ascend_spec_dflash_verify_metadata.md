---
type: Guide
title: SGLang Ascend DFlash验证元数据：live长度、Q边界与padding
description: 说明DFlashVerifyInput在NPU延迟规划、重建V4当前写窗口、线性allow mask与ragged累计边界的契约。
tags:
- task.implementation
- topic.speculative_decoding
- topic.kv_cache
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dflash_info.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_common_hooks.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/graph_runner/npu_cudagraph_backend.py
  role: implementation
created_at: '2026-11-08T12:08:06Z'
updated_at: '2026-11-09T04:32:43Z'
platforms: []
aliases:
- DFlashVerifyInput
- live_seq_lens_cpu
- qo_indptr
---

# SGLang Ascend DFlash验证元数据：live长度、Q边界与padding

## Verify输入语义

DFlashVerifyInput是线性候选链，topk固定1；custom_mask的True表示允许attention，与某些FIA bool屏蔽mask的True语义相反。draft_token_num是固定最大宽，num_tokens_per_req用于padding；ragged layout描述实际各请求宽度，live_seq_lens_cpu保存扩张前已提交前缀。

prepare_for_verify将候选作为input_ids，在NPU且非idle时用live长度重建DSV4本轮verify bundle，再切TARGET_VERIFY；清旧extend track mask并准备Mamba track索引，生成ForwardBatch。NPU或显式defer时立即返回，由ModelRunner在DP/EP padding后做attention/graph规划；提前算出的can_run_cuda_graph只是候选条件。

## Q与KV累计边界

固定宽qo_indptr为0,width,2*width...；ragged用layout.qo_indptr_device，并在图padding时先扩展到bucket。KV read长度在此由prefix+verify_lens得到，cum_kv_seq_len是其累计和；不能把Q indptr误用为KV长度，或将已扩张的host长度再次加width。

runner_ids按本轮IterationIds打包read stream，可写入预分配kv_indices_buf以省分配和D2D copy。仅在custom_mask非None且window非None的自定义mask窗口转换分支调用window.tree_mask，并断言layout is None；custom_mask为None时不触发该断言，不能据此排除全部ragged窗口读。custom mask若需扩容按允许语义填True，这不代表所有后端都可以忽略padding的独立长度约束。

## 验证与边界

按请求核对live、final KV长度、Q宽与write窗口，覆盖同bucket不同raw_bs、ragged padding、Mamba track和V4跨压缩组。关闭图基线与图重放有效行应一致，padding不应写真实request状态。本次未执行，本文只闭合模型元数据，不声明所有底层attention或硬件支持ragged。
