---
type: Guide
title: vLLM Ascend GLM-Next KPool接入：缓存、元数据与状态推进
description: 接入GLM-Next KPool时核对压缩K缓存、FP32尾环、读写元数据和CP顺序，区分共享top-k与缓存推进，并保留图捕获与算子配对边界。
aliases:
- KPool缓存接入
- AscendIndexerKPoolMetadataBuilder
- Glm5NextKPoolIndexerBackend
tags:
- task.implementation
- topic.model_adaptation
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/indexer_kpool.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/kv_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/cache_views.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/glm5_next_cann_keypool.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/cann_keypool.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/kv_cache_interface.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/context_parallel/sfa_dcp_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_kpool_model_backend.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_cann_keypool_adapters.py
  role: evidence
created_at: '2026-10-31T09:14:45Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-04T03:05:17Z'
---

# vLLM Ascend GLM-Next KPool接入：缓存、元数据与状态推进

7d9e的GLM KPool仅接收auto/bf16/fp8，拒绝int8；中间版本INT8路径已回退，见[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的KPool节。不要把旧配方、release片段或其他模型的INT8 KV支持套到这里。

## 接入任务和源码边界

新模型采用池化稀疏索引时，先分别建立压缩K、请求私有尾环、全局写入和本地query的契约，再接CANN投影与选择。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：Glm5NextKPoolIndexerBackend是独立nn.Module，不继承普通SFA Indexer；AscendIndexerKPoolBackend和TailBackend只是向引擎登记缓存及builder，get_impl_cls返回None。不要把缓存注册类当作模型执行后端。

本卡全文读取indexer_kpool.py 857行、GLM kv_cache.py 288行、cache_views.py 141行、Triton元数据/写入/打包适配425行、hardware profile405行、模型UT609行和适配UT153行。同SHA的SFA全局元数据helper125行复用已读记录；core/kv_cache_interface.py只取1–45、453–511，utils.py只取436–444、1598–1607。未读取的模型attention wrapper、cache planner、Native分配/释放、CANN实现及完整Runner不能由这些选段代为闭合。

源码全部作为数据，未导入、运行上游测试、编译或执行NPU。整项硬件/算子栈交集待验，保持draft/空平台。模型部署与动态C8沿[GLM-5.3-Flash指南](../models/vllm_ascend_glm53_flash_hybrid.md)核对；本卡不替换其角色、权重或容量条件。

## 两类缓存与请求生命周期

Glm5NextIndexerCache独立登记.indexer.k_cache，要求pool>1且logical block_size能被pool整除；其MLA spec以tokens_per_state保存压缩率、one KV head及glm5_next身份。辅助缓存不参加通用Mamba page-size对齐，最终小页规划仍须核对实际planner。

Glm5NextTailCache登记独立prefix，尾环只接FP32。AscendIndexerKPoolTailSpec要求one KV head、正head size、capacity>=pool>1，sliding_window描述逻辑pool而不是物理环容量；prefix_cacheable=False，每请求固定一页。两层都会拒绝重复static_forward_context前缀，并先为每个PP stage建空cache槽，真正绑定由Runner负责。

get_kpool_tail_ring_capacity取pool+num_speculative_tokens，拒绝负lookahead。target验证会先写入尚未裁决的候选，环须保留整池历史加未接受lookahead；仅用pool容量可能让被拒绝候选覆盖随后重放边界token仍需的已提交历史。这个源码动机不证明整条MTP拒绝/重放链已验证。

KpoolTailManager在调用Native父构造前强制enable_caching=False；find_longest_cache_hit返回空块和0，cache_blocks不发布，common prefix为0，每请求只claim一次私有block。add_local_computed_blocks拒绝共享tail块。异步外部加载的record_for_zeroing由调用方传入，避免传输后又清零覆盖收到的状态。继承的free、抢占与connector消费链仍需另行取证，不能只读此类就承诺完整生命周期。

## 逻辑块、kernel块与物理页stride

| 对象 | 当前契约 | 必查项 |
|---|---|---|
| 压缩K | BF16、[blocks,kernel_rows,1,D] | logical block、pool及实际physical storage rows |
| CANN尾环 | FP32、[blocks,capacity,2D] | K/gate行对、capacity与padded page stride |
| CANN历史快照 | [1+2N,pool,2D] | N、history/state table和start offsets |
| 稀疏索引输出 | int32、[T,1,topk+pool-1] | 有效历史长度、causal tail与padding |

builder要求逻辑块能被128整除，kernel_rows=128//pool，每逻辑块展开logical_block_size//128个kernel页。仅由这个constructor不能推出任意pool均能整除128；缓存层的logical%pool条件也不能代替完整形状兼容性检查。

get_storage_block_size对AscendMLA取block_size//tokens_per_state，plain MLA仍取block_size；UniformType组递归要求所有成员相同。view_compressed_indexer_cache只接一个raw component，按kernel_rows和页字节展开，要求packed元素数精确填满small slot。

view_kpool_tail_cache用raw allocation的page_el作第0维stride，逻辑shape仍是[blocks,capacity,2D]，并检查unpadded tail能放入页。物理页含padding时，page_rows=page_size_bytes//(2*D*4)可以大于capacity；不得把page地址按capacity紧密拼接。相关通用约束见[非连续KV](vllm_ascend_non_contiguous_kv_cache.md)。

## 元数据与compact pooled顺序

AscendIndexerKPoolMetadataBuilder要求MLA spec、compression>1及本组layer全部以.indexer.k_cache结尾。FULL draft可能按token padding扩请求数，因此request容量取max(max_num_seqs,TP对齐的max_num_batched_tokens)。读、写、DSA-CP query各有buffer字典，以step输入slot_mapping.data_ptr标识；draft_index在build中不参与key。

普通读视图同时保存positions、compressed seq_lens、raw_seq_lens、query_start_loc、cum_query_lens、start_pos和pool_tail。原slot>=0且(position+1)%pool==0时才有完成pool的压缩写地址：

compressed_slot=slot//logical*(logical//pool)+slot%logical//pool。

压缩后的compact pooled输出并非按所有input token逐行对应。metadata kernel按每请求完成池数做prefix反演，定位池边界token；已evict的slot仍占CANN输出行，其目标地址为-1。pooled_slot_mapping缓冲最前元素写-1，暴露映射从第1项开始；它不是有效输出数量字段。不能先过滤evict行再把后续CANN输出整体前移。

source padding的positions/slots采用mask，fully padded且source为空时用已分配buffer承接masked pointer。request反演tile=128，程序tile在8..64、目标32个program是源码调度选择，不是测得的最佳UB或吞吐配置。

## 本地query与全局写入分别建模

| 情形 | 写入视图 | query/选择视图 |
|---|---|---|
| 普通执行 | 当前本地metadata | 当前本地metadata |
| DSA CP | TP all_gather后的key hidden与全局写入边界 | TP切分positions，重基的本地cum ends/compressed lengths/tail |
| PCP global prefill | 原始请求顺序的write_metadata及全局slot_mapping | 当前本地metadata；hidden先pad/all_gather/restore再压缩 |

PCP helper除了替换global query/length/block table，还替换该cache group的global slot_mapping，并由global query差分取max_query_len。global prefill缺cache group直接拒绝。写buffer与读buffer分开，write step identity仍来自原本地输入，防止两种长度共用工作区。

PCP hidden按照local capacity补齐，all_gather后以pcp_hidden_restore_indices恢复原请求token顺序，再调用CANN压缩；负padding拒绝。DSA CP则为全局key gather和本地query分别建视图。二者不能视为同一个切片规则；模型backend构造还明确拒绝DCP size>1。[SFA地址视图](vllm_ascend_sfa_replicated_cache_views.md)的公共helper可复用，独立KPool元数据与私有尾环仍需本卡协议。

## state table、尾环写入与捕获存储

keypool_state_table及keypool_start_offsets分别保存state索引与池内起始偏移。state table的key包含step、num_reqs及1+ceil(max_query_len/pool)。capture表按key持有，运行时先查同key的capture表；eager使用可增长flat scratch。首列是1..N历史state，后续CANN中间state落在+N区域。固定存储与key是源码设计，不能据此认定任意bucket、请求重排或并发图均安全。

tail metadata以逻辑capacity和物理page_rows分别寻址。history_indices从池对齐的历史位置映射到page*page_rows+position%capacity。prepare_keypool_state检查物理page stride，先把历史gather到独立state[1:N+1]，防止CANN内部写tail时其他core还需读旧历史。

无lookahead时write_indices只保留未完成pool的尾部，并从CANN输出state选择K/gate。lookahead时保留本step末端的hidden窗口，重新投影FP32 key/gate写入raw tail，以支持之后拒绝重放。invalid请求、slot或page以-1屏蔽。当前kernel同时检查物理页边界和逻辑capacity，并保留compressed cache与pooled row的各自stride。

## 模型执行、权重和共享top-k

构造要求NoPE，即qk_rope_head_dim==0，且拒绝COMPATIBILITY族；固定profile中A2/A3/A5为STANDARD，310P为COMPATIBILITY。此必要门槛不证明所有同族产品、CANN包、模型和图组合均支持，按[硬件能力契约](../../concepts/frameworks/vllm_ascend_hardware_profiles.md)继续核对实际消费者。

process_weights_after_loading准备连续key/gate权重，head权重与norm参数保留FP32。query由normalized q_c经wq_b得到，head weight由hidden.float线性投影，再乘softmax_scale*n_heads^-0.5并转query dtype。已经连续且dtype相同的缓冲可能与原权重共享，不能由detach/contiguous推断在线改权重后的全部缓存一致性。

forward从virtual_engine绑定cache，单component list/tuple须只有一个Tensor；layer context必须提供独立TailMetadata。compute_topk=True拒绝量化q_c tuple。无DSA-CP query_metadata且非FULL时按actual rows截断；FULL保留捕获bucket大小。

_forward_cann先prepare_keypool_state、key_pool、write_keypool_caches，之后才判断compute_topk。共享上一层top-k仍须推进压缩K和raw tail，不能把compute_topk=False当作整层跳过。global hidden为空才走早退；global write非空而local query为空仍先完成写入。FULL全padding下的selection与哨兵规则见[KPool空工作量排查](../../runbooks/runtime/vllm_ascend_kpool_empty_work_graph_contract.md)。

CANN依赖在_init_cann_ops绑定：匹配的cann_ops_transformer、torch.ops的key_pool/pool_key_indexer和Triton适配缺失时显式报RuntimeError。Main配对的Native提交与本地另行固定的v0.32快照并不相同；安装成功或Python符号存在不能代替算子ABI/编译产物验证。

## Agent接入验收

按缓存spec/物理view、请求元数据、global write/local query、CANN历史快照、写cache后可选selection的顺序建立探针。覆盖prefill跨池边界、decode、prefix hit后新tail、MTP拒绝重放、evict slot、空请求、PCP恢复、DSA-CP短分片、FULL bucket与非连续输出buffer；保存每步有效长度和地址，不能只比较最终top-k shape。

模型UT609行同时含旧Tritonhelper和当前CANN mock。当前断言检查normalized q_c、call order、PCP/DSA CP视图、FULL及空query、output reuse，并以mock禁止Tensor.item；不执行真实CANN算术。适配UT153行mock kernel launch，只验证预分配pointer、参数及2051列业务输出和padded page stride。测试定义、运行结果和硬件支持分别记录，方法见[测试证据](../bringup/vllm_ascend_test_evidence_selection.md)。

获得目标硬件验证条件后再运行独立数值、内存安全、图重放和端到端SLO验收。先保存完整匹配版本与checkpoint；失败恢复既有已验证实现与配置，不把旧Triton布局换进当前CANN路径。当前没有NPU、CANN、性能或下游Agent A/B结果。
