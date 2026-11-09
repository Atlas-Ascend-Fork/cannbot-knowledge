---
type: Runbook
title: vLLM Ascend GDN元数据验证：图回放场景与缓冲区诊断
description: 依据CPU测试场景定位GDN图回放在batch收缩、无草稿或idle后的状态错位，核对FIA填充、请求与token容量、持久引用和Host清理归属，保留实机验证边界。
aliases:
- GDN图回放元数据
- _remove_spec_graph_padding_queries
- _materialize_graph_query_start_loc
- GDNAttentionMetadataBuilder310
tags:
- task.debugging
- topic.precision
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_gdn_attn_builder.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/gdn_attn_builder.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/gdn_attn_builder_310.py
  role: implementation
created_at: '2026-10-31T11:05:12Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T11:12:53Z'
---

# vLLM Ascend GDN元数据验证：图回放场景与缓冲区诊断

## 症状与证据边界

GDN/KDA在图回放、batch收缩、动态draft归0或idle DP后出现状态串请求、旧conv输出、metadata shape不符或图模式结果与eager不一致时，按下面的实际字段定位。这里是固定源码保护与测试设计导出的诊断方法，没有在本仓复现或修复真实NPU故障。

主证据为固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的test_gdn_attn_builder.py1595行、34个CPU测试函数；公共builder1158和310P subclass60解释场景断言背后的机制，三份全文只作数据阅读。未运行上游导入、测试、模型或NPU。整项硬件/图/软件栈交集待验，保持draft/空平台。适配字段先读[GDN元数据接入](../../guides/integration/vllm_ascend_gdn_metadata_builder_contract.md)；GLM RecoverSSM专用staging/采样commit另见[已有诊断](vllm_ascend_glm_recoverssm_graph_metadata.md)。

## 先按测试场景建立可观察输入

| 固定测试函数 | 需保留的输入和断言 |
|---|---|
| test_spec_graph_fia_padding_refreshes_captured_buffers | K7、1/2活跃请求、显式/省略真实请求数；核对旧capture引用更新、原common输入不变 |
| test_spec_graph_real_prefill_is_not_treated_as_padding | seq_lens为[71,8]、draft为[7,-1]；真实第二行保留prefill |
| test_full_graph_without_runtime_spec_resets_captured_spec_inputs | 先spec capture再普通decode；旧spec offset/accepted清0、state填PAD，Host输出从填NaN变为0 |
| test_graph_attaches_once_after_padding_and_reuses_final_buffers | 真实请求2→1→3→2，公共/310P及spec开关分别检查地址和attach次数 |
| test_full_graph_idle_dummy_uses_zero_length_recurrent_metadata | 图数组4行、query_lens全0；核对零长度边界及NULL state |
| test_host_conv_indices_are_shared_and_refreshed | block表首列[10,20]更新为[40,50]；同一buffer地址必须反映本轮索引 |

这些是已读的测试设计，尚未在本仓执行。显式num_actual_reqs=0与保留图数组但query_lens全0是不同输入；后者有上述idle fixture，前者仍须核对父类容量和后续分支，不能由参数范围允许0自动推所有空批均通过。

## 快速探针

保存graph_request_count、num_actual_reqs、num_actual_tokens、num_decode_tokens和num_spec_decode_tokens；同时保存CPU/device query_start_loc、seq_lens upper bound、draft counts、phase mask、state indices、accepted和token indices。检查每项是请求、token还是边界数组，不能只比较一个batch size。

记录builder/backend类型、_USE_COMMON_KERNEL_METADATA、_SPEC_GRAPH_PAD_SLOT_ID、父分配的request/token容量，以及conv/length/offset buffers的data_ptr、有效长度和旧capture对象是否仍指同一storage。probe先读取现有状态，不通过改padding或清缓存掩盖证据。

## 路径一：FIA把padding写成完整K+1跨度

_remove_spec_graph_padding_queries只在full graph+spec入口使用。它要求CPU seq-lens upper bound和匹配请求数的draft数组、且至少一项draft>0；inactive条件为seq_len=0且draft<0，并必须是请求后缀。inactive散落中间直接ValueError，不能排序后悄悄改变共享MLA顺序。

helper clone CPU offsets，把inactive后的边界重复为首个inactive起点，再生成GDN-local device offsets/actual tokens，原common metadata保留。例如原[0,8,16]、第二行seq_len0/draft-1，GDN视图变[0,8,8]且actual8，原对象仍可保留16；两者不是一个计数。

真实prefill即使query_len=K+1且draft=-1，seq_len>0时不能当padding裁掉。全批draft0或缺所需CPU信息时本helper不应用，继续按实际普通分组/失活重置检查；不要把该函数描述成无条件清全部图填充。

## 路径二：请求容量与token容量混用

_pad_spec_decode_metadata先独立检查spec/non-spec token indices容量，再写捕获的请求字段。_materialize_graph_request_tensor要求actual<=graph<=buffer capacity且来源覆盖actual；_materialize_graph_query_start_loc另外检查N+1边界容量，并将尾部重复末有效终点，生成零长度dummy请求。

公共spec padding state用NULL_BLOCK_ID、mask False、accepted用_GDN_GRAPH_DUMMY_ACCEPTED_TOKEN_COUNT=1。1是one-based合法dummy输入配零长度span，不是采样实际接受数；不能据此无条件推进候选state。

公共_can_pad_spec_decode要求请求数和spec token数都不超decode_cudagraph_max_bs；不满足时保留动态路径。310P subclass允许token数到spec_token_indx.numel，不能把公共单token限制强套到并发MTP，也不能跳过真实容量检查。

## 路径三：普通decode和idle仍带旧state IDs

_pad_decode_metadata的有效请求计数取num_decode_tokens；num_decodes可能包含零长度图行。真实前缀copy，其余state填NULL_BLOCK_ID，边界重复末有效终点。idle的offset应全0、state应全NULL，不能沿输入block table残留的98/99之类值访问旧pool。

actual_seq_lengths是首offset加相邻diff，padding长度为0。公共builder复用自己的spec/non-spec length buffer，先完成padding再_attach各phase一次。若conv包装捕获的是旧动态引用或长度仍按未padding请求数构造，先查attach时机和引用，而非扩大mask。

## 路径四：本轮没有spec，旧捕获分支仍可能执行

full graph且配置启spec、但本轮num_spec_decodes=0时，每次build都调用_reset_spec_decode_graph_inputs：spec state填PAD_SLOT_ID、offset/accepted/公共length清0。新metadata.spec_decode_metadata=None并不能让旧capture对象引用自动失效。

Host subclass还清已经分配的spec conv indices；共享conv输出每步整体置0，包括失活分支。UT先捕获spec对象，再切普通decode/idle，检查旧对象指向的数据也变为no-op并与新decode复用同一输出buffer；这是测试定义，不是本次图回放结果。

区分“仍启用的padding请求accepted1”与“整条失活分支accepted0”。把两者统一为1或0都不能代替query span/state sentinel的完整协议；也不要把其他SGLang版本的index0/padding修法直接迁来。

## 路径五：Host group索引或输出未刷新

Host额外buffers只按group代表layer的opt-in配置分配。_prepare_conv_indices对一维连续来源保留alias，对matrix取首列复制，容量不足报错；non-spec prefill/decode共享最长索引前缀。更新请求block表后，同一地址应看到本轮IDs，recurrent多列state table仍保持原协议。

共享conv输出容量按max(max_seq×(K+1),decode_graph_max_bs)、feature3×local projection、model dtype分配一次，每步清一次，group layers顺序消费；它不是每layer/每请求独享。接入方核对buffer owner、phase有效行及清理时机，不能只检查data_ptr相同。

缺shared buffer的普通调用由卷积包装负责自己的初始化；已提供buffer的空indices分支不替你清理。与[KDA输出归属](../../guides/integration/vllm_ascend_glm_next_kda_dispatch_contract.md)联查，避免在错误层增加额外清零或临时tensor。

## 310P、版本与真实prefill分别判断

GDNAttentionMetadataBuilder310设置PAD_SLOT_ID、_USE_COMMON_KERNEL_METADATA=False；省略公共non-spec包装/chunk/actual-length字段，spec只共用conv包装且length为None。保留兼容类名AscendGDNAttentionMetadataBuilder310。不能按公共builder预期强行补字段，或把局部310P源码当全模型图支持证明。

align模式下device seq_lens与block-table请求行要一致；非0.32的裁行分支和0.32行为分别保留，不能拿过期CPU长度算state slot。one-token prompt只有已有state才改decode，真实K+1 prompt chunk仍prefill；DSpark target的重排阈值包含base token，不随draft sample_from_anchor缩短。

## 验证、修复与回退

按已定位的字段来源、分类、容量、引用或清理owner恢复匹配版本的合同；本卡没有提供一个跨所有模型的patch。先验证原common输入不变和有效请求视图正确，再测spec→非spec、grow/shrink/grow、0活跃请求、真实K+1 prefill、混batch、zero draft和310P/common字段差异。

UT1595的34个函数主要用CPU与局部mock，检查stable bool partition、request/token维度、one-based dummy accepted、FIA后缀、旧capture引用更新和Host共享索引；DCP16等fixture不代表实际HCCL/NPU通过。真实设备还需检查kernel sentinel解释、图地址、数值和跨步state推进。

失败关闭新增图/动态投机组合，按基线重建匹配模型、builder和状态后验证eager；不扩大capture容量、删guard或循环复用异常state来继续比较性能。记录metadata CPU/H2D、kernel、buffer及通信成本；没有质量/状态正确性证据时不宣称吞吐收益。
