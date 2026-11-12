---
type: Guide
title: SGLang Ascend DSpark验证：实时长度、compact散射与epilogue
description: 说明target verify executor如何保存live前缀、扩张Host长度一次、post-pad规划、compact输出恢复和图内/图外接受的统一结果。
tags:
- task.implementation
- topic.speculative_decoding
- topic.graph_execution
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dspark_components/dspark_verify.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dflash_info.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/dspark/dspark_verify_window.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_dsv4_backend.py
  role: implementation
created_at: '2026-11-08T12:08:05Z'
updated_at: '2026-11-08T12:08:05Z'
platforms: []
aliases:
- TargetVerifyExecutor
- DsparkVerifyEpilogue
- ScatterCompactToStrided
---

# SGLang Ascend DSpark验证：实时长度、compact散射与epilogue

## Host长度与最终规划

non-compact verify用DFlashVerifyInput承载线性候选，保存live_seq_lens_cpu；当backend需要CPU长度且不会自加verify时临时扩张host镜像，初始化ForwardBatch后恢复原batch镜像。NPU调用forward_batch_generation时不强制skip_attn_backend_init，由ModelRunner在最终padding后规划；否则图bucket/DP padding改变后会读旧页表。

## Compact输出契约

ragged窗口将不同请求长度的候选压紧，query indptr和window_index描述packed→原固定宽矩阵。若target graph附有epilogue，可读取已写的strided logits/hidden；否则scatter compact到bs*verify_width，padding填0，再统一应用logits调整。图返回却无epilogue输出直接assert，不能读取旧buffer。

commit_hidden只注入接受部分：compact用ragged注入，static将hidden reshape为[bs,width,D]再按commit处理。target hidden缺失是错误，因为下一轮draft上下文依赖它；不能静默只提交token ids。

## 接受与折叠

folded路径从图epilogue读取AcceptOuts；eager路径按greedy、sharded/blockwise或普通采样选择，混合greedy batch再逐请求选择结果。图中accept是greedy，采样批次必须满足更严格路径。TP sync站点依据greedy/sample区分；cutoff verify长度限制接受，不能把未验证draft保留为已接受。

预算受限时需同时检查cap_trim_lens、correct_len、bonus、commit_lens与prefix新长度。模拟接受/bonus有独立seed和override协议，只是实验工具，不是真实观测。

验收应覆盖相同token tier但不同ragged布局、Host镜像恢复、DP padding、graph→eager切换、grammar与采样，并与static全宽结果对照有效候选。compact节省target计算却增加打包/散射和元数据成本；本次未运行，不对所有NPU芯片或分布保真作实测声明。
