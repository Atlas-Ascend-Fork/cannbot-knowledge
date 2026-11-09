---
type: Guide
title: vLLM Ascend 310P运行时覆盖：CPU状态、KV清零与目标图回放
description: 聚合310P request staged writes、Host batch镜像、KV直接清零/共享槽、MRv2目标图phase、MRv1草稿尾元素与RoPE保护、采样替代和分片导出约束；区分真实覆盖与继承边界，定位状态陈旧和图输入错位。
aliases:
- Ascend310PStagedWriteTensor
- Ascend310PRequestState
- AscendKVBlockZeroer310V2
- get_310p_shared_cache_slots
- ModelAclGraphManager310
- AscendSpecDecodeBaseProposer310
- ShardedStateLoader310.save_model
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.graph_execution
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/kv_block_zeroer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/kv_cache_sharing.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/sample/sampler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/sharded_state_loader_310p.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/spec_decode/llm_base_proposer_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/aclgraph.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/input_batch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/kv_block_zeroer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/states.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/_310p/fused_moe/fused_moe.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/_310p/fused_moe/shared_experts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/_310p/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/_310p/worker/v2/model_state.py
  role: implementation
created_at: '2026-11-03T06:06:23Z'
updated_at: '2026-11-03T06:39:58Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 310P运行时覆盖：CPU状态、KV清零与目标图回放

## 版本、对象和任务分界

固定Main ceac1a2，完整阅读本卡9份实际实现及3份包导出/说明文件。仅按源码提取310P替代实现，不证明所有模型实际选中这些类，也没有执行上游、NPU、图、采样或checkpoint导出。Native父类、UVA对象、模型Runner接线和外部API仍需按配对版本核对，保持draft/空平台。

这里的ModelAclGraphManager310是目标模型图管理器，旧_310p/spec_decode中的AscendSpecDecodeBaseProposer310是MRv1草稿覆盖；二者均不同于[MRv2 MTP proposer与逐步草稿图](vllm_ascend_310p_mtp_proposer_contract.md)。普通原语替代及MRoPE切片见[310P原语合同](vllm_ascend_310p_primitive_fallback_contract.md)，采样结果与拒绝提交见[310P采样合同](vllm_ascend_310p_sampling_contract.md)。不要只按目录或MTP名字混合三套生命周期。

## CPU拥有的staged write不是逐dirty-row GPU散射

Ascend310PStagedWriteTensor在UVA模式持有UvaBuffer的cpu/np，并把gpu设为uva()返回视图；普通模式创建CPU和device zeros。stage_write把values转list，非空才改NumPy切片并标记index；stage_write_elem标记对应index。max_concurrency被丢弃，类没有并发提交或范围保护协议。

apply_write有dirty时：UVA只刷新gpu=uva()并清dirty，不提交显式H2D；普通模式把整个cpu tensor一次copy_到gpu、non_blocking=True，再清dirty，并非只复制dirty indices。这里没有内部stream事件、pin-memory分配或提交后Host禁止改写机制；真实异步性和消费者可见性必须由调用者保证。清dirty表示提交已安排，不表示device已经完成；直接改cpu/np却不stage也不会自动触发普通模式提交。

Ascend310PRequestState自行建立容量、请求双向表和free indices，不调用父__init__；all_token_ids走UVA，total_len和num_computed_tokens走普通staged tensor，prompt/prefill长度用UvaBackedTensor。它还保存独立CPU/NumPy的computed长度、last sampled以及device draft/next-prefill缓冲。不能把同名字段的存在当成CPU与device镜像自动一致。

add_request先委托父逻辑，再写num_computed_tokens_cpu；只有computed>0时才从all_token_ids[computed-1]初始化last_sampled_tokens_cpu。computed=0不会在这个覆盖中清掉旧slot留下的CPU last token，slot复用与其他重置路径必须一起核对。父add/remove/reorder全部语义未在本卡闭合。

Ascend310PInputBatch只新增block_tables_np、input_ids_cpu、logits_indices_np三个可为None字段，不计算内容、容量、顺序或新鲜度。按同batch大小复用引用仍可能是旧请求数据；真实发布点和采样消费者必须属于同一调度轮。

## 无Triton KV清零与共享槽是两项独立规则

AscendKVBlockZeroer310仅登记FullAttentionSpec，跳过runner_only层；从static_forward_context读恰为两个K/V张量，按data_ptr去重。逻辑页比率取首个已登记group的spec.block_size//kernel_block_sizes[group][0]，后续group复用同一个比率。没有验证除法整除、比率正值、所有group比率一致或block ID容量，不能将首group合法推广到异构KV组。

zero_block_ids把每个逻辑block映射到[start,end)物理首轴范围，对所有登记K/V逐段zero_。它不是任意format的通用字节页清理，也不处理被跳过的Mamba state；负/越界切片语义需caller先验证。空列表或没有登记tensor时直接返回，不证明实际需要的缓存已经清过。

V2适配只将flat block_sizes转成单元素嵌套列表，空/原嵌套列表保留，再委托V1 init；另加enabled布尔守卫。cache_dtype和pin_memory虽在接口/对象中出现，所读直接清零逻辑没有据此另选格式或Host拷贝实现。

get_310p_shared_cache_slots只有layout同时layer_compact/block_compact才尝试；要求所有page_size_bytes相同、恰好一个Attention group、至少一个Mamba spec、Mamba spec互等且各Mamba group层数相等，不能在一个group混Attention/Mamba。返回Mamba层在各自group内的slot映射，不是按所有层全局递增，也不表示Attention与Mamba直接共用一套tensor内容。任一条件不满足返回空dict，不能解释成强制启用共享或自带存储分配。

## 目标图捕获必须与MTP verify的phase一致

ModelAclGraphManager310仅在有speculative_config且graph mode包含FULL时包capture，否则直接父capture。它临时替换全局AscendInputBatch.make_dummy：num_reqs>0且num_tokens//num_reqs>1时改SpecDecoding，其他保持父dummy phase。谓词是整数平均长度，不独立证明任意ragged batch均为uniform MTP；真实capture描述符和运行时query布局仍须匹配。

替换在finally恢复，因此异常不会永久留下该引用；但它没有并发/嵌套隔离，也没有保存class method原始descriptor的完整通用恢复协议。捕获期间其他使用同一类的线程可能观察到临时函数。

_updatable_graph_replay先resolve_tasks；非空才让update_stream等待当前compute stream，再跳过直接ModelAclGraphManager覆盖、沿其父run_fullgraph回放，非空才graph.update。任务为空时不做这项握手，并非无条件device全同步。源码说明310P无FIA/PA graph_task的SpecDecoding FULL依靠compute stream上先刷新稳定buffer、再replay的顺序；本函数不负责刷新全部buffer，不能删掉上游拷贝或在其他stream照搬。

任务非空分支的底层ExternalEvent/资源寿命仍按[UpdatableGraph任务合同](vllm_ascend_updatable_graph_task_contract.md)核对。注释里的小模型开销动机没有本卡可引用的测量，本次也未验证实际310P FULL数值或性能。

## MRv1草稿尾保护与采样替代

AscendSpecDecodeBaseProposer310在_run_merged_draft前将普通RoPE class flag设True，finally设False，调用的是模块导入时捕获的父方法引用。后续替换父方法不自动更新_original_run_merged_draft；finally也不恢复进入前的True，不能当作任意嵌套安全上下文。

无extra input slots时，set_inputs_first_pass先clone持久input_ids最后元素，执行左移赋值，再恢复尾元素，最后在每请求采样位置写next tokens。缺采样位置时用query_start_loc[1:]-1；同时设positions与hidden前缀。这里跳过DCP处理并返回(None,None)附加参数，不能推广为任意context parallel已适配。num_tokens=0未在该覆盖中完整成功短路，会涉及尾部-1索引；输入和容量域需caller保证。

需要extra slots时委托父set_inputs_first_pass，而非执行该尾保护，相关算子协议见[EAGLE输入展开](vllm_ascend_eagle_input_expansion_contract.md)。不要由MRv1的保护存在推断MRv2相同切片也已自动保护。

AscendTopKTopPSampler310在VLLM_BATCH_INVARIANT为真时直接委托父forward_native；其余先apply_top_k_top_p，再按logprobs_mode保存processed logits或FP32 log_softmax，另以FP32 softmax交_random_sample_310p。其他mode此层返回None，但父Sampler仍可能处理别的输出。新模型不能把此覆盖读成所有采样/约束/拒绝链都被替换，或由相同概率推断与另一RNG实现逐token同seed一致。

## checkpoint导出不能只看函数签名

ShardedStateLoader310.save_model先用父_filter_subtensors处理state_dict，只按当前TP rank、TP_ONLY_PATTERN和part0保存一次safetensors。传入pattern与max_size在本实现中没有消费，没有按max_size拆part，也没有使用PP rank或建目录的逻辑；所需目录、覆盖策略和TP/PP文件唯一性必须由调用者保证。

generate_quant_description把全局model_quant_type取自quant_config.quant_description，缺配置或AttributeError回FLOAT，写version1.0.0；仅名称以.weight/.bias结尾且tensor为INT8/INT32/INT64时标全局量化类型，其余都标FLOAT。它不是从每层真实scheme、scale、packing或混合精度推断的精确schema；不能单凭parameters_type_map.json证明checkpoint可重新加载或数值还原。

适配验收优先检查slot复用和镜像发布、页比率/共享槽、FULL phase与稳定地址、MRv1/2区分，以及导出后实际重载。这里仅蒸馏固定实现的可执行合同；没有导出/重载、采样、通信、图或硬件运行结果。


## 3164 版本补充：共享专家重叠与 encoder-only state

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`；完整变化与必要上下文静态读取，不标目标全文FULL，未执行upstream/JIT/NPU/图/通信/性能测试。

310P不再在MoERunner里统一关闭shared-expert多流，而对同一个executor实例绑定310P selector/submit/finish方法，保留原权重validation hook。MLP path强制LINEAR_WRAPPER，因为310P scheme持有输入scale/offset、量化补偿和NZ布局，标准A8 fused路径会绕过这些合同。

只有multistream开启、无LoRA且TENSOR_PARALLEL模式时，gate/up在等router-ready的同一共享流上提前提交activation、prepared down输入和可选expert sigmoid gate；产生的是每forward新SubmittedSharedExpertWork310，不跨step缓存。finish仍等routed_combine_start再做down和output gate，公共final join保留。它不是无条件重叠所有设备/量化/并行组合。

MRv2在load_model之后、profile/capture之前主动创建shared stream，计入资源预算；FULL+TP>1+shared overlap时，dummy sampler后额外预热batch1及较小capture尺寸的compute_logits，避免最大batch采样profile未建立小消息HCCL通道、捕获后耗尽310P event。源码动机不等于本次延迟或资源实测。

新增Ascend310PEncoderOnlyModelState组合310P mixin与共享Ascend encoder-only metadata构造，服务无KV group的BERT/BGE非因果层，仍替换310P RoPE/sampler并维护捕获seq_lens地址。零KV group不是缺少attention metadata的理由。模型选择和实际encoder ABI按同版本Runner验证。
