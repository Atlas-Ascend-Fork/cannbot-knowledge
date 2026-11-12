---
type: Guide
title: SGLang Ascend MLA模型层：投影吸收、索引复用与流依赖
description: 闭合DeepSeek MLA/DSA模型层从q_lora到稀疏attention和输出投影的NPU分支，说明融合精度选择、动态INT8与BF16索引器边界。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/modules/deepseek_v2_attention_mla_npu.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/mla_preprocess.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/dsa/dsa_npu_indexer.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/dcp.py
  role: implementation
created_at: '2026-11-08T12:07:53Z'
updated_at: '2026-11-08T12:07:53Z'
platforms: []
aliases:
- Deepseek MLA NPU
- q_lora
- AG_AFTER_QLORA
---

# SGLang Ascend MLA模型层：投影吸收、索引复用与流依赖

## 场景与调用链

NPU模块把模型层拆为准备和计算：q_lora norm、q_b投影、K norm/RoPE及cache写，随后按MHA/吸收式MLA/DSA选择attention，最后恢复输出投影。MHA路线将latent经kv_b投成完整K/V；MLA路线先用w_kc吸收q_nope，再使用latent cache，避免每步展开全部历史KV。

普通MLA的小token分支可融合split Q/K与RMSNorm，但只有token<65536、无prefill CP且模型未opt-out时选择；DSA分支阈值为65535。源码明确融合路径与分开RMSNorm不数值等价，opt-out必须保留，不能把少一次kernel调用当作无损替换。

## DSA与量化边界

indexer即使跳过TopK也可能仍需写K缓存。共享TopK的后续层直接复用前层结果；新算出的全局TopK在DCP下只localize一次，不能重复重映射。nextn没有可复用前层结果时需自行计算。

动态INT8 MLA若配BF16 indexer，必须重新生成未量化q_lora并清除dynamic_scale；不能将INT8 latent直接喂入BF16索引器。ModelSlim缓存路线动态量化Q，并在BF16 RoPE侧除以query descale与K scale的乘积，交由FIA恢复QK/PV量级。

MLAPO已经写KV时传save_kv_cache=False；非融合分步路线由显式cache写负责。DSA的prefill、draft extend和mixed阶段不直接套用decode的MLAPO选择。DCP先聚合Q，再执行局部attention并按LSE合并。

## 输出与流所有权

输出BMM按维度和阶段选择native transpose_batchmatmul或自定义batch_matmul_transpose，大维度不能越过65536附近的原生限制；gate在o_proj之前应用。多流准备需让投影流等待输入生产流，在侧流记录张量使用并等待ready event，再由主流等待结果。启用多流只改变调度，不删除K写入与TopK读取依赖。

适配时依次核对融合opt-out、q_lora dtype、共享TopK来源、cache唯一写入者、事件与output head形状。建议以相同输入对比MHA/吸收式、prefill/decode和开关多流的输出及cache；本次仅做来源阅读，无性能或数值测量。源码未逐特性声明硬件矩阵，平台保持未知。
