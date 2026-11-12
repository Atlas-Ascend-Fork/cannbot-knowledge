---
type: Guide
title: SGLang Ascend混合线性注意力：图元数据与接受后双状态恢复
description: 闭合固定图bucket中的Mamba slot、query边界和树检索缓冲，以及GDN/KDA投机接受后SSM提交和conv rollback。
tags:
- task.implementation
- topic.attention
- topic.speculative_decoding
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_hybrid_linear_attn_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_gdn_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_kda_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/linear/kda_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/hybrid_linear_attn_backend.py
  role: implementation
created_at: '2026-11-08T12:07:59Z'
updated_at: '2026-11-09T04:31:18Z'
platforms: []
aliases:
- AscendHybridLinearAttnBackend
- conv_state_rollback
- move_intermediate_cache
---

# SGLang Ascend混合线性注意力：图元数据与接受后双状态恢复

## 图内固定缓冲

以下图元数据描述限定于 AscendMambaAttnBackendBase 的 GDN/Mamba2 路径。该后端按最大batch预分配int32 mamba slot、GDN扩展slot、query_start_loc及Eagle token/sibling/parent树缓冲。固定draft宽从max_tokens/max_bs得到，必须整除。capture将request pool id映射到Mamba slot；decode query边界逐行增长，verify按draft宽增长，topk>1才准备树字段。

replay明确拒绝ragged verify。padding请求/状态slot清为0，seq_len fill为0；query边界的padding尾部保持最后有效token累计数，不能每个padding request再增加draft宽而创造虚假token。GDN额外展开状态索引也必须与实际Q行一致。Ascend KDA 继承共享 KDA 后端，使用另一套图元数据：共享后端声明支持 ragged verify graph，以 -1 标记 padding 状态 slot，并按 ragged query 边界处理；Ascend KDA 将 ragged 候选 dense 化。不能把上述拒绝条件或零 slot 约定套给 KDA。

## SSM提交与卷积回滚

verify已保存全部候选SSM。接受后以metadata.mamba_cache_indices找到persistent目标slot，从对应accepted-step中间态搬移所有层；prefix tracking可额外选择边界步写track slot。最后正确步是候选步索引，不能混用包含bonus的接受长度。

卷积没有默认逐步snapshot：先将verify窗口复制到需要的跟踪槽（其他行自拷贝），再用conv_state_rollback按last accepted step和draft宽恢复工作槽及跟踪槽。只搬SSM而不恢复conv，或者只截token而不搬任何状态，都会污染下一轮。KDA的strided V-first mover由其专用hybrid覆写，不能直接复用本类连续搬移假设。

## 实施与验证

先检查图bucket真实请求数、query边界、Mamba索引和intermediate容量，再根据accept结果执行SSM及conv双恢复。测试接受首步/中间/末步、空DP rank、请求重排、prefix tracking和下轮decode。额外scratch及rollback带来内存/设备操作成本，收益只在整体speculative接受率与吞吐实测后判断。本次未运行测试，图支持也不等于逐芯片兼容已确认。
