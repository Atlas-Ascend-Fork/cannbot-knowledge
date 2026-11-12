---
type: Guide
title: SGLang两阶段PP在HCCL上的配对收发与skip标记
description: 说明NPU PP=2输出通信为何合并send/recv，以及纯chunk跳过时仍发送标记以维持跨microbatch匹配和事件生命周期。
tags:
- task.implementation
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/managers/scheduler_pp_mixin.py
  role: primary
created_at: '2026-11-08T12:10:30Z'
updated_at: '2026-11-09T04:33:52Z'
platforms: []
---

# SGLang两阶段PP在HCCL上的配对收发与skip标记

输出通信入口仅在_is_npu且pp_size==2转入专用方法。HCCL的独立isend/irecv可能等待匹配peer而阻塞，因此send和recv都有时经send_recv_tensor_dict配对提交；只有单方向需要时仍走send-only或recv-only，不能称为每步总是双向batch。

发送和接收针对不同microbatch，不能各自根据本地pure-chunk状态跳过。最后stage决定可跳过时发送{__msg_type__:output,__skip__:True}，中间传递此标记；接收方只按目标batch存在且非prebuilt判断是否参与，收到后再决定是否省略完整结果。否则会出现一侧recv没有匹配send。

完整结果发送前等待队列中的q_event；接收后copy stream先等schedule stream，再准备batch_result并记录D2H事件。另一路前向proxy由_pp_recv_proxy_tensors接收、作为pp_proxy_tensors交给_pp_launch_batch，只有其非CPU Tensor在forward stream中record_stream，防止allocator过早复用。这不覆盖本节输出通信返回的next_pp_outputs；后者保存为self.pp_outputs供后续输出环传，不能推断所有输出张量都获得同样保护。skip路径也保留PPProxyTensors标记，不能丢为None而破坏后续环传。

注释提及约10%吞吐损失是上游实现动机，没有本次可重现benchmark，不应作为收益保证。验收需覆盖相邻microbatch一方纯chunk、一方输出、空/prebuilt、双向及单向、TP辅助组和队列事件；此方法不能推出任意PP数或全部TP×PP模型组合已支持。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
