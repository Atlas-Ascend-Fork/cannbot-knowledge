---
type: Guide
title: vLLM Ascend 混合缓存补丁：命中对齐、状态分配与 dtype 解析
description: 核对Hybrid coordinator的可缓存/私有组、DCP与Mamba粒度、Eagle丢块、PD consumer split、310P页padding，以及platform/worker的Pydantic dtype扩展差异。
aliases:
- AscendHybridKVCacheCoordinator
- AscendMambaManager
- _skips_eagle_block_drop
- _mamba_block_aligned_split
- _widen_cache_dtype_literal_for_worker
tags:
- task.implementation
- task.debugging
- topic.kv_cache
- topic.precision
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_kv_cache_coordinator.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_mamba_block_aligned_split.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_mamba_config_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_mamba_manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_replayssm_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_indexer_kv_dtype.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_kv_cache_dtype.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_kv_cache_dtype.py
  role: implementation
created_at: '2026-11-03T05:18:49Z'
updated_at: '2026-11-03T05:18:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 混合缓存补丁：命中对齐、状态分配与 dtype 解析

## 固定范围与兼容入口

固定 ceac1a2 八个补丁按整文件AST投影检查全部程序语句，未应用补丁、运行Pydantic、分配KV或执行NPU。Hybrid manager、缓存dtype parser、实际量化kernel分别是独立合同；解析接受int8/mxfp8不代表目标attention具备相同布局或数值支持。相关[输入元数据](../../concepts/frameworks/vllm_ascend_input_attention_metadata.md)、[Mamba加载复制](vllm_ascend_mamba_kv_load_copy_contract.md)和[抢占恢复](vllm_ascend_preempt_kv_preservation.md)继续各管自己的阶段。

## 可缓存组、私有tail与实际token预算

工厂按is_prefix_cacheable统计组。含DeepSeek V4/V4.1标识或同时有可缓存与私有组时选AscendHybrid；无可缓存、单组或关闭caching时委托原coordinator，并对零可缓存组复制config/展开Uniform spec以禁前缀缓存。私有组不能靠一个hash命中复用。

token_budget优先max_in_flight_tokens，否则max_model_len，两者不是无条件同值。实现忽略传入PCP并对子manager传PCP=1；这是其内部管理合同，不自动证明任意PCP拓扑已支持。开启caching的Mamba有效块不乘DCP，其他组按DCP扩粒度；MambaManager.find_longest_cache_hit还固定dcp_world_size=1，不能将递归state当普通KV按DCP均分。

相同spec仅在manager类也相同才合组，FullAttention优先；不可缓存tail把compress_ratio纳入tail alignment。命中对齐为hash/scheduler粒度与tail的LCM。DCP1、Mamba align且block>hash时存在partial hash hit路径；allow_partial_hash_hits保存在实例，但该局部enable条件还需沿继承消费者核对，不能只看配置字段就宣称所有局部路径关闭。

find_longest_cache_hit迭代协调各组hit，FullAttention可重用前轮结果，Eagle checkpoint校验随缩短重新考虑；返回blocks、共同hit和最长局部hit差值。全局共同hit不等每组最大hit，per_group接口另返回向量；最终FullAttention blocks按ceil(hit/effective_B)裁剪。私有tail不参与普通hashlookup，但仍约束对齐。

## Eagle、PD与块边界不能只按use_eagle布尔判断

_skips_eagle_block_drop在没有KV transfer或纯producer时为真，consumer/both为假；coordinator从KVCacheConfig附带属性读取该信息，调用方需确认实际是否附带，不能用外层VllmConfig配置存在推同一对象已设置。

_mamba_block_aligned_split在纯PD consumer且已有computed prefix时直接返回新增token预算；KPool场景按最后完整cache位置限制chunk，是否退一个Eagle块再看上述角色规则。其他skip-drop场景临时关闭存在的use_eagle/use_eagle_block_drop字段，finally恢复。补丁先严格比对原方法参数名tuple，签名不符即RuntimeError，不是兼容任意Native版本的软fallback。

AscendMambaManager在有external tokens且本轮还调度新token时，父分配预算另加一块；不能只按local hit块数估显存。local hit、total computed与main-model tokens是不同单位/阶段，错误地互代会让余量判断失真。

## 310P hybrid页和RecoverSSM验证

310P配置先走MambaModelConfig校验，MLA明确拒绝。以每token Attention页字节与完整Mamba state页字节计算Attention块，kernel对齐128；cache_mode=all还与模型chunk/显式Mamba块取LCM，align模式令Mamba block等Attention block。页不足时扩大block，再padding Mamba页到Attention页大小。能放入一页是容量条件，不证明支持所有hybrid算子或有相同带宽。

RecoverSSM补丁仅use_replayssm且is_glm_recoverssm_model时调用专属validate，再置use_kda_recoverssm=True并返回；其他模型委托原验证。它同时改VllmConfig方法、Pydantic model_validator绑定并rebuild_dataclass，不能只修改同名Python函数就认为构造验证已接通。模型/状态消费者仍按[RecoverSSM指南](../optimization/vllm_ascend_glm_kda_recoverssm.md)核对。

## platform与worker的dtype扩展区别

platform的CacheDType补丁在原类型同时已有int8/mxfp8时跳过，否则替为固定Literal列表；Native新加但列表未包含的类型可能不被保留。worker补丁则在当前args上追加缺项，并更新annotations、dataclass field及Pydantic schema；两条不能描述成完全相同的无损扩展。

IndexerKVDType在platform/worker分别追加int8并rebuild，worker还给mxfp8设置float8_e4m3fn映射并更新已可导入attention.selector引用。旧Native没有register_kv_cache_dtype API时才把fp8字符串翻为E4M3；有该API的分支此函数直接return，不表示这里完成实际dtype注册。父类schema、导入绑定、字符串到Tensor dtype及真实cache布局须逐层核对。

验证组数、可缓存性、共同/各组hit、Eagle角色、partial tail、DCP/PCP参数、external+new token额外块及dtype在父/worker解析一致；覆盖未知签名、Native新增dtype、纯私有组、页面padding和重复导入。静态patch存在或config构造成功不能替代全模型KV、递归state数值与性能验收。
