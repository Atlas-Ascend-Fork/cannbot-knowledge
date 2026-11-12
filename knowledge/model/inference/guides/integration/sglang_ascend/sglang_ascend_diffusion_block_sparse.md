---
type: Guide
title: SGLang Diffusion块稀疏：首步LASER与首帧保留
description: 说明BlockSparse后端的metadata、128块/stride8估计、首帧稠密保护和BNSD实际调用。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/attention/backends/block_sparse_attn.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/attention/backends/laser_attn.py
  role: implementation
created_at: '2026-11-08T12:26:53Z'
updated_at: '2026-11-09T04:32:43Z'
platforms: []
---

# SGLang Diffusion块稀疏：首步LASER与首帧保留

## 场景与配置

长视频self-attention可按metadata.current_timestep先跑skip_first_steps个LASER步骤，再启用块稀疏；skip必须非负，sparsity在[0,1)，零稀疏会提示直接用LASER。依赖attentions且head_dim只接受32/64/96/128，不能因公共选择器注册而认为无需扩展。

## 机制与代价

以128 token为块，stride8估计QK，估计scale除8，row_sparse使用1-sparsity；随后构造int8块掩码及逐行int32有效块计数。按latent高宽与patch推导首帧块，将其行和列强制保留为dense，再重算计数。sparsity表示丢弃比例，1-sparsity才是目标保留比例；首帧保护可能提高实际保留密度、降低实际丢弃比例，若相关块已保留则不会增加密度。源码因BSND质量问题实际转换连续BNSD后执行，不应删除该布局变换。

接入时确认每步metadata更新、latent与patch一致、真实首帧边界与padding相符。先LASER基线，再逐步提高稀疏度并测视频时序/文本一致性、有效块数和端到端延迟；较小序列可能被估计与布局成本抵消。扩展存在但稀疏质量不通过时可回LASER；attentions扩展缺失时LASER也不可用，应选择依赖已满足的FA或SDPA，本次没有实测，芯片范围未知。
