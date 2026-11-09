---
type: Guide
title: vLLM Ascend RFork 权重接线：预布局、共享草稿与默认加载回退
description: 沿 RForkModelLoader 的 processed_layout、shared_target、post-load hooks 与
  fallback 接入新模型，说明量化/NZ选择、EPLB旁路、全局注册恢复及原生loader接口边界。 明确 RForkModelLoader.download_model/load_weights
  的 NotImplementedError 接口边界。 说明构造失败回退时static_forward_context的快照、原dict身份恢复与既有模型基线保护。
tags:
- task.implementation
- task.debugging
- topic.checkpointing
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/rfork_loader.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/setup.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/safety.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/session.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/types.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/transfer_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/shared_experts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/routed_experts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/fused_moe.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/model_loader/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/model_loader/base_loader.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/model_loader/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_restored_lifecycle.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/rfork.md
  role: supporting
created_at: '2026-10-29T20:37:39Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-04T03:05:17Z'
aliases:
- RForkModelLoader.download_model NotImplementedError
- RForkModelLoader.load_weights NotImplementedError
- _snapshot_process_global_model_state
- _reset_process_global_model_state
- _RForkProcessGlobalModelState.static_forward_context
---

# vLLM Ascend RFork 权重接线：预布局、共享草稿与默认加载回退

使用7d9e时，CPU-offload Engram另有本地权重ready与owner检查，见[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的RFork节；不能仅用旧版“非NPU tensor”边界判断新实现，也不能把主机表传输注册等同加载完成。


## 任务与固定范围

新模型在RFork注册前后tensor集合变动、重复transpose/NZ、shared expert校验失败、草稿重复注册target内存，或fallback时二次分配OOM。固定Ascend ceac与原生vLLM v0.32.0，整项平台未核验，保持draft/空平台。这里只蒸馏Host加载/调用合同，未执行模型、CPU/NPU测试、生成器或服务，不宣称全部量化scheme闭合。

## 注册、模型构造与session身份

setup.py通过vllm.general_plugins登记ascend_model_loader，入口先global patch、register_netloader，再register_rforkloader导入带@register_model_loader("rfork")的类。原生decorator要求BaseModelLoader子类，同名注册会警告并覆盖；确认实际loader类，不能只看命令行load-format。RForkModelLoader重写load_model，download_model和独立load_weights仍抛NotImplementedError，不是任意inplace reload接口。

原生initialize_model优先新式(vllm_config,prefix)构造并进入当前配置上下文，记录reload metadata；旧式签名有推断兼容警告。RFork沿该接口初始化，不等于已执行BaseModelLoader的完整标准load_model流程，特别不能默认继承在线layerwise finalize、全部内存日志或加载后的所有保护。

_get_rfork_session_attr按runner_type=draft、MTP model_type/architecture等识别main/draft，把rfork_session或rfork_draft_session存于进程寿命LoadConfig。_ensure_rfork_session对已有对象直接复用，没有每次重新验证全部identity；不得在复用同LoadConfig后任意改变模型/strategy而假设会自动换key。新session记录全局/TP/PP/EP、条件DP shard及配置指纹。

## 先判断旁路与payload阶段

mutable_weights_bypass_reason遇任一sleep mode或非None weight_transfer_config旁路；另外expert_map_path非None、原生enable_eplb、Ascend dynamic_eplb或expert_map_record_path也会选default loader。旁路发生在本次ensure session之前，不代表它会替既有session完成清理。不能把某个fused-MC2开关等同于全部旁路条件。

_requires_processed_layout_transfer在model_config.quantization非None、非bool且可转int的weight_nz_mode==2，或hardware policy为FORCE_NZ时为真。固定policy不证明某硬件所有模型都适合RFork；其余路线为checkpoint模式。它们的hook顺序如下。

| 路线 | 注册/read前 | read后 |
| --- | --- | --- |
| processed_layout | initialize_model后先process_weights_after_loading，再NPU synchronize，再注册最终候选布局 | 不重跑整套转换，仅刷新FlatQuant host scalar等规定状态 |
| checkpoint | 构造后直接注册，取得seed并read | 运行post-load，但暂时抑制AscendUnquantizedFusedMoEMethod的转换 |
| shared_target | draft所有live待传项均由target已注册区域覆盖且无独立非NPU状态时提前复用 | eval后返回，不重复read或运行可能改写共享storage的hooks |

## post-load不是纯metadata整理

原生process_weights_after_loading先处理word embedding tying，遍历QuantizeMethodBase；必要时device_loading_context临时搬运参数，再调用各层quant finalize，更新参数TP状态并处理内存压力。随后是deferred attention、model-level hook与torchao reload状态。RFork预布局会真正调用这些过程，不能由processed_layout名字推导为纯shape检查或对未填值tensor总安全。

_rfork_pre_transfer_weight_processing只对AscendMoERunner拥有的quant method去重，若process_weights_after_loading有__wrapped__，临时替换为该原函数。已读AscendSharedExperts在multistream_overlap开启时用wraps包装原hook，随后以随机NPU输入验证split/integrated输出；预布局绕开的是这层验证。它不证明新模型传输后已经重新通过同一校验。正常进入上下文后的finally恢复记录的方法，方法替换也不应被当作跨线程加载隔离。

checkpoint read后，_rfork_skip_unquantized_moe_post_load_processing仅将该未量化MoE method临时替成noop；其他dense、attention、model hooks仍执行。已读未量化转换会pad、transpose、contiguous、replace_parameter及按能力转NZ/专家列表，重复调用可能改变已传storage；不要把局部skip推广为跳过所有post-load。

processed read后_refresh_rfork_flatquant_state对带aclnn_clip_ratio的模块要求clip_ratio为单元素Tensor，调用item刷新host值；不重跑布局转换。新scheme的额外host cache/derived对象需沿实际消费者适配，不能据命名tensor已经到位就省略运行态初始化。

draft共享排除区域来自target backend在锁下返回的注册块快照；快照本身不延长target storage寿命。全共享早返与部分共享manifest skip都需保持target owner存活，不能只复制地址列表。相关身份/名单合同见[manifest接入](vllm_ascend_rfork_manifest_contract.md)。

## 成功加载、发布seed与回退分别判定

register_destination、acquire_seed、transfer_from_seed及后处理成功后eval，才尝试发布seed。_start_rfork_seed_service失败或DEFERRED可继续返回可推理模型；source=transfer/local/fallback/shared_target和loader elapsed不证明已经被planner发现，elapsed也不含后续deferred promotion完成时间。

没有兼容seed的专用异常记source=local；ImportError/OSError/RuntimeError/ValueError进入fallback，其他编程/退出异常不被同一异常集合兜底。代码未执行通用输出精度比较，所以“数值不对会自动fallback”不是实现保证。

fallback最多2轮prepare_for_fallback，轮间0.5秒；必须service_stopped和memory_reset均真才可继续分配。lease_released可仍为False而允许后续延迟发布。清理不满足时保留owner并拒绝第二模型，FINALIZED不可恢复；不是无条件强制释放内存后再试。

已开始构造的失败尝试会恢复snapshot中的static_forward_context、static_all_moe_layers、Ascend EPLB registry/counter与RoPE缓存，并移除新discarded模型的Dynamo hooks，保留已有模型基线。它是特定已读全局集合的恢复，不包含所有自定义模型可能修改的任意全局变量。

安全清理后释放局部model引用，做4轮gc.collect/torch.npu.empty_cache，再以浅copy LoadConfig的load_format=auto、extra_config={}调用原生get_model。原VllmConfig未被整体重写；default loader与外部资源依赖仍存在，4轮回收不是显存归零保证。default加载失败会传播；已有session可尝试将fallback模型发布或延迟发布，见[清理排障](../../runbooks/runtime/vllm_ascend_rfork_retained_memory_cleanup.md)。

## 验收与剩余工作

记录真实loader/session、旁路原因、layout模式、预/后hook名单、target共享owner、before/after结构digest、fallback原因和清理结果，分别比较全冷、seed命中、shared_target与失败路线的ready时间及输出。已读mock定义验证特定全局恢复与租约控制，不证明所有模型构造副作用、CANN/NPU格式、内存与精度；量化hook/外部引擎/全部模型仍需按目标继续验证。
