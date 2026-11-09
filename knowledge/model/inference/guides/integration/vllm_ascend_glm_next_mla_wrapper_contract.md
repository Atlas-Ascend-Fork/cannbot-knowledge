---
type: Guide
title: vLLM Ascend GLM-Next MLA接入：NoPE、索引器与权重路径
description: 接入GLM-Next MLA时沿模型投影、MLAModules和IndexerWrapper选择Ascend后端，保留checkpoint参数名、NoPE条件与缓存身份，核对包装层兼容参数和真实执行入口。
aliases:
- GLM-Next MLA接入
- Glm5NextMLAAttention
tags:
- task.implementation
- topic.model_adaptation
- topic.attention
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/attention.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/mla.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/indexer_kpool.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/kv_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/kv_cache_interface.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_indexer_backend.py
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

# vLLM Ascend GLM-Next MLA接入：NoPE、索引器与权重路径

## 接入路径与源码范围

模型接入时按Glm5NextMLAAttention→MLAModules→平台MLA wrapper→IndexerWrapper→模型指定backend逐层核对投影、参数路径与cache身份，避免模型类存在却绕过Ascend执行入口。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取模型attention.py 324行、ops/mla.py 316行及factory UT；KPool backend857行和缓存层288行复用同SHA全文记录，core551行仅取已列缓存spec/pool判断选段。

未读取的Native get_rope/MLAModules实现、量化与权重加载、完整attention impl、Runner或CANN实现仍需取证。全部源码作数据，未导入注册custom op或运行测试/NPU；整项硬件与模型/版本交集未知，保持draft/空平台。部署入口保留[GLM-5.3-Flash](../models/vllm_ascend_glm53_flash_hybrid.md)的角色/权重条件，不将其他GLM或Kimi适配直接覆盖当前模型。

## 模型投影先由实际配置决定

Glm5NextMLAAttention要求num_heads能被TP size整除，num_local_heads=num_heads//TP。input_size若指定只改变投影输入维，否则用hidden_size。

| 配置/模块 | 当前模型连接方式 |
|---|---|
| q_lora_rank存在 | DeepSeekV2FusedQkvAProjLinear输出q低秩与kv+rope部分；q_a RMSNorm后q_b ColumnParallel |
| q_lora_rank不存在 | Replicated KV a projection与独立q_proj |
| kv投影 | kv_a RMSNorm；kv_b ColumnParallel的quant_config=None，来源注释限定其在FP8 checkpoint仍为BF16 |
| 输出投影 | RowParallelLinear，保留传入quant_config |
| 主attention缩放 | 初始(qk_nope_head_dim+qk_rope_head_dim)^-0.5 |

表中记录连接与配置，不表示FP8权重、scale、checkpoint mapping或fused kernel已正确加载。是否存在q-lora和模型维度必须来自真实config，不能用源码注释中的示例数字代替配置。

## NoPE与RoPE路径分开验证

skip_rope=True时主rotary_emb=None，避免NoPE配置缺rope_parameters时触发主RoPE断言；否则要求rope_parameters，非default类型根据apply_yarn_scaling改为deepseek_yarn或deepseek_llama_scaling。yarn分支再按mscale²修正主attention scaling，且会修改传入配置字典的rope_type。

稀疏is_v32由index_topk非None决定；该分支仍调用get_rope创建indexer_rotary_emb并要求q_lora_rank存在。这里只读调用，未读Native get_rope对零dim/None参数的具体行为，不能由名称断言NoPE已经在完整链运行。当前Glm5NextKPoolIndexerBackend另外要求qk_rope_head_dim==0并拒绝DCP>1/COMPATIBILITY族，最终按[KPool接入](vllm_ascend_glm_next_kpool_cache_contract.md)核对。

## Indexer参数、缓存与延迟backend选择

模型Indexer只在稀疏配置中构造，assert index_topk、index_n_heads、index_head_dim、index_kpool、cache_config与topk buffer均存在。

| 名称 | 参数与持久对象 |
|---|---|
| index_kpool_compress_ape | 直接FP32 Parameter[pool,D] |
| index_kpool_compress_gate | 直接BF16 Parameter[D,hidden]，checkpoint名没有.weight后缀 |
| wq_b | ReplicatedLinear，保留quant_config |
| wk_weights_proj | fused key与head-weight，MergedColumnParallelLinear、disable_tp=True、quant_config=None |
| k_norm | LayerNorm(D,eps=1e-6) |
| k_cache/tail_cache | BF16压缩K不含量化scale；请求私有FP32 K/gate尾环，capacity=pool+lookahead |

源码注释称FP8 wk加载时upcast到BF16以保持fusion；实际loader没有在这里读取，不将注释当作已执行的转换证明。权重shape、dtype和checkpoint名逐项核对，不能按普通Linear给gate追加.weight。

get_ascend_indexer_backend_cls延迟导入并返回Glm5NextKPoolIndexerBackend。模型Indexer.forward直接抛“必须通过IndexerWrapper的Ascend backend”错误，不能为了通过shape检查直接调这个占位forward。

## wrapper保留参数路径与模型factory

IndexerWrapper直接持有原wq_b/wk_weights_proj/k_norm，并注册模型层直接Parameter；backend共享同一组模块对象。它在type(vllm_indexer)上寻找get_ascend_indexer_backend_cls，存在则调用模型factory，否则走普通AscendSFAIndexerBackend。仅在instance上临时添属性不等同于该type级选择契约。

checkpoint路径继续是...indexer.<name>，不用新增impl段；nn.Module按共享对象去重named_parameters。factory UT使用FakeIndexer/FakeKPoolBackend，断言wq_b.weight、wk_weights_proj.weight、k_norm参数、APE和gate名称保留且没有impl.前缀。它只定义CPU/Fake选择与路径检查，未加载真实checkpoint、量化权重或CANN。

wrapper的k_cache/head_dim/enable_sparse_li_c8/num_cache_tensors/topk_output_width/get_topk_lengths及process_weights_after_loading转给backend；forward传hidden、normalized q_c、k_hidden、indexer_metadata、compute_topk与可选gather handle。模型backend须满足这些接口，不能只返回可调用对象就认定完整替换。

## MLA对象树、缓存marker与执行入口

MLAModules收集投影/norm/rotary/indexer/is_sparse/topk buffer，模型调用MultiHeadLatentAttentionWrapper时传skip_topk=False和fuse_qkv_rmsnorm=True。GLM随后在inner cache layer发布model_version=glm5_next与indexes_kv_by_block_stride=True，Runner按spec/view协议识别，不需要靠模型名字猜缓存布局；物理规划见[双页类指南](vllm_ascend_glm_next_pool_planning_contract.md)。

AscendMultiHeadLatentAttention初始化nn.Module并构造AscendMLAAttention，把indexer、投影/norm、rotary、cache与topk协议交给inner impl。skip_topk setter先保存backing值，impl存在时转发；topk_indices_buffer直接通过impl属性访问。不能因为inner impl不是nn.Module而漏掉投机共享索引的运行时状态。

fuse_qkv_rmsnorm在Ascend wrapper中只为签名兼容接受，没有在这里启用CUDA那套融合；allow_short_prefill_indexer_scoring_skip也被丢弃。性能Agent必须确认真实Ascend preprocess路径，不能把传了兼容参数当作优化已开启。

构造时先mark_fused_preprocess_weights，告知量化方法不要重复拥有transpose/NZ转换；process_weights包装对SFA调用impl方法，其他调用原方法，源码理由是SFA会处置kv_b_proj。这里没有读取具体NZ转换或完整权重处理实现，不能由mark函数名承诺所有quant组合正确。

wrapper拒绝重复static_forward_context prefix。其forward分配output并调用torch.ops.vllm.mla_forward；显式传入的positions/kv_cache/attn_metadata不是这个Ascend入口实际消费的上下文来源。mla_forward经eager_break_during_capture，从forward_context.no_compile_layers[layer_name]获取对象，再按inner layer_name取metadata及已绑定kv_cache，交给impl.forward。mla_forward_fake直接返回，注册声明output可变；本卡没有执行导入期注册或图捕获。

## Agent接入验证与回退

先记录真实config、TP与各projection维度/量化策略，核对NoPE/RoPE、factory返回类、原checkpoint参数名、context prefix与cache markers。保存模块对象共享和named_parameters，再核对加载后权重处理顺序；不能只看类名或state_dict条目数量判断接入成功。

随后按真实backend接口验证normalized q_c和key hidden来源、topk长度、compute_topk共享状态与tail推进，覆盖prefix/PP/MTP、eager/FULL及目标设备。Cache正确性沿已有KPool卡验收，底层wrapper替换、量化scale、Native接口与CANN ABI保留各自证据；旧[GLM DSpark适配](vllm_ascend_glm_mla_dspark_adapter.md)和[Kimi DSpark](vllm_ascend_kimi_dspark_adaptation.md)仍限定各自模型。

失败恢复完整已验证模型类、权重和配置，避免绕过占位forward、删NoPE/并行assert或只改版本字符串。当前只有固定源码和测试定义，没有模型加载、NPU数值、吞吐/时延或下游Agent A/B结果。
