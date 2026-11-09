---
type: Guide
title: vLLM Ascend V4.1 缓存规划：共享block池、packed页与视图偏移
description: 接入V4.1缓存时区分scheduler组、物理slot和全局block池，核对packed字段、K与scale及folded偏移、页面stride和准入成本，避免容量错算与覆盖。
aliases:
- get_layer_tuples
- get_deepseek_v41_kv_cache_config
- make_folded_index_cache_spec
- V41缓存池
tags:
- task.implementation
- topic.kv_cache
- topic.memory
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/cache_config.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/deepseek_v41_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/kv_cache_interface.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/attn_utils.py
  role: implementation
created_at: '2026-10-31T06:05:01Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T06:12:40Z'
---

# vLLM Ascend V4.1 缓存规划：共享block池、packed页与视图偏移

## 接入任务与证据范围

为新模型接入V4.1缓存或定位容量/覆盖问题时，先列出逻辑资源、scheduler group、物理slot及全局block ID，再对齐spec、allocation和实际view。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的cache_config.py297行、KV接口551行、缓存UT1964行和测试参考345行全文；Runner只读V1 _adjust_kv_layout及V2 _adjust_dsv4_kv_layout/_reshape_kv_cache_v2的完整方法。来源均作数据阅读，没有运行测试、模型或NPU。may_override_num_blocks按vLLM精确0.32.0走kv_cache_utils，其他lane走kv_cache_planning；这是固定源码分支，不保证任意vLLM版本均兼容。

它与[DSV4 KV计划](vllm_ascend_dsv4_kv_plan_contract.md)的608字节tile/TurboQuant接口不同，也不把[CLA共享层](../../runbooks/runtime/vllm_ascend_cla_kv_sharing_forces_chunked_prefill.md)的同一份KV别名等同池内资源复用。部署范围见[V4.1模型边界](../models/vllm_ascend_deepseek_v41_platform_boundary.md)，恢复状态见[SWA回放](vllm_ascend_swa_bounded_replay_contract.md)。整项硬件与真实kernel ABI未验证，保持draft/空平台。

## 三种数量分别计算

get_layer_tuples按真实名称把long KV、配对index K/scale及可选folded view放到同一物理slot的不同字节区；compressor state、target SWA与draft SWA可以别名该slot，物理页容量取连续资源字节和与各别名需求的最大值。full source与target/draft层按各自层号排序，不凭字典输入顺序决定地址。

group_cache_specs将物理tuple转置成scheduler group：每个target SWA组从每个物理slot取一层，draft另成组，MLA与state也有各自组。用replace生成padded specs，保留原spec不变；scheduler group数量、同一ID的物理slot数量、池每ID总字节数不能互换。不同仍活跃group使用不同全局block ID，不是同一个活跃ID上任意覆盖别名资源。

get_deepseek_v41_pool_bytes_per_block把各slot的page_size相加。get_deepseek_v41_kv_cache_config以available_memory//该和算capacity，再调用当前Native may_override_num_blocks；每个slot分配num_blocks×page_size，descriptor的offset/layer_stride为0、block_stride为该slot的page_size。override需另核真实语义，不由一个向下覆盖的测试推导任意上调都安全。

若模型只有SWA且无full-context source，每层独立slot；不能强行套有long/index source的复用图。命名解析、配对index、非空成本、SWA列分布等前提要在接入时验证，直接索引/zip和局部assert不等于完整异常输入schema。

## 可复核的容量例子

CPU参考配置是40层、KV source为2/8/14/20、index source另含24/28/32/36，block128、head512与index128。它产生51个逻辑资源、12个scheduler group、4个独立物理slot；每个全局ID的池成本为540928字节，即3×131072+147712，不是12×540928。

该例加3个draft SWA层后成为13组、54资源，仍复用4个物理slot，每ID总成本不变；但每请求block需求可增加。不能把这句话扩为整个drafter零新增HBM，模型权重、context投影、激活、工作区与并发需求仍需单算。具体数字只属该测试几何，不作为所有V4.1 checkpoint或block size常量。

## packed cache字段与物理字节

uses_a5_packed_cache查当前profile的DSV41_PACKED_CACHE能力，不直接给出所有SKU支持表。packed分支要求MLA/SWA head=512、index head=128，不匹配显式ValueError；这是固定packaged ABI宽度guard，不能把配置改宽来凑通过。

| 工厂 | packed字段算术 | 后续核对 |
| --- | --- | --- |
| make_swa_cache_spec | 512个FP8值+16个BF16 scale，head_size=544、dtype=uint8、cache_dtype=a5_mxfp8_bf16_scale。 | 窗口、block rows、实际writer/attention采用同一布局。 |
| make_mla_cache_spec | 512个FP4值占256字节，再加32个BF16 scale共64字节，head_size=320、dtype=uint8。 | tokens_per_state为压缩比；默认scale_dim=0，scale_dtype字段本身不再增加一平面。 |
| make_index_cache_spec | head_size=64个uint8 K，scale_dim=4、scale_dtype=uint8，共68字节/物理行。 | 与nonpacked int8 K+一个FP16 scale的路径分开。 |
| make_folded_index_cache_spec | 8×68=544字节/折叠行，tokens_per_state=8；block_size必须整除8。 | 第三view偏移和QSLI调用方，不能只从工厂存在推运行激活。 |

AscendMLAAttentionSpec.real_page_size_bytes按物理行×KV heads×(head_size×dtype字节+scale_dim×scale_dtype字节)计算；物理行对Ascend MLA是logical block_size//tokens_per_state。Native可选storage_block_size不是这里的派生行数，不能把已经变小的物理block再次除压缩比。SWA自己的compress_ratio、window与bounded_replay也要保留。

spec merge核对量化/scale/压缩/布局与causal等一致性；SWA合并还保留window、extra_retained_tokens及bounded_replay，optional字段按构造函数显式声明传递。相同shape或继承同一MLA基类不保证可放同组，target因果和非因果draft尤其不能合并。

## Runner视图与folded第三偏移

V2 _reshape_kv_cache_v2先从KVCacheConfig descriptor获得V4.1每层block_stride，再构造view；index起始偏移为long KV未补页字节数，scale接在该index K后。folded K必须再加split index K/scale的未补页字节数，成为第三view。把folded从offset0建立会覆盖long KV，不是可接受的共享。

_adjust_dsv4_kv_layout把raw storage_offset的字节与initial_offset相加，按dtype检查对齐，再用page_size/dtype_size作为首维stride；其余维为逻辑shape stride。V1方法委托make_page_strided_cache_view，不能由方法名断言所有allocator、backing或传输范围已闭合。逻辑numel、连续payload和物理页stride分别记录，相关原则见[非连续KV接入](vllm_ascend_non_contiguous_kv_cache.md)。

缓存UT包含非零raw offset、int8 backing、相邻页隔离和V2 folded block32/64/128写入检查。通用测试allocate_cache_views主要建普通long/index/SWA视图，没有专门folded偏移规则；folded测试改用生产V2 reshape。因此不要把一个golden helper的能力泛化成所有缓存格式。

## 测试证据与Agent验收

1964行文件的61个测试定义覆盖规划、组重排、回收ID、容量/准入、压缩坐标、共享metadata、CP与SWA读下界等多个层面；模块有Native配置importorskip，CPU fixture替换NPU norm/pin与native metadata/collectives。它们是验证设计，未由本次执行，亦不证明所有压缩器、CP、图或packed kernel正确。

先保存各层spec/role、scheduler group→全局ID、physical tuple、page成本、原始buffer地址/offset、typed view shape/stride及K/scale/folded间隔。以同一全局ID跨不同slot核对地址，再检查不同活跃group的ID隔离、释放后复用、PAD、非连续block table和draft附加组；不能只比总分配字节或指针数量。

选择实际非packed/packed能力与checkpoint后，核对builder恢复的logical block size、corrected device seq_lens、每组slot与reader/writer接口，再加入capture/PCP/PD等组合。先验证数值和隔离，后比较可用block数、峰值HBM和吞吐；失败恢复匹配版本和整套spec/allocation/view，保留缺key/错位错误，不截断head或吞异常掩盖布局分歧。
