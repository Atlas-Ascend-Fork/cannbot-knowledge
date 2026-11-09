---
type: Guide
title: vLLM Ascend GLM-Next缓存规划：双页类、分组与容量
description: 接入GLM-Next时按主MLA与压缩Indexer的共享组、独立尾环和Mamba组规划两类物理页，核对PP本地slot、全局block容量与版本builder钩子，避免重复预算折扣。
aliases:
- GLM-Next缓存规划
- get_glm5_next_kv_cache_groups
- get_glm5_next_pool_bytes_per_block
- get_glm5_next_kv_cache_config
tags:
- task.implementation
- topic.kv_cache
- topic.memory
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/cache_config.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/kv_cache_config_builder.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/kv_cache_interface.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/kv_cache.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/cache_views.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_cache_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_kv_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_glm5next_pooled_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_glm5next_pooled_cache_write.py
  role: evidence
created_at: '2026-10-31T09:34:04Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T09:42:18Z'
---

# vLLM Ascend GLM-Next缓存规划：双页类、分组与容量

## 消费任务与证据边界

GLM-Next混合注意力接入、长上下文容量评估或PP worker缓存初始化时，先确定scheduler group、物理tensor slot与block ID的关系，再算HBM预算。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2；本卡全文读取cache_config.py 464行、builder22行、缓存view141行及UT280/851/388行和NPU测试定义239行。缓存层288行复用同SHA全文记录；worker1514行只取771–864，platform2057行只取128–130，utils1922行只取724–745，core551行仅取1–45、147–169、453–511。

Native helper、UniformType merger、完整Runner分配/释放及CANN实现没有由这些源码闭合。全部文件作为数据，未导入、运行上游测试、编译或执行NPU；整项硬件与实际版本配对待验，保持draft/空平台。已有[KPool缓存接入](vllm_ascend_glm_next_kpool_cache_contract.md)负责query/write/state推进，[空工作量排查](../../runbooks/runtime/vllm_ascend_kpool_empty_work_graph_contract.md)负责PKI哨兵和图重放；本卡负责规划控制面。

## 先识别三类attention spec

get_glm5_next_kv_cache_groups要求存在model_version=glm5_next的spec，并要求hybrid KV manager开启。主MLA是MLAAttentionSpec且tokens_per_state==1，压缩Indexer是同类且ratio>1，tail必须是AscendIndexerKPoolTailSpec、glm5_next及cache_role=indexer_tail。存在任一GLM attention类别却缺其他两类时拒绝，不能只登记一个Indexer cache就进入通用布局。

_create_glm5_next_attention_groups要求每层恰有main/indexer/tail三者，full logical block size统一且能被Indexer ratio整除，tail ratio一致且capacity>=pool。numeric layer index要两两对应；attention的synthetic非数字名可保留注册顺序，但Mamba分组另有数字索引要求。unsupported cache role与不匹配数量直接报错。

| scheduler组 | layer顺序与ID | 物理页类别 |
|---|---|---|
| combined full-history | main、indexer逐层交错，main放第一项；两者共享该组block IDs | main用大页类，indexer用小页类 |
| tail | 独立UniformType固定环组 | 小页类，block ID独立分配 |
| 各Mamba组 | 独立scheduler groups | 大页类，各组独立分配ID |

main-first使scheduler解包第一个nested spec时选择FullAttentionManager。共享物理backing的组仍须拿不同block ID；不能把“共享tensor”解释成它们可同时写同一逻辑页。

## 双页类对齐与Mamba分组

_align_glm5_next_cache_specs分别计算两组最大值：main MLA加全部Mamba取page_size_bytes和unpadded/real size的最大值；Indexer加tail独立取最大值，再用object.__setattr__写各spec.page_size_padded。已有较大padding会保留。不能把全部组统一成一个最大页，也不能只看元素payload忽略实际padding。

_group_glm5_next_mamba_layer_names按数字layer index恢复连续recurrent runs，不依赖dict插入顺序。它拒绝同一个layer同时含MLA/Mamba或含多个Mamba spec；取最大连续Mamba run长度作为group数，再把排序后的Mamba名按offset::max_run_length分组。这个group数不是简单的Mamba层总数。

standalone MTP保留full与tail两组，没有Mamba也合法。_get_glm5_next_cache_layout识别到GLM后要求恰好一个combined full组和一个tail组，其他只能是Mamba；遇未支持组拒绝，不能静默套用GLM公式。

## PP本地slot与全局规格

PP投影可能保留空layer_names组及其全局nested specs。page size类从这些保留spec派生，slot数只由本worker实际layer_names决定：

main_slot_count=max(本地MLA层数, 每个本地Mamba组的层数)，
small_slot_count=本地Indexer层数。

只含Mamba的worker可以没有main/indexer/tail本地层名，仍有main slot且small slot为0；UT有对应定义。全空worker的bytes_per_block和上游调用guard没有在这里闭合，不能由这个Mamba-only例外推所有空stage安全。

## 容量按物理block成本核算

get_glm5_next_pool_bytes_per_block返回：

bytes_per_block=main_slot_count*main_page_size+small_slot_count*small_page_size。

get_glm5_next_kv_cache_config先取available_memory//bytes_per_block并clamp到至少0，再调用Native may_override_num_blocks。override如何验证、是否允许超过可用预算及外层admission要另查实际版本；这里不承诺设置override仍能装下。

每个slot描述成标准unpacked KVCacheTensor：size=page_size*num_blocks，offset=0，layer_stride=0，block_stride=page_size。每个main slot可被一层MLA和各独立Mamba组相应位置复用；每个small slot由对应Indexer与tail共用backing。它们从全局BlockPool独立分配ID，因此物理叠放与逻辑状态隔离同时成立。

get_glm5_next_max_memory_usage将每个组的ceil(max_memory_usage_bytes/page_size_bytes)相加，再乘完整physical bytes_per_block。不能只取最大组所需block数，也不能把所有层payload相加代替实际slot成本。prefix、tail和Mamba的具体需求仍来自各spec接口；这份缓存容量之外另计模型权重、激活、workspace、通信、图及运行时预留。

旧[DSA显存预算](../../optimizations/rules/dsa_decode_memory_budget_indexer_cache.md)提醒主KV之外还要计Indexer cache和权重，其DSV3.2-exp约4GB/0.85B是特定来源例。它不提供当前GLM两类页、组间ID和tail状态的物理成本公式。

## Worker预算与版本builder接口

_scale_kv_cache_memory_for_multi_group在普通多组折扣前，检查nested spec的model_version属于deepseek_v4/deepseek_v41/glm5_next；命中后直接保留available_memory，原因是模型planner已按共享物理池核算。GLM这条早退不依赖runner.use_sparse=False，不能对稀疏GLM再打一遍通用折扣。

普通非GLM分支仍有standardized backing、layout compact、Mamba/Step或V2 full/sliding条件，以及不使用sparse/compress等检查；最终fallback按最大group pages/sum(all pages)缩放。此处只读该完整函数，不表示已验证所有Worker模型组合。

AscendKVCacheConfigBuilder的_get_pool_bytes_per_block对识别出的GLM layout返回双页类成本，否则委托Native父类。NPUPlatform的get_kv_cache_config_builder_cls返回这个路径；父类hook存在及调用时序必须与目标Native配对核对。

cache_config.py对vllm_version_is("0.32.0")从kv_cache_utils导入create_kv_cache_group_specs/may_override_num_blocks，其他版本从kv_cache_planning导入；新builder22行自身又从kv_cache_planning导入DefaultKVCacheConfigBuilder。不能只看到一个0.32分支就认定整条Main builder链在0.32都存在。

vllm_version_is缓存结果，优先env VLLM_VERSION，否则读vllm.__version__，用Version(parsed.public)比较并剥离PEP440 local suffix；invalid version报错。手动改版本字符串只改变选路，不补齐缺失API/ABI。版本覆盖与缓存判定的消费边界见[插件版本判断](../../concepts/frameworks/vllm_ascend.md#vllm_version只改变版本判断输入)；Main实际配对与本任务冻结的Native快照仍须分别核对。

## view、测试与Agent验收

requires_padded_page_layout是池级判断：存在MambaSpec、至少一份Mamba spec带page_size_padded，并存在indexes_kv_by_block_stride。单独tail或普通Mamba padding不足以进入这条共享物理页状态布局。每个view的第0维stride要等于物理page bytes；NoPE可有零宽rope view，不能因逻辑Tensor连续就丢弃physical block stride。

| 已读测试定义 | 可支持的源码检查 | 不支持的结论 |
|---|---|---|
| cache config UT280 | pool4/16、两类页/描述符、standalone MTP、Mamba-only PP、缺pair/不可整除拒绝、sparse/packed worker预算 | Native builder hook使用importorskip/hasattr时可能skip，未实际运行 |
| KV UT851 | 私有tail/spec与free计数、PCP/DSA CP视图、stable draft buffers和expanded pages | 文件fixture mock元数据/尾部kernel；不证明真实CANN/NPU或Native释放实现 |
| Worker UT388 | CPU raw backing复用、reshape/bind、padded页stride、offset与不同block ID隔离、V2 tail view | 未运行，不代表完整Runner、connector或并发访问通过 |
| pooled write e2e239 | NPU元数据、大position、CP start、改变write row width、padding/stride与graph/in-place 2051列索引 | 没有显式硬件family guard不等于全部硬件通过，也不测试完整key_pool数值 |

Agent应保存spec类别、每组layer顺序/数字索引、两种page bytes、本地slot数、组间block ID、描述符layers与stride、可用缓存预算和override、目标Native hook身份。先用独立算术核对实际分配总字节，再验证跨组不同ID互不覆盖、prefix/tail/MTP与PP配置；最后测目标硬件质量与SLO。失败恢复完整已验证配置，不能关闭hybrid manager或改model_version绕过契约。当前没有NPU、实测HBM、性能或Agent A/B结果。
