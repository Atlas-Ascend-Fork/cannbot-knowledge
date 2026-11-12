---
type: Guide
title: SGLang Ascend多层MTP图缓冲：共享地址与原生准备回退
description: 说明逐步反向捕获、共享输入buffer、NPU原生prepare替换及select_index和padding哨兵约束。
tags:
- task.implementation
- topic.speculative_decoding
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/multi_layer_eagle_draft_extend_cuda_graph_runner.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/multi_layer_eagle.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/graph_runner/npu_cudagraph_backend.py
  role: implementation
created_at: '2026-11-08T12:08:03Z'
updated_at: '2026-11-09T04:32:21Z'
platforms: []
aliases:
- MultiLayerEagleMultiStepDraftExtendCudaGraphRunner
- fill_draft_extend_prepare_buffers_native
---

# SGLang Ascend多层MTP图缓冲：共享地址与原生准备回退

## 缓冲与捕获顺序

多层draft extend用一组持久input_ids、positions、out_cache_loc、seq_lens及CPU镜像、req ids、correct/accept数量、hidden和select_index缓冲供所有step共享。建立runner后倒序捕获各step，各 step 共享输入地址，但分别 resolve 独立 backend；每个 NPU backend 从 _pool=None 创建自己的 graph pool handle，pool 只在该实例的各 shape 间复用，并非跨 step 共用；NPU的关闭图判定用cuda_graph_fully_disabled，不能只看一个普通CUDA decode配置字段。

NPU将fill_draft_extend_prepare_buffers替换为native PyTorch版本，因为此处Triton mega-kernel有CCU错误记录。回退是本版本实际实现选择，不是删除准备工作，也不证明所有Triton kernel在NPU不可用。

## 原生准备契约

token buffer只copy真实rows，padding留给既定捕获协议；seq_lens先按bucket fill再copy raw请求。num_accept_tokens padding=-1，temperature padding=1；select_index为i*num_tokens_per_bs+num_front_tokens+num_correct_drafts。global_num_tokens及logprob token数使用bucket总token，hidden仅在源存在时copy。不能把raw batch和padded bucket混写。

rotate_input_ids在NPU batch_size=0时提前返回，避免零grid触发triton-ascend abort；有请求时逐extend段旋转，并插入各请求新token与选择索引。

## 验收与边界

对raw_bs<bucket、空DP rank、不同接受数量、多step重放和无hidden源检查每字段，尤其padding哨兵与select_index。不要把graph-owned输出保留到下一次重放还假设不变。native准备增加若干设备操作，换取可运行路径；本次未捕获或运行CCU回归，不给出性能结论。
