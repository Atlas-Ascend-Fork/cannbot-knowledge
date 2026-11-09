---
type: Guide
title: vLLM Ascend 310P MRv1：CPU slot 计算、NZ 缓存与投机图门禁
description: 按310P专用runner/input batch/block table核对CPU索引、manager/kernel块比例、NZ分配、异步拒绝修正、采样ID重排和实际图执行拒绝条件。
aliases:
- NPUModelRunner310
- NPUInputBatch310
- temporary_modify_uniform_decode_query_len
- BlockTable._compute_slot_mapping_numpy
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.kv_cache
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/_310p/block_table.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/_310p/model_runner_310p.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/_310p/npu_input_batch.py
  role: implementation
created_at: '2026-11-03T05:15:00Z'
updated_at: '2026-11-03T05:15:00Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 310P MRv1：CPU slot 计算、NZ 缓存与投机图门禁

## 版本、runner与拒绝条件

固定 Main ceac1a2 的三个MRv1兼容文件按整文件AST投影读取全部程序语句：block_table.py199、model_runner_310p.py1038、npu_input_batch.py59原始行；注释/docstring未逐字全文审阅，没有导入/执行上游或NPU。MRv2的[310P MTP合同](vllm_ascend_310p_mtp_proposer_contract.md)采用另一套worker路径，不可按相似类名混用。

NPUModelRunner310继承通用V1 runner后重建310P InputBatch、替换sampler/rejection sampler并固定权重布局FRACTAL_NZ。initialize_kv_cache_tensors明确拒绝kv_transfer_config、use_sparse、use_mla；拒绝由该函数作用范围限定，不等于所有后续310P框架永不支持。supports_standardized_shared_kv_backing=False，不直接沿通用runner的共享raw backing方案推接入。

## CPU索引与虚拟块不变量

BlockTable slot计算接受(req_indices,positions)或(num_reqs,query_start_loc,positions)；后一形式按query边界diff展开请求号，要求token数与positions一致。输入可为NumPy、CPU Tensor或可转数组值，device Tensor会TypeError，不能自动D2H或依赖不支持的NPU算术。

普通slot=b×B+p%B。DCP时虚拟块为B×d，owner=(virtual_offset//I)%d，本地offset=(virtual_offset//(d×I))×I+virtual_offset%I；非owner填PAD_SLOT_ID。块表扁平row stride还含blocks_per_phys_block，不能仅用max_num_blocks_per_req。空tokens只提交0长度copy。

MultiGroupBlockTable对kernel_sizes缺省补[[0]]，单项可广播到多组，否则长度需匹配；max_num_blocks默认ceil(max_model_len/(B×DCP))且也检查组数。提供kv_cache_groups时zip没有额外核其长度，caller应保证所有组完整。NPUInputBatch310先继承通用持久字段，再把block_table替成310P实现，不能认为只换worker类就自动更新已有batch的表。

## 图状态与padding的真实选路

ChunkedPrefill/PrefillCacheHit强制eager；启用spec时状态不是SpecDecoding、query长度不等uniform预算或非整齐请求×query也强制eager。普通DecodeOnly且全部prompt已完成、每请求1query时才补uniform标志。ngram在dispatcher与局部context中把uniform query设1，退出finally恢复runner字段；不是把所有spec方法的K改1。

query_start_loc图padding在uniform时追加等距边界；非uniform时要求请求数未pad并额外造一dummy边界到padded token数。GDN query尾部用最终累计端点，普通query尾部用-1，两者不能统一。dummy捕获临时强制SpecDecoding，finally清flag；profiling不触发同一spec capture分支。

传统FULL spec replay非capture且有update_stream时，先同步current、更新参数、wait更新流，再run_model；ENPU也先update，其他路径在forward后update。重排先后会改变设备依赖，不能用“地址稳定”代替正确顺序。M-RoPE在每次forward前按positions准备cos/sin slices。

## 拒绝修正、采样ID与Host镜像

_prepare_inputs先commit块表、按调度数展开请求索引；有draft时num_valid_tokens扣实际draft数。accepted copy事件先同步；异步spec有前批映射时在device按valid_count修computed，再同步回CPU用于310P slot算术。没有该条件按CPU直接copy。不要在该同步回填后再重复套通用optimistic修正。

positions由每请求computed+query offset在CPU算；输入从Host token表取，prompt embeddings只拷有效范围，多模态/M-RoPE另走专用准备。discard index依据optimistic长度是否覆盖request，不能拿所有padded行当有效采样。spec metadata用每请求实际draft长度，LoRA按scheduled与sampled不同数量映射，LM-head TP另pad logits indices。

复用prev_sampled IDs时先按req_id关联前后索引，写当前sample落点，再按前batch的固定draft stride挑实际本批draft范围。完全连续匹配可走index_copy快速路径，否则scatter；新请求/未复用部分仍需Host→device。仅比较token总行数相同无法证明请求重排映射正确。

## NZ缓存分配与重建边界

Attention缓存按manager块可整除的backend supported size筛选，且kernel_size×head_size<=128×128；取来源列表首个可用项，不是性能搜索。K/V分开empty_with_format(NZ)；manager/kernel比例扩大物理行数。Mamba把raw int8切成spec shapes/dtypes，特定shared slot可复用同状态列表；层名中linear_attn/attn参与分类，适配新模块命名必须检查，最后层集合不全会断言。

may_reinitialize_input_batch跳过EncoderOnly组，对Mamba按prefix caching/spec块预算扩大每请求表容量。需要重建时assert UVA cpu_offload_gb=0，不能在保留旧offload引用时悄悄换batch。kernel sizes在此为每组候选列表，旧静态类型cast不改变运行数据结构，消费者必须接受其真实形式。

验收先记录实际worker/runner、每组spec/块大小、CPU表与device slots、NZ存储、query/GDN尾值，再覆盖新旧请求重排、拒绝、K变动、ngram图、prefill eager、LoRA/TP logits及Mamba共享。没有真实310P/配对Native结果时，不把静态guard、empty分配或dummy通过当模型/图/性能支持。
