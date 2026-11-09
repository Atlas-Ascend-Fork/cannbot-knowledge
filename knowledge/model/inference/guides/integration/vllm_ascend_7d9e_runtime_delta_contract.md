---
type: Guide
title: vLLM Ascend 7d9e运行时迁移：采样、缓存与图接入
description: 固定7d9e核对310P采样、AscendStore/RFork寿命、GLM PCP与KPool、CANN TopK、V4.1首SWA回放、MLA补头、QSA版本门禁及PLE512分块，按条件和数据归属迁移。
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.speculative_decoding
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/_310p/worker/v2/sampler.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/_310p/worker/v2/sample/dispatch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/_310p/worker/v2/sample/bad_words.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/_310p/worker/v2/sample/penalties.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/_310p/worker/v2/sample/logit_bias.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/_310p/worker/v2/sample/logprob.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/_310p/worker/v2/sample/min_p.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/_310p/worker/v2/sample/temperature.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/_310p/worker/v2/sample_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/in_flight_save_blocks.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/layerwise/pool_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/ascend_store_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/model_loader/rfork/local_weights.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/model_loader/rfork/rfork_loader.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/model_loader/rfork/tensor_layout.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/glm5next/recoverssm_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/glm5next/recoverssm_metadata.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/glm5next/kda.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/worker/v2/model_states/mamba_hybrid.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/ops/fused_moe/router/fused_topk_router.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/device/device_op.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/csrc/torch_binding.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/csrc/torch_binding_meta.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/csrc/build_aclnn.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/glm5next/attention.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/ops/triton/glm5_next_cann_keypool.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/.github/vllm-main-verified.commit
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/deepseek_v41/decoder_replay_layers.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/deepseek_v41/decoder_replay_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/deepseek_v41/model.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/attention/dsa_v41.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/attention/mla_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/tests/e2e/pull_request/one_card/test_mla_prolog_head_padding.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/qwen4_exp/cpu_length_sync.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/qwen4_exp/model_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/qwen4_exp/qsa.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/models/qwen4_exp/ple.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/ops/triton_ple.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/vllm_ascend/ops/triton/docs/ple_conv_prefill.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: supporting
created_at: '2026-11-04T02:54:54Z'
updated_at: '2026-11-04T03:07:25Z'
platforms: []
aliases:
- InFlightSaveBlockTracker
- register_sampling_kernel_overrides
- RFork Engram local_weights
- GLM RecoverSSM PCP producer
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# 固定版本的运行时迁移任务

本卡只说明固定 Main `7d9e52da97606050f61f33275b9d9a0def86881a` 的十组接入差异。原有卡主要固定 `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，此前增量固定 `3164adc8fe75892fbf7f99f524bb72fddf1e6efd`；中间观察版本 `5f5e25dd94db85b59251be7d3baf7c808475b6d7` 只用于辨别引入后又回退的改动。本卡不把这三条历史版本自动替换为最新版本。7d9e 的 `.github/vllm-main-verified.commit` 指向 Native `24420b7a341af37a9bc3186e6fc6062512e0aa58`，它与旧卡的配对 pin 不同；本次没有取得并闭合该 Native 实现。

选择目标时先记录 Ascend/Native/CANN/torch_npu、实际 Runner、模型类、connector mode、checkpoint 和投机配置，再读对应主题。下述仅静态阅读固定源码与完整相关差异，没有导入上游、运行 UT、编译、NPU、分布式服务、图回放或性能实验。十主题没有足够统一产品证据，保持 draft、空平台且不增加 verified。

| 当前问题 | 下文入口 | 先避免的误判 |
| --- | --- | --- |
| 310P参数被拒绝、logprobs不一致 | 310P MRv2 | 旧拒绝表套新版本；把过滤后分布当raw logprobs |
| Pool保存后块提前释放、reset失败 | AscendStore | bulk与逐层混用；把完成计数当按rank去重或持久化成功 |
| RFork主机权重未加载、fallback内存残留 | RFork | 路径相同当ready；draft释放target的表 |
| GLM启PCP或选择KV dtype | RecoverSSM、GLM KPool | 把producer准入扩到consumer；继续使用已回退的INT8配方 |
| MoE路由或MLA补头结果改变 | MoE普通TopK、MLA | 用旧自有kernel解释新SDK；逻辑view当成已物化NZ存储 |
| V4.1回放漏KV、首SWA读错区间 | DeepSeek V4.1 | 先compact后写完整cut层KV；encoder/decoder边界混用 |
| Qwen CPU同步或PLE资源回退 | Qwen4Exp、PLE | 按相似类名替换父类；较小tile直接当成性能收益 |

## 310P MRv2：后处理已扩展，旧拒绝表只属于旧版本

[310P采样合同](vllm_ascend_310p_sampling_contract.md)中的旧 min_p、penalty、logprobs 与 processors 拒绝表不能用于判断7d9e。新 `Ascend310PSampler` 保存 min_p、repetition/frequency/presence penalty、allowed IDs、bias、分词后的 bad words 和每请求 logprobs 数；请求槽复用会重置对应字典与开关，bias staging 被 invalidate，数值数组经 dirty 标志在 `apply_staged_writes` 批量 H2D。`add_request` 仍先拒绝存在原始 bad_words 却无 token IDs 的请求，再处理槽范围；越界槽静默返回不代表请求已登记。

`_apply_postprocess` 的顺序为 allowed IDs → logit bias → bad words → penalties → temperature → min_p → top-k/top-p。温度0或1跳过除法；min_p先对当前 logits 做 FP32 softmax，以本行最大概率乘 min_p 作为门槛，严格小于门槛才置负无穷。不能先 top-p 再 min_p，也不能把这里的后处理 logits 当原模型分布。Sampler为加工创建 FP32副本；无随机且无加工时走原 logits 的 argmax，其他 greedy 请求走加工后 argmax，mixed batch按每行 temperature>=1e-5决定随机结果。

penalty与bad words需要绑定 `req_states`，缺失分别抛 RuntimeError。二者从 CPU请求历史构造当前行历史，并依据 `expanded_local_pos` 把本次验证行之前的输入补入；因此请求槽、expanded行和本地步号必须对应同一步。penalty padding采用 vocab_size 哨兵。它们调用 Native 的通用 penalty/bad-word实现，本卡没有闭合其全部算法；`.cpu()`、`.item()`和 Python循环也不构成无Host同步合同。

输出 logprobs 在任何mask、温度或采样加工之前，按原 logits 的 FP32 log_softmax生成。`gather_logprobs` 返回采中token列加可选top-k列，rank统计严格大于采中logprob的token数；同一token可在采中列与top-k列重复。batch以请求的最大非负logprobs数建立结果；prompt_logprobs没有在这段实现中产生，不由“请求不再被旧表拒绝”推导已实现。

新 `register_sampling_kernel_overrides` 缓存注册 Native temperature/min_p/bias 三个 kernel launch ABI；bias替身忽略传入stride/块参数而用实际二维Tensor索引，按whitelist→bias→min_tokens顺序写。注册时还限定修改dispatcher模块的vars读取，规避lazy owner伪造非mapping `__dict__`，无Triton路径补Host next_power_of_2。不能把这些局部替身当全部Native采样kernel已替换；LogitBiasState310传入的stop/min_tokens状态为中性零值，本轮不据此承诺min_tokens约束。

显式seed的请求持有CPU Generator，按expanded行映射同一请求源；新的 `_prepare_cpu_generators_310p` 直接复用CPU源当前状态，仅为非CPU源缓存CPU镜像，避免因临时离batch重建CPU源。常规采样仍调用310P逆CDF helper，不能以源码变化宣布同seed完整序列已通过。验收先覆盖后处理组合、槽复用、多行同请求、mixed greedy/random与随机/MTP切换，再分别比较raw logprobs和最终抽样分布。

## AscendStore：bulk保存引用归专用tracker，逐层走自己的完成路径

[KV Pool传输状态](vllm_ascend_kv_pool_transfer_state_contract.md)与[后端选择](../deployment/vllm_ascend_kv_pool_backends.md)保留各自旧版本；7d9e factory按 `use_layerwise` 明确选择 `LayerwiseKVPoolScheduler` 或 `KVPoolScheduler`。公共 `BaseKVPoolScheduler` 的retain为no-op、pending为False，只清理已完成异步load请求。不能把公共基类存在视为它替所有模式保存了bulk引用。

非逐层 `KVPoolScheduler` 在hybrid保存时使用 `InFlightSaveBlockTracker(world_size)`。只有存在speculative分组元数据且 `req_meta.can_save` 才retain；每组剔除末尾spec scratch，再过滤block ID<=0，touch其余块并给request metadata分配递增event ID。scratch必须保留独占引用以便重定位，不能为“防提前释放”把它也pin住。tracker没有按block ID去重，引用数量须与传入列表和释放次数一致。

worker回传 `completed_events[event_id]=count` 后累计计数；小于expected_worker_count保持引用，达到或超过才删除event并逆序free，令共享prefix最后进入驱逐队列。未知event只warning跳过。它按计数而非rank集合计完成，没有在此证明重复通知去重、丢失通知超时或SDK写入成功；还须沿worker完成协议验证。`has_pending_push_work`读events，reset同时检查events和blocks，仍有追踪内容就返回False。

Base reset对残留load ID还检查block pool是否仅剩null块；仍有引用则拒绝，否则清旧ID再发reset RPC，异常或NACK不算成功。Connector对Mooncake layerwise另拒绝reset_cache。逐层scheduler不继承bulk tracker：它按block_key或gva分流，禁不支持的数据面，block_key不支持P/D TP mismatch，强制load_async=False。逐层release、commit和失败撤销继续按既有传输owner核对，本卡未重读全部worker/SDK。

迁移时先记录factory最终类、hybrid/spec组、can_save、event ID与实际world_size，按retain→完成计数→逆序free→reset建立观察；不要跨bulk/逐层复制pin或reset逻辑。计数归零、RPC返回与持久化可读分别验收。

## RFork：只有本地加载完成且地址未变的Engram主机权重可豁免

[RFork处理后权重](vllm_ascend_rfork_processed_weight_loading.md)、[Manifest合同](vllm_ascend_rfork_manifest_contract.md)与[清理排查](../../runbooks/runtime/vllm_ascend_rfork_retained_memory_cleanup.md)中的来源版本继续保留。7d9e新增 `local_weights.py`，只处理已经导入的 `AscendParallelEngramEmbedding` 且 `cpu_offload=True` 的table；用sys.modules发现类型，避免对其他模型主动导入NPU依赖。

RFork load_model在model state准备后、shared-weight检查和destination注册之前执行本地host weight loading。table的ready状态记录模型owner弱引用、checkpoint路径/key，以及weight/weight_scale_inv各自弱引用和data_ptr。再次使用须同时满足checkpoint tuple相同、tensor数量相同、对象仍是原对象、device仍为CPU且data_ptr未变；只检查文件路径或tensor shape不足。load_checkpoint成功返回后才record；部分加载异常不产生整对权重的ready豁免。

`find_non_npu_state_tensors`仍扫描非meta、非空参数和buffer；只有这些经ready核实的tensor ID才免于“非transfer device”拒绝，其余主机状态不能伪装为本地权重。ready检查不是checkpoint内容hash、并发写保护或持久化验证；原对象上原地修改内容不会由data_ptr变化自动发现。

fallback先完成session注册内存清理并确认可重新调度，再release旧模型本地host权重，之后才允许default loader分配第二个模型。若初始化在model对象形成前失败且启用Engram CPU offload，代码要求修复并重启，不能安全地自动重试未知部分分配。release对共享table检查state.owner；draft不是owner时保留target存储，弱引用也避免为了ready账本长期pin替换后的tensor。default loader完整返回后，在可advertise的fallback路径才record readiness并启动seed服务。

接入时区分本地host表加载、NPU transfer、共享draft与fallback四阶段，验证checkpoint变化、tensor替换/设备变化、失败中途与target/draft释放顺序。不能只以传输注册成功宣告CPU Engram数据已准备，也不能在MR清理失败后先分配第二模型。

## GLM RecoverSSM：PCP producer有条件放行，并传回原始PCP上下文

[GLM KDA接入](vllm_ascend_glm_next_kda_dispatch_contract.md)与[RecoverSSM配置](../optimization/vllm_ascend_glm_kda_recoverssm.md)解释旧链路。7d9e `validate_glm_recoverssm` 不再普遍要求PCP=1：仍要求有speculative_config、关闭stochastic rounding、PP=1、DCP=1；APC开时mamba_cache_mode须align，关时须none。存在transfer时只接MooncakeConnectorV2或MooncakePullConnector。PCP>1进一步要求TP=1并且transfer角色为kv_producer；不向consumer、TP>1或其他connector扩大准入。FP16 cache的未验证注释没有变成支持声明。

metadata builder先归一图padding、按align准备物理state index，在临时关闭Native CUDA staging的context中调用父build，finally恢复原graph模式；建立conv metadata后，从原始common_attn_metadata回传pcp_context。这里的“原始”很关键，不能只从经过归一或替换的局部metadata猜上下文存在。

MRv2 Mamba hybrid在真实PCP batch下分别为本地attention组和原请求顺序的global Mamba组建metadata，再合并。KDA遇global batch有prefill时all_gather hidden并按hidden_restore_idx恢复因果顺序，以head分片推进状态；输出按padded_gather_idx回到本rank本地行。映射元素数不等于pcp_size×local_num_tokens时抛RuntimeError；graph-owned output用index_select的out形式写回。只修改配置validator而漏掉上下文或行序恢复，不能视为已接通。

固定版本的feature guide另给明确部署声明：GLM-5.3-Flash在A3/A5的MRv2使用实验RecoverSSM，默认仍是native AscendC KDA；`--use-replayssm`默认关闭，去掉它回到native路径。P/D须匹配权重、speculative窗口、cache dtype、conv layout、RecoverSSM与prefix-caching配置。P/D head-shard数不同时，两端都用SD `[state_len, conv_dim]` 卷积state，文档声明Mooncake将P的head shards汇集到每个接收D的state；该声明不是本次传输实现或真机验收。

| 文档八设备角色例 | Prefill | Decode |
| --- | --- | --- |
| 并行与角色 | TP1/PCP8/DP1/EP8，kv_producer | TP1/PCP1/DP8/EP8，kv_consumer |
| 投机与执行 | use-replayssm、MTP5，target与draft eager | use-replayssm、MTP5，FULL_DECODE_ONLY |

每个D DP rank接收其分配请求的全部八份KDA head shards，DP8不表示单请求的recurrent state或卷积state预算自动除八；应以每请求完整shape、dtype字节、页padding、spec/RecoverSSM持久buffer及并发计容量。`[state_len, conv_dim]` 是轴序合同，不能只检查元素乘积相等就把DS布局当SD。示例P显式enforce-eager且draft也eager；同段又说明KDA有eager dispatch边界，P外围模型不必普遍enforce-eager，其他图配置须单独验证。不能从示例或validator不拒绝便推导全部compiled P配置通过，也不把示例MTP5当所有窗口的支持证明。

验收先覆盖prefix hit、PCP prefill、混batch、padding与后续spec提交，检查global请求轴、head归属和local输出映射。Native父builder、Mooncake实际传输、全部RecoverSSM kernel和图/数值组合仍需独立验证。实验路径浮点差异可能影响生成token，模型质量和性能按真实workload验收；A3/A5只属于该文档对本主题的声明，不扩成整张十主题卡的平台范围。

## MoE普通TopK：从仓内自有kernel切到CANN原生入口

路由选择继续参考[MoE路由合同](vllm_ascend_moe_topk_host_dispatch.md)。3164至7d9e的净差异删除普通 `csrc/moe/moe_gating_top_k` 族及其Torch/Meta注册和构建列表项，DeviceOperator中的同名普通adapter也删除。7d9e普通fused router直接调用 `torch_npu.npu_moe_gating_top_k`，不能再用旧自有Device源码解释这一新调用的内部算法。

router先以is_fused_supported决定是否回退父grouped路线；普通分支按softmax取norm_type0，否则取1，renorm来自renormalize，bias在必要时转router_logits dtype后以参数名bias传入，同时传k/group/scaling/eps。普通分支直接返回SDK的weights和IDs，本地不再由旧DeviceOperator统一把IDs转int32；实际dtype和数值约束需要按安装版本核验。旧A5 wrapper固定renorm0再手动处理softmax归一的动作也不能自动带入新入口。

sqrtsoftplus的hash/vision分支仍有独立 `torch.ops._C_ascend.moe_gating_top_k_hash` 及fallback，不能把普通TopK迁移说成所有MoE路由自定义算子删除。验收按普通/分组/hash/vision分别固定实际call、bias dtype、renorm、expert ID类型及后续消费；CANN原生入口的Device实现、SoC/shape支持和性能并未由这次仓内差异闭合。

## GLM KPool：按最终版本的类型门禁选择，不能保留中间INT8路径

[GLM KPool缓存](vllm_ascend_glm_next_kpool_cache_contract.md)与[Triton写入](vllm_ascend_triton_glm_kpool_execution_contract.md)保留旧版本。中间5f5曾有INT8 completed-pool分支；7d9e已回退该支持。最终模型Indexer仅接受indexer_kv_dtype为auto、bf16或fp8，int8显式ValueError。auto/bf16建立BF16 completed K cache，fp8建立E4M3 cache；FP8遇OffloadingConnector或PreemptOffloadConnector显式NotImplementedError。此约束只针对这里的GLM KPool，不推广至所有模型KV dtype。

最新write_keypool_caches取消pooled_scales输入与INT8校验/写scale路径，QUANTIZED由scale_cache是否存在决定。FP8池化行按FP32最大绝对值/448生成descale，全零行取1，再把值除scale写cache；同一物理slot写scale。tail与completed pool分别校验自己的物理范围，尾环仍由K/gate组成，不能把已完成池的FP8格式搬到FP32请求私有tail，也不能只改cache dtype就恢复被回退的INT8 ABI。

迁移应检查最终model配置、cache dtype、scale缓冲、wrapper签名和CANN selector一组一致，再测零池、跨pool边界、spec拒绝重放及offload禁配。被删除测试、release fragment或中间实现不构成当前支持证据；新的类型门禁也不等于已完成所有FP8精度/图/传输组合验收。

## DeepSeek V4.1：先写完整cut层KV，再按首SWA专属边界回放

[有界回放合同](vllm_ascend_swa_bounded_replay_contract.md)与[3164模型迁移](vllm_ascend_deepseek_3164_migration_contract.md)保留旧边界。7d9e在可安全执行cache-only写入时，把decoder replay起点从cut+1提前到最后KV source层cut。trim条件是模型有layers、PCP=1、不启SP且cut不含Engram；否则仍用cut+1。整体准入仍拒SP/PP/DCP/microbatch、不兼容的图模式、cut之后的Engram、非DSpark drafter、窗口或层类型不匹配的draft以及LoRA，不能只满足trim条件就绕过这些门禁。

rows有效时，`AscendDecoderReplayLayers.__call__` 在切换到compact metadata之前先调用cut层 `write_batch_kv`，为完整输入写共享cache；该layer先做hc_pre和input layernorm，再调用独立 `dsa_v41_write_kv`，后者按当前metadata的actual tokens调用_update_caches，不执行attention或MLP。随后才收紧row buffers与模型states、运行tail并scatter有效结果。cut本身会重建的top-k/candidate输出不再预先按旧行表compact，不能把旧buffer列表原样搬到新起点。

首SWA的读取范围不能直接沿用其他tail层的decoder replay_start。初始化发现first_swa_prefix所属组后，建立第二个专属metadata builder并独立prepare_source_rope；找不到owner或出现重复会assert。普通组metadata完成后，first builder改用 `inputs.encoder_replay_start`，以独立空shared字典构建，执行它产生的Device metadata tasks，再覆盖首SWA的metadata项。它共享本轮rope views，但不把普通builder缓存结果视为同一个边界。

模型另以 `dsv41_decoder_replay_forward` custom op在运行时从ForwardContext解析mutable replay对象，避免Dynamo固定warmup rows。注册重复layer名报ValueError，返回late auxiliary数量不符报RuntimeError；fake结果只声明shape，不能充当数值执行证据。接入时同时核对完整cut层cache、encoder/decoder两个边界、首SWA任务顺序、compact行、辅助输出与eager/compiled一致性。本节没有闭合_update_caches全部算法、PCP manager或真实图捕获，不能把cache-only写入设计推成端到端节省。

## MLA：Eagle head身份与NZ补头材料化分别处理

[Attention并行迁移](vllm_ascend_3164_attention_parallel_migration.md)与[MLA执行](vllm_ascend_flashmla_dcp_execution_contract.md)保留旧路径。7d9e的draft判定除了runner_type为draft，还接纳 `backends.model_tag == "eagle_head"`；MLAPO仍要求非draft再满足enabling_mlapo，QKV-A融合output gate还会另外关闭MLAPO。不能只检查顶层Runner名称就让Eagle head消费target的MLAPO权重或cache合同。

在 `_build_prolog_v3_weights` 的非量化分支且head_padding>0时，Q_B权重先转置、view为[q_lora_rank,num_heads,qk_head_dim]，沿head轴padding，恢复二维后显式clone，再contiguous并转FRACTAL_NZ。clone在此建立独立二维存储，不能因二维view的逻辑shape正确就假定旧三维base布局能被NZ转换正确解释。W_UK只在仍为原head数量时补相同头轴，传给Prolog的num_heads采用padded数量；不把这一分支扩大到所有量化权重处理。

新增回归源用BF16、heads4/6/8/12、三token和固定Q/NoPE/RoPE维度，对照逐中间量BF16舍入的CPU投影与独立RoPE算子，分别检查NoPE和RoPE误差，finally恢复内部format选项。这是测试定义，本次没有执行，也不能从文件描述的A3回归推广成全平台/任意head支持。新模型先核draft身份、真实head数与padded数、二维存储和cache输出形状，再按本模型维度做数值验收。

## Qwen4Exp：长度同步准入跟随实际Native类，而非同名模块

[Qwen缓存所有权](vllm_ascend_qwen4_exp_cache_ownership.md)中的稳定初始化决定继续成立。7d9e在 `can_skip_qwen_cpu_length_sync` 内按 `vllm_version_is("0.32.0")` 选类：该分支读取qsa_cache.QSAMetadataBuilder/QSAStateBackend，其余分支读取qsa_indexer.QSAIndexerMetadataBuilder/QSAIndexerBackend。QSA adapter自身也按同一版本选择AMD indexer模块、side-cache backend，以及Qwen4ExpQSAFlashAttentionBackend或Qwen4ExpQSABackend。迁移应核对实际Native配对和类对象，不能靠给旧模块做同名alias宣称完整新ABI兼容。

跳过同步仍要求精确AscendQwen4ExpModelState与AscendMTPSpeculator类型、限定架构、PCP=DCP=1、关闭sparse offload；MM须有明确非realtime encoder。target/draft全部backend-builder对须命中allowlist，双方均包含AscendQSA，且draft架构、backend和实现类精确匹配。可选Ascend state builder只有确为对应Native builder子类才加入允许列表；其余未列子类也不会自动放行。任何import或检查异常返回False，保留精确CPU计数路径。

ModelState在target/draft KV初始化之后先清skip标志，通过能力判断且存在可同步的num_computed_tokens_stream后，先synchronize旧拷贝，再将稳定标志置True；producer与consumer复用同一标志。类名更新没有取消这次等待，也没有把每batch乐观长度变成精确长度。Native类实现和QSA其余大规模接口差异仍未在本节闭合，特别是新的forward ABI、paged-KV回退和状态元数据；这里仅封闭长度sync的双版本类选择facet。

## PLE：固定512通道tile保留数值与旧state读取边界

[PLE接入合同](vllm_ascend_qwen4_exp_ple_contract.md)解释模型patch与旧2048 tile。7d9e的 `PLE_BLOCK_C` 固定改为512，`PLE_NUM_WARPS=8`保留，作用于所有Ascend分支。新增prefill文档将其动机归于避免A3的2048 tile过大UB分配；文档同时记录在已测A3 9382和A5 950DT形状上512比2048更慢，并把模型性能和原始A3 9362 compiler target的CI结果留作待证。本次未读取PR计时原值或执行设备测试，不能把较小tile写成性能收益。

wrapper输入为[T,C] inputs/residual、[slots,C,window] conv_state、[C,K] weights和每请求state_indices。模型四tap、常见dilation3，所需历史长L=(K−1)×d；源码检查state通道等于C、window>=L，并要求query_start_loc和has_initial_states。实际state及state index stride传给kernel；weights转置成连续[K,C]临时量，不修改调用者weight。token_indices可把逻辑混batch行映射回物理行，调用者仍须保证边界累计、映射容量、slot值域和连续inputs/residual，不能把少数wrapper检查当完整合法性校验。

卷积先按query累计终点二分定位请求，对每tap读取旧state或当前inputs，FP32累积后先舍入到输出dtype，再做SiLU并再舍入。outer_residual存在时先把residual_old+激活值舍入，再加outer；这一中间舍入不能因融合而省略。null slot的卷积贡献为零且不写state，并非在fused residual模式把整个输出清零。独立第二kernel按每请求最后L个“旧state+本次输入”写回，确保卷积所有token读旧state；不能把writeback并进逐token卷积而默认无跨program依赖。

模型局部dispatch只有prefill调用这两个Ascend kernel，decode/spec仍委托Native PLE；legacy private prefill method也仅在Native仍有该方法时安装。文档的FP16/BF16、state精确比对、容差及6/6通过属于作者报告，FP32未覆盖；源码存在和来源报告不构成本仓复测。C、tile、L、dilation、K、null ID、outer开关及PDL能力为编译常量，num_reqs/搜索轮数/token-map标志避免特化，但scalar stride仍可能产生变体。迁移先测输出/舍入、state精确写回、null和mixed映射，再测UB、真实变体数和模型TTFT/TPOT；固定tile没有消除重编译或内存安全验收责任。

## 可复核的源码范围与未闭合项

以下行号均属于7d9e；“有界”表示只对所列机制取证，不声称整文件或整个版本已穷尽。详细blob与全路径差异清单留在生产审计产物，不作为运行时依赖。

| 主题 | 固定源码与实际阅读范围 | 仍需另取证的边界 |
| --- | --- | --- |
| 采样状态与输出 | `_310p/worker/v2/sampler.py` 130–466；sample目录八文件完整实现；`sample_utils.py` 16–46、122–143 | 新Native父实现、prompt logprobs、全部rejection/Runner与随机分布验收 |
| 保存引用 | `ascend_store/in_flight_save_blocks.py` 1–66；pool_scheduler 704–829；layerwise/pool_scheduler 31–78、130–143；connector 63–80、117–188、516–530 | worker完成去重/失败、SDK持久化与逐层完整释放 |
| 主机权重 | `rfork/local_weights.py` 1–97；rfork_loader 752–969；tensor_layout 445–458 | 全部session协议、CANN主机分配/释放与并发修改 |
| PCP RecoverSSM | `recoverssm_config.py` 1–46；metadata 1–67；kda 425–512；mamba_hybrid 340–396；speculative_decoding文档1064–1127 | Native父build、完整PCP manager、传输和kernel数值闭包 |
| 普通TopK迁移 | fused_topk_router 113–241；DeviceOperator、Torch/Meta与构建文件完整删除差异 | SDK普通TopK Device和消费端完整dtype验收 |
| KPool类型 | glm5next/attention 40–125；triton/glm5_next_cann_keypool 1–104及INT8删除差异 | 其余Indexer/selector、Native cache分配与真实FP8/offload行为 |
| 首SWA回放 | decoder_replay_layers 18–221；state 174–199、358–422及完整差异；model/dsa_v41完整相关差异 | 全部cache更新、原始encoder边界producer、真实图执行 |
| MLA补头 | mla_v1 1025–1053、2070–2118及完整差异；head-padding测试1–92 | SDK NZ/Prolog实现、其他量化与维度 |
| QSA长度同步 | cpu_length_sync 1–115；model_state 35–59；qsa 47–76及版本选择差异 | 最新Native类实现和QSA其余forward ABI |
| PLE512 | triton_ple 1–288；新文档1–53；模型ple 20–47、211–304 | Native decode/spec、9362编译、模型数值/性能/变体计数 |

本卡可用于选择源码探针、配置拒绝条件和迁移验收矩阵；成功解析、来源引用、代码登记、Host返回或入队均不能替代执行、数值、图和端到端质量结果。
