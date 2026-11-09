---
type: Guide
title: vLLM Ascend Mamba 状态接入：MambaCopyKVConnector、加载与复制顺序
description: 沿 MambaCopyKVConnector 和 copy_state_after_kv_load 核对同步加载后的 bulk copy、逐层接管、pending 消费与失败清理，对照 ActiveKVConnector 的无计算步、禁用、参数透传及模型状态选择。 补充共用Mamba补丁的Triton/Tensor回退、完整边界/accepted修正和逐层metadata消费。
aliases:
- MambaCopyKVConnector
- copy_state_after_kv_load
- init_asecnd_model_state
- _prepare_layerwise_mamba_copy
- _finish_previous_layerwise_mamba_copy
- ActiveKVConnector
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.kv_cache
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/kv_connector.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/kv_connector.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_mamba_kv_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/mamba_hybrid.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/default.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_mamba_utils.py
  role: implementation
created_at: '2026-11-02T03:15:06Z'
updated_at: '2026-11-03T05:18:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Mamba 状态接入：MambaCopyKVConnector、加载与复制顺序

## 消费任务与固定范围

MRv2混合线性注意力模型接入远端KV加载，或出现源state已更新但running state仍旧、失败后下一步又复制旧状态时，先核对加载、状态索引决策、实际copy与forward的顺序。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：wrapper43行、测试157行、状态工厂84行和Mamba状态496行全文；Runner仅519–555与650–693，default状态仅71–84。独立Native5df63a7203cdb9328d824a27b682e77c7b9928be的KVConnector179行全文，pin复用同SHA。

Main pin指向544f182d9f0c9bfe8bd7645525951d5e3692a542，独立Native父接口用于明确版本差异，不证明二者ABI已配对。源码与测试均作为数据，没有执行导入、pytest、copy kernel、模型或NPU。整项模型和硬件范围未知，保持draft/空平台。

[GDN执行接入](vllm_ascend_gdn_runtime_dispatch_contract.md)管每层state消费者的wait/save，[GDN元数据](vllm_ascend_gdn_metadata_builder_contract.md)管索引与分组，[RecoverSSM诊断](../../runbooks/precision/vllm_ascend_glm_recoverssm_graph_metadata.md)管staging/commit。本卡补Runner层加载与复制时序，不替代这些协议或完整递推算子分析。[KVPP预取](vllm_ascend_kvpp_runtime_contract.md)的整层广播Future也不等于Mamba远端加载或状态复制完成。

## 模型状态选择先于接入假设

init_asecnd_model_state保留源码中的这个拼写。模型具有get_model_state_cls属性时，先调用它并实例化返回的类，优先于平台默认分派；此处只有hasattr，没有额外的callable或返回类校验。不能仅看到is_hybrid就认定实际类必为公共Mamba状态。

没有模型覆盖时，hybrid优先选Mamba状态；STANDARD_WORKER_PATCHES能力不满足则进入_310p专用类，满足则选AscendMambaHybridModelState。非hybrid也先处理该能力门控，再检查CrossAttention并选择encoder-decoder，最后为普通AscendModelState。这是固定工厂顺序，不是所有自定义类、310P或混合模型已通过的支持表。

Runner只有在model_state.copy_state_after_kv_load可调用、存在KV transfer组且connector.requires_mamba_state_copy_after_load为真时，才把本实例self.kv_connector包装为MambaCopyKVConnector。没有全局修改上游KVConnector类或共享NO_OP对象。包装器保存inner引用与回调，不复制inner；inner是否另被共享仍由构造方负责。

## 先决策，再选择三条复制路径

preprocess_state在_align_mode关闭时返回；有PCP manager且model_uses_kpool_indexer命中时，先切换到其global batch/block tables，再检查请求数。请求数0也提前返回，因此这两个早退不构成上一轮deferral完整清理的保证。

有效align批次先检查上一轮layerwise pending，再获得Mamba组和align context，执行preprocess_mamba_align_fused_kernel推进设备侧state索引与src列/offset。这个决策要在attention metadata之前，不能把“推迟copy”改成连索引决策也延后。接着按下面顺序选择：

| 路径 | 条件与实际动作 |
| --- | --- |
| layerwise接管 | _prepare_layerwise_mamba_copy找到可调用prepare_mamba_state_copy且返回真；保存ctx、请求数、idx_mapping及待copy层集合，跳过bulk。 |
| 加载后bulk | 未被逐层接管，存在transfer组且requires_mamba_state_copy_after_load为真；保存_pending_bulk_copy，等wrapper回调消费。已有pending则报Previous Mamba bulk copy was not consumed。 |
| 立即bulk | 前两项未命中，直接ctx.run_fused_precopy。 |

context和copy函数来自Native相关接口，实际patched kernel、父类生命周期及各Mamba类型布局没有由本卡闭合。get_mamba_state_copy_func与get_mamba_state_copy_funcs在所读代码中有不同调用位置，不按名字近似互换。PCP global化也不是任意hybrid+PCP组合通过的证据。

## Wrapper保证调用顺序，加载完成还依赖inner合同

MambaCopyKVConnector.pre_forward先把scheduler_output、args和kwargs原样传给inner.pre_forward；正常返回后才调用copy回调。inner加载抛错时不会copy，也没有捕获并吞掉该异常。它没有另加设备event、stream等待或跨rankbarrier；远端state是否在inner返回时已经可读，要核实际connector的同步/逐层协议。

copy_state_after_kv_load无pending时直接返回；有pending则先将_pending_bulk_copy清空，再调用run_fused_precopy。因此正常重复hook只消费一次，但copy自身失败后没有自动保留或重试pending的事务保证。不能捕获异常后直接重用同一回调，假定它还会完成原复制。

Main Mamba.finish_execution在failed=True时清_pending_bulk_copy，然后委托super；成功路径不自动消费未执行pending。所读AscendModelState.finish_execution在device_metadata存在时调用finish。Runner的已读选段用try/finally向finish_execution传forward_failed，父execute成功返回后才设False；这些是局部清理调用证据，不代表所有state、传输和线程都被回滚。

## 逐层pending与下一有效步骤的检查

_get_layer_state_ranges按Mamba缓存组及组内层顺序，将每层映射到展平state-type数组[start,end)，结果会缓存。prepare接管后，connector应在对应层加载完成后调用do_mamba_copy_for_layer。

do_mamba_copy_for_layer对没有pending或已消费的层直接返回；找不到range也返回且不移除该pending层。有效层把context中的state地址、stride、元素大小和group索引等数组切到本层，调用mamba_utils模块属性上的precopy kernel，再discard层名。这里没有独立设备完成同步，不能把discard当DMA或kernel数值已验证。

_finish_previous_layerwise_mamba_copy在下一有效align preprocess中，先取出并清空当前deferral；存在未消费层则按排序层名抛RuntimeError，不会继续调用finish_mamba_state_copy。全部消费后才按可调用性通知connector finish。异步sample路径可能落后一步，所以检查放在下一次preprocess；异常前保存pending层列表，不能据字段已清空就丢掉故障证据。

## 独立Native的KVConnector生命周期

独立5df版本的get_kv_connector无transfer组时返回共享NO_OP_KV_CONNECTOR，否则构造ActiveKVConnector、注册KV caches与host transfer buffer ops。以下是该Native文件本身的合同，不能默认为Main配对版本完全相同：

| 入口 | 已读行为与边界 |
| --- | --- |
| pre_forward | disabled时返回；否则检查metadata、处理preemption、bind并保存load kwargs。有has_sync_kv_loads才在此启动load，其他load推迟post_forward。 |
| _start_load_kv | 先清_pending_load_kwargs，再在已有或临时forward context内调用外部start_load_kv；外部异常没有自动重试pending。 |
| post_forward | disabled返回None；否则启动待发load、wait_for_save，收发送/接收/错误块、统计、事件和worker meta，再clear metadata；不是覆盖所有异常的finally。 |
| no_forward | Active内部调用自己的pre/finish/post并返回只有connector输出的ModelRunnerOutput。wrapper直接委托此入口，不增加Mamba copy或模型执行。 |
| set_disabled/reset_capture_state | wrapper均透传。该Native set_disabled还改变kv_transfer_state的全局agent引用；reset不受本类disabled早退保护。 |

wrapper本身没有保存disabled标记，pre_forward仍会在inner正常返回后调用copy回调。不能由set_disabled透传推出wrapper在任意pending状态下都不copy；要结合实际profiling/no-op接线与pending生命周期检查。

独立Native的post_forward签名只有finished_req_ids。wrapper虽接受并透传args/kwargs，却不注入旧参数，也不做版本翻译；给inner传wait_for_save=False可能被真实签名拒绝。UT中的宽松Mock接受该kwarg只证明透传设计，不能证明该Native生产接口接受它。

## 测试设计与Agent验收

157行UT用CPU状态字典、mock决策kernel和connector，定义同步load将source从7改42后running读取42，非同步fixture读取原7；顺序为decision→pre_forward→copy，重复hook不再copy。另覆盖load异常不copy、input_batch/metadata透传、post不注入移除参数、各生命周期入口、两实例回调独立，以及failed清pending仍结束metadata。这些是未执行的测试定义，不证明真实远端传输或FULL图回放。

Agent保存实际model_state/connector类与版本、requires标记、sync-load标记、请求/idx_mapping、源目标state列、pending bulk/layers、加载完成证据及copy前后值。先验证首步、连续步、块边界、逐层接管、重复hook、no_forward、load/copy异常与下一步清理，再核eager/允许的图、PCP和目标模型递推数值。先恢复匹配状态与完整协议，再测加载等待、copy和forward各段成本；本卡没有NPU、精度、性能或Agent A/B结果。


## MRv1共用Mamba补丁：整批与逐层copy不能混淆

新增同提交 patch/worker/patch_mamba_utils.py512原始行的全部AST程序投影；这里补的是Native mamba_utils模块属性替换，非前文MRv2 wrapper本身。_TEMPORAL_TILES=1，TRITON_BATCH_MEMCPY能力决定pointer kernel或Tensor-copy fallback，不能因模块能import就宣称310P有同样Triton路径。

有Triton时src/dst/size metadata按实际copy数H2D，batch grid为copy数、BLOCK_SIZE=8192；没有能力时裸指针batch_memcpy明确拒绝，collect保存有Tensor所有权的pair，复制采用src.clone后写dst。指针转Tensor helper检查非负/元素对齐并界定底层storage范围，仍不自动约束为原逻辑state view范围，调用方copy_spec必须正确。

preprocess清finished/preempted/resumed的旧state index；本步0 token也清该请求index。当前state列由computed+scheduled及num_speculative_blocks决定，跨列时按accepted-1收集copy并将Host accepted重置1，避免后续重复平移。CPU fallback postprocess先将真实accepted同步回Host，再判断是否越完整cache边界、选dest列与accept偏移，不能在异步计数尚未就绪时直接用乐观值。

逐层路径先按layer保存src/dst/bytes，再重新pack成连续slice、一次stage metadata；每层load后只消费该层slice，finish若仍有层未copy就抛带层名错误。_layer_copy_staged防重复stage，但reset/finish才清状态；层名、layout和copy_funcs必须与真实KV group逐层一致。UniformTypeKVCacheSpecs按layer取Mamba spec，再选mamba_type的state-copy函数，不用某组首层的规则覆盖全部层。

MambaCopyBuffers.create将uint64请求替成int64存指针metadata，dtype变化不是更改地址所有权或证明地址范围安全；外部kernel按真实位宽解释。bulk与layerwise回调、Tensor fallback pair及加载后copy的接管条件必须成套验证，不以一个metadata offset归零认定所有设备copy已完成。本次未运行任一路径。
