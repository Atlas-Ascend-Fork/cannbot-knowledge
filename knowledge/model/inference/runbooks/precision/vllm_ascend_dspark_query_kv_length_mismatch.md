---
type: Runbook
title: vLLM Ascend DSpark 状态诊断：query宽度、有效KV长度与缓存组
description: 当DSpark拒绝采样后读到未写KV或满图padding错位时，区分K/K+1、实际draft长度和target上界，并按真实层到cache-group映射构建slot与图参数。
tags:
- task.debugging
- topic.kv_cache
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/dspark_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/dspark_context.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dspark_valid_kv_lengths.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dspark_speculator.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dspark_proposer.py
  role: evidence
created_at: '2026-10-29T14:55:50Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T15:05:19Z'
---

# vLLM Ascend DSpark 状态诊断：query宽度、有效KV长度与缓存组


## 症状与快速检查

固定ceac1a2b的Host接口显示：target optimistic长度可能包含拒绝/lookahead，而DSpark非因果块会读取配置允许的整个KV范围；错误长度可能暴露未写slot。图padding、不同block size的多组缓存或dummy残留又会放大这种错位。本卡给出源码探针，未声称本仓复现过设备错误；实际产品范围未闭合，保持draft/空平台。

同时保存K、sample_from_anchor、每请求真实query宽度Q、num_reqs与padded num_reqs、CPU/device seq_lens及query_start_loc、每层cache-group/逻辑block size、读表和写slot。先看[块布局合同](../../guides/integration/vllm_ascend_dspark_block_markov_contract.md)，不能只凭num_speculative_tokens推所有buffer尺寸。

## 有效KV长度与query长度是两条轴

1. MRv1 set_inputs_first_pass在device侧先减num_rejected再加Q。CPU canonical mirror已由runner做接受数校正，只clone后加Q，不能再减一次。固定UT例中device 128、rejected 2、CPU 126、Q=5，双侧都应131；不是CPU 129。异步CPU镜像字段可能为None，不能为凑字段引入额外D2H等待。
2. MRv2的_prepare_draft_dcp_metadata_inputs在无DCP MLA路径从draft input_buffers.seq_lens构造独立CPU有效长度，真实行copy、padding行置0；不使用target上界再加Q。这是当前FIA需要Host列表导致的一次batched blocking传输，在forward/replay前进行，不应移进capture。
3. MRv2 FULL图的actual_seq_lengths_q累计query长度必须覆盖每个padding请求，例Q=8、padded B=4时为[8,16,24,32]；有效KV长度可以是[22666,0,0,0]。不能因为KV padding为0就截短captured Q，也不能把query累计长度当KV长度。external_flashmla对象在该更新helper中跳过，不对其强套FIA字段。
4. DCP委托专用manager，GQA/SFA等分支不同；不把无DCP MLA的Host长度方案推广到所有backend。非FULL forward可能处理padding输入，但metadata只消费真实请求token数量。

## 缓存组与写入地址

MRv1从模型声明的draft attention层与实际kv_cache_groups求交，保留每组表和slot；UniformType组要先取该层spec。kernel逻辑block size可能不同于共享allocation的物理页大小，不能用physical page size计算逻辑token slot。共享元数据覆盖为per-group表后若需要滑窗，要再次应用[读窗口规则](../../guides/integration/vllm_ascend_draft_kv_window.md)，写slot仍保留绝对位置。

MRv2 get_draft_context_group_layout按加载模型的层顺序返回group映射；多组没有显式map、map长度不等层数、没有真实draft attention层时拒绝。不能借target、indexer或从层编号猜的block id填入草稿组。P侧MLA context初始化校验use_dcp=False，且实际draft attention配置的PCP/DCP均为1；descriptor tap次序/hidden size/prompt长度及[num_tokens,feature_width]的BF16特征也须匹配。复制草稿可能使用独立CP配置，不能把此局部条件反推为target全局拓扑限制。

chunk slot helper用绝对position=token_offset+i，在每组分别算block_ids[position//block_size]×block_size+position%block_size，再按draft层顺序组织列表。它检查组集合、容量、正block size和非负block id；投影并写入后有当前NPU流synchronize，不能在通知远端可读或重用页之前省去完成边界。这里仅读初始化helper，不表示完整传输/取消/代际隔离协议已关闭。

## Dummy、DP/PCP与修复验证

MRv1 dummy每组context/query slot清为-1，避免写入上次真实请求缓存。MRv2 replicated PCP先广播骨干hidden再顺序采样，propose在复制草稿、adaptive或特定profiling路径重新协调draft DP shape；不能复用不同token数的target sync state。LM-head行padding与attention query padding分别遵守各自容量。

修复后检查两种anchor布局、接受/拒绝边界、同一请求连续步的有效长度刷新、零实际请求但非零padding、FULL/eager对照和不同组block size。监测读slot均已写、query累计长度与captured shape一致，且dummy不改真实cache。所引UT用mock/CPU表达这些合同，本次未执行；完整kernel、设备同步时序和真实PD仍待验证。失败先停用草稿并恢复已知缓存/图配置，不删除容量guard或用target上界掩盖缺失长度。
