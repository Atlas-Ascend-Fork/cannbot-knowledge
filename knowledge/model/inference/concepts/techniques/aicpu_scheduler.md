---
type: Concept
title: AICPU Scheduler（值依赖分核下沉 ARM 核）
description: 以当前 SparseFlashMLA/LI metadata 接口说明值依赖分核、压缩长度和余数、CP 模式复用及 Decode 事件同步。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_ascendc_operator_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/indexer.py
  role: implementation
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-10-29T15:17:34Z'
platforms:
- a3
- '950'
---

# AICPU Scheduler：值依赖分核

## 机制

稀疏注意力的合理分核不仅取决于 shape，还取决于实际上下文长度。技术方案将只依赖 shape 的最大 workspace、tiling key、block dim 和静态 tiling data 放在 Host，将运行时值依赖的分核交给独立 AICPU metadata 算子，再供主 NPU 算子消费。减少 Host 往返、为调度和主计算重叠提供机会；是否掩盖要以时间线确认。

## 当前 V4 接口

| 主计算格式 | Metadata 入口（cann_ops_transformer） |
| --- | --- |
| 非量化 Shared-KV | sparse_flash_mla_metadata |
| 混合打包 FP8 KV | mixed_quant_sparse_flash_mla_metadata |
| HiF8 Q/KV | quant_sparse_flash_mla_metadata |
| LI Int8/FP8/HiF8 | quant_lightning_indexer_metadata |

`generate_sas_metadata_kwargs` 提供 TND/PA_BBND、压缩比、窗口、head 等配置；calc_sas_metadata 补 cu_seqlens_q、seqused_q、seqused_ori_kv，压缩时再补 compressed_seq_lens 与 compressed_seq_remainders。LI 也用整除后的 seqused_k 和余数 cmp_residual_k，不能把原始未压缩长度直接传给 LI。

## 复用与同步边界

前向按 C1A/C4A/C128A 与 LI 分模式生成 metadata，不逐层重复相同模式；CP Prefill 的 prev/next 必须分别计算。原生 MTP Spec 只需 C1A。LI 量化模式为 FP8=1、Int8=2、HiF8=4，主算子与 metadata 必须一致。

Decode 的 enable_multi_streams 可用独立 metadata_stream，事件0建立输入依赖，事件1让消费者等待所需结果。复用只覆盖当前前向和兼容模式，不能跨步复用变化的实际长度或凭空认定调度开销为零。

V3.2 技术报告另有将 LI 分核放入 AICore 的实现；这是不同算子的调度选择，不能把它与 V4 独立 AICPU 算子混为同一调用。机制与算子见[SAS](../kernels/sparse_attn_sharedkv.md)、[LI](../kernels/lightning_indexer.md)和[图模式](npu_graph_mode.md)。本次为源码审阅，未执行硬件验证。
