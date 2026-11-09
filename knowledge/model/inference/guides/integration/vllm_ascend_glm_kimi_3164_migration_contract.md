---
type: Guide
title: vLLM Ascend GLM/Kimi 版本迁移：量化 KPool、RecoverSSM 与输出地址
description: 核对3164 GLM KPool BF16/FP8/INT8缓存与scale对齐、piecewise KDA caller-owned输出、RecoverSSM prefix align、视觉NZ二维投影；补充Kimi重复RS与MiniMax score派发变化。
aliases:
- GLM KPool FP8 INT8 scale cache 3164
- glm5next_kda_forward_with_output piecewise
- RecoverSSM prefix caching mamba align
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/glm5next/attention.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/glm5next/cache_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/glm5next/cache_views.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/glm5next/kda.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/glm5next/kv_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/glm5next/multimodal.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/glm5next/recoverssm_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/glm5next/recoverssm_metadata.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/glm5next/sparse_attn_indexer_kpool.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/kimi_k3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/minimax_m3/msa_m3.py
  role: implementation
created_at: '2026-11-03T06:35:09Z'
updated_at: '2026-11-03T06:35:09Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend GLM/Kimi 版本迁移：量化 KPool、RecoverSSM 与输出地址

固定差异 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd` 的完整 unified diff 与必要上下文已读，未将目标整文件标为FULL；既有ceac卡继续作为旧版本证据。本次没有上游导入、真实模型、NPU、图、多卡或性能运行。

## GLM KPool 新 dtype 与物理页

Indexer允许auto/bf16/fp8/int8，前两者保留BF16，后两者分别E4M3FN/INT8；非法字符串拒绝。FP8显式拒绝OffloadingConnector或PreemptOffloadConnector，不能把这条限定自动扩成INT8也拒绝或其他connector已验证。cache spec只接受这三dtype，quantized每token scale_dim1：FP8的scale FP32，INT8的scale FP16，BF16无scale。

small page由indexer与FP32 tail共享页类，增加lcm对齐保证tail整行和量化scale在scheduler页切kernel block后对齐。view_compressed_indexer_cache对每kernel页先放dense key再放scale，K/scale视图使用各自dtype换算的统一**字节**页距；校验页可整分、容量够且scale对齐，storage_offset需加原view offset与key_bytes。返回tuple长度变为1或2，不能沿ceac无scale路径只取一个tensor、按numel紧凑flatten。实际量化write/selection另由同版本attention/indexer合同核对。

## KDA 自定义 op 与 piecewise 地址

旧custom op只包core+gated norm，新版本将whole layer dispatch移到eager op：`forward`在piecewise模式分配graph-owned empty_like输出，调用mutates(output)的glm5next_kda_forward_with_output；非split模式调用直接返回Tensor的glm5next_kda_forward，fake返回empty_like、mutates空。后者没有eager_break装饰，不能把新返回地址路线用于分段重放。

_forward内计算QKV、gate、core、o_norm与o_proj；PCP恢复行有caller buffer时index_select直接写out，没buffer时返回新Tensor，普通非PCP按同样规则copy/return。_forward_core不再单独eager_break。需要记录piecewise开关、custom op schema/fake/mutates和buffer地址，不能只按op名字复用旧签名，也不能因减少hidden-wide copy便宣称所有模式更快。

## RecoverSSM prefix 与视觉 NZ

RecoverSSM不再无条件禁止prefix：enable_prefix_caching=True要求mamba_cache_mode=align，False要求none。spec必需、stochastic rounding拒绝、PP/PCP/DCP=1等旧边界仍保留。align metadata builder在调用Native前通过device-independent mamba_get_block_table_tensor计算physical state IDs，避免CUDA-only fallback；prefix开关本身不证明缓存命中、回滚或所有dtype数值正确。

GLM vision仅当hardware profile要求二维NZ输入、weight_nz_mode=2、UnquantizedLinearMethod及BF16/FP16权重时，把gate/up、down和attention out投影flatten为二维再恢复前导维。该predicate在构造时缓存；权重不改，量化投影与其他硬件不强制套这条路线。shape恢复与真实bias/TP行为仍需完整模型验收。

旧SparseAttnIndexerKpool helper删除query_metadata参数与local query override，selection直接消费indexer_metadata的cum ends/seq_lens和positions；最终不再额外按query_metadata.actual mask。它与ceac的global write/local query接口不可拼接，复用topk仍推进cache。当前默认CANN路径、历史Triton helper与新版量化路径分别按实际caller选中，不能从单文件签名推断支持全部CP模式。

## Kimi 与 MiniMax 的相邻变化

Kimi decoder在SP且fuse_o_proj_mm_reduce_scatter为False时才再做RS：fused O-proj即使fallback也返回token shard，重复RS会把prefix相对bank缩小。不要据fusion失败就恢复无条件外层RS，先核对实际输出分片合同。

MiniMax-M3把CANN MsaIndexScore decode选择常量改为True，A5也与A3使用该路径；A5 Triton kernel仍可import作为rollback资料，但不再是该固定版本的默认decode选择。更改派发不是新性能结论，升级需同时对照score、forced blocks、TopK/count和完整模型延迟。

Agent按版本保存quantized pool页/scale ABI、输出地址生命周期、prefix对齐状态、视觉format与SP归约次数；覆盖piecewise/eager、空池/空query、prefix hit、MTP拒绝、FP8不支持offload的明确拒绝，以及CANN/Triton独立数值比较。本次没有为上述组合填写verified。
