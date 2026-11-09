---
type: Guide
title: vLLM Ascend KVPP 物理分配：allocate_kvpp_cache、owner与双scratch预算
description: 沿 allocate_kvpp_cache 核对 PP 本地层与 TP×PCP 的 owner、main/indexer 连续 bundle、draft 隔离、双 scratch 复用及预算和对齐开销。
aliases:
- allocate_kvpp_cache
- KVPPPhysicalCachePlan
- build_kvpp_layer_layout
- register_kvpp_draft_layers
- map_kvpp_layers_to_owners
- _allocate_kvpp_buffer
tags:
- task.implementation
- task.debugging
- topic.kv_cache
- topic.parallelism
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/kvpp_cache.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/kv_cache_placement.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_kvpp_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_kvpp_cache_specs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_kvpp_cache_placement.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kvpp_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T02:11:25Z'
updated_at: '2026-11-02T02:46:13Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend KVPP 物理分配：allocate_kvpp_cache、owner与双scratch预算

## 消费任务与来源范围

新模型适配KVPP、增加draft或修改KV量化布局时，把逻辑cache spec、owner、连续bundle和真实backing分开核算，再检查attention view和传输是否使用同一span。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文阅读分配器57行、规划器207行、三份UT81/59/213行及辅助220行；Worker仅阅读640–682和1251–1307，config仅1–111，pin复用同SHA记录。

全部文件作为数据，未运行上游导入、UT、模型或NPU。Main所配Native pin与本任务独立Native快照不同，get_layers、spec继承、unify_hybrid_kv_cache_specs和dtype/split helpers的真实配对实现没有由本卡闭合。硬件、完整模型和ABI保持待验；[KVPP容量指南](../optimization/vllm_ascend_kvpp_capacity_tradeoff.md)的950DT测量不能变成本卡的全硬件证明。

本卡处理KVPP的持久层与两份scratch，不替代[V4.1物理池](vllm_ascend_v41_cache_pool_contract.md)、[GLM-Next双页类](vllm_ascend_glm_next_pool_planning_contract.md)或[SFA复制地址](vllm_ascend_sfa_replicated_cache_views.md)。相同block ID、共享backing或都含indexer，不构成这些模型planner能任意套用KVPP布局的证据。

## 先建立PP本地owner和真实draft归属

map_kvpp_layers_to_owners的输入必须已经是当前PP worker本地cache名称。KVPPConfig开启时size=TP×PCP，DP和PP不进入该所有权组。target按extract_layer_index得到的数字层号排序，同一层号的main/indexer共用owner；连续均衡分区，先分base个层，前remainder个rank再多一层。world size大于target层数时允许部分rank没有target所有权。

例如本地target层9–16分给3个owner时是3/3/2的连续分区，不按全模型层总数、字典插入顺序或hash分布。Worker预算入口使用PCP rank×TP size+TP rank构造KVPP rank；真正通信组与global rank关系仍需与目标进程拓扑核对。

register_kvpp_draft_layers在speculative_config不存在或use_eagle()为False时直接返回。其余情况下，非最后PP stage使用空draft集合；最后stage必须从已加载speculator.draft_attn_layer_names读取，缺失时报错。先检查shared_kv_cache_layers或模块kv_sharing_target_layer_name，draft共享到target时拒绝，再向本地cache模块设置_kvpp_is_draft。

find_draft_layers读取这些明确属性；模块不存在或未初始化属性时报错，不凭层号猜测draft。draft名称可以与target重复数字索引，也可以没有数字；它们不加入target owner映射，按各自名称独立分配持久缓存。测试辅助把若干方法判为use_eagle只是测试桩，不能据此宣布所有投机方法已通过Native真实路由。

## Spec归一化、组件字节和bundle顺序

create_kvpp_cache_allocation_plan浅复制worker_spec，拒绝任一非FullAttentionSpec或不同block_size。这个局部检查不是任意混合模型支持声明。Worker.get_kv_cache_spec先登记draft归属，再在use_eagle()且存在SlidingWindowSpec时复制并调用unify_hybrid_kv_cache_specs，让预算与engine组使用full-allocation spec；注释明确attention计算仍是windowed。不要直接把原始SlidingWindowSpec交给公共plan工厂，再用取消guard掩盖分歧。

get_kvpp_cache_specs从各组layer_names还原每层spec；UniformTypeKVCacheSpecs按层名解包，否则使用组spec。该实现依赖实际Native对象合同，不证明不同descriptor版本可任意互换。

| cache分支 | 每块组件字节来源 | 接入检查 |
| --- | --- | --- |
| AscendSFAIndexerCacheSpec | replicated size×block_size×KV heads×head_size×dtype bytes；有scale_dim再加独立scale组件。 | 主数据和scale的dtype与偏移分别核对。 |
| packed SFA main MLA | 直接使用spec.page_size_bytes作为一个组件。 | packed helper选路与真实writer/reader ABI另验。 |
| 其余cache | 先取MLA真实kv_lora_rank/qk_rope_head_dim、CacheOnly层宽度或普通head维，再按量化split factor拆page bytes。 | 非SFA且FA量化时用quant_config.get_kv_quant_split_factor，否则用calc_split_factor。 |

无法识别的MLA attention模块显式TypeError。这里读取调用关系和字节运算，没有完整分析所有imported helper、量化方法或自定义spec的内部实现；不能用相同shape代替字节合同。

build_layer_cache_bundles先按数字层号、是否Indexer、名称排序target，把同层组件放进一个bundle；draft按名字排序后以单层bundle追加。build_kvpp_layer_layout从字节cursor=0开始，逐组件追加num_blocks×size_per_block，没有逐组件alignment padding。主KV和indexer必须连续，runtime才可从首组件开始广播整个span。

## 双scratch按target执行序号复用

allocate_kvpp_cache重建计划和各bundle layout；scratch_size取全部target bundle字节的最大值。scratch_size>0就分配两份scratch，即使当前rank拥有所有target也如此。没有target、仅有draft时不分配scratch。

按bundle顺序遍历：owner缺失的draft与本rank拥有的target各自分配持久buffer；远端target选择scratch[target_index % 2]。每个target均推进target_index，包括本地持久target；draft不推进。它不是数字层号奇偶，也不是只数远端层或按远端owner rank取余。

各cache组件通过buffer.narrow(offset,length)产生raw int8 views，同一bundle内共享连续backing。共享scratch使多个非相邻target层会别名，计算与下一层预取必须遵守[KVPP调度合同](vllm_ascend_kvpp_runtime_contract.md)。不能将返回字典中每个层名误算为独立storage，也不能在早一层仍使用scratch时提前写入复用它的后续层。

## 物理预算、逻辑预算和对齐开销

KVPPPhysicalCachePlan.get_num_blocks以num_blocks=1计算每块成本。设P是本rank拥有的target与全部本地draft bundle总字节，S是全部target bundle的最大字节，则：

`bytes_per_block = P + 2 * S`

`num_blocks = available_bytes // bytes_per_block`，成本为0时返回0。公式没有额外的available_bytes非负校验，调用方需维持预算前提。空owner rank仍可能需要两份scratch；只计持久层会高估容量。

_allocate_kvpp_buffer先用torch.zeros申请size+2MiB个int8元素，再从(-data_ptr)%2MiB位置narrow出size长度的对齐view。每个独立backing多申请完整2MiB，返回view仍保有原storage；并非最多2MiB-1的底层申请，也不是torch.empty未初始化缓存。逐组件view没有再各自申请2MiB。

因此P+2S是payload的每块成本，未包含每份backing的这项固定申请开销。对正num_blocks且布局不变的本分配函数，payload之外还要按实际独立backing数量计对齐申请；零长度与其他allocator行为另验。Worker所读_apply_kvpp_memory_budget也没有在这个函数里显式扣除该项，不能把公式结果当实际峰值HBM上界。本卡没有复现OOM，也没有完整读取整个profiling/预留调用链。

Worker保留available_kv_cache_memory_bytes，若有物理plan则先取num_blocks，再返回num_blocks×sum(logical_cache_spec各spec.page_size_bytes)给上层。这个数是换算后的逻辑预算，不能又当真实物理申请字节，或再对同一共享存储重复施加节省比例。权重、激活、workspace、通信和运行时预留仍需独立核算。

## 已读测试设计与Agent验收

规划UT覆盖PP本地9–16层、world大于层数、main/indexer同owner、输入顺序变化、draft重号/无数字名、缺失归属与跨target共享拒绝，以及packed/unpacked、scale dtype和量化split。若干mock几何的每块预算为404/392/328字节、无持久target的rank为248字节；这些不是实际模型常数。

分配UT检查两份scratch别名、owner持久分配、main/indexer连续偏移、零初始化、独立storage字节加每份2MiB，以及三层DSpark draft写入不被target scratch覆盖。Worker spec UT定义归一化后的FullAttention预算路径，helper还根据Native dataclass字段选择旧shared_by或新layers/layer_stride descriptor。它们是CPU/mock测试设计，未在本次执行，不能替代真实Native兼容、NPU视图、并发传输或精度结果。

Agent应记录本地层/role、每层spec与block_size、TP/PCP/PP rank、owner、bundle顺序、组件dtype/字节、target ordinal、scratch别名和独立backing计数。先复算P/S、逻辑预算及固定alignment申请，再检查真实typed view的offset/stride和writer/reader边界；覆盖draft独立性、PP非末阶段、空owner rank、非零offset和连续两步scratch复用。数值与恢复通过后再测容量、峰值HBM、传输尾部和SLO，不能从绑定成功或检索通过推断性能收益。本卡无NPU、精度、性能或Agent A/B实测。
