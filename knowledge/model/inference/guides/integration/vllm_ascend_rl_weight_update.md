---
type: Guide
title: vLLM Ascend RL 权重更新：暂停、传输、版本隔离与路由回放
description: "按同卡 IPC 与跨卡 HCCL 选择更新生命周期，防止 keep 跨权重版本继续使用旧 KV，并正确消费 routed_experts、tokens-only 与 trace replay。 补充 query参数、/inference/v1/generate、Trace Replay与实际Runner选择，区分null数据和更新完成证据。 补齐HCCL/NPU IPC实际factory键、rank/wire/metadata、packed软硬容量、stream/故障storage与每chunk握手，文档ipc映射保留版本差异。 后续发布5f5e25的TITO入口改用--enable-scale-out或--tokens-only，明确输出/abort返回ID与trace opt-in。"
tags:
- task.implementation
- topic.reinforcement_learning
- topic.checkpointing
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/rl.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/rl.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/mrv2_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/user_guide/feature_guide/rl.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/weight_transfer/hccl_engine.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/weight_transfer/hccl_common.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/weight_transfer/npu_ipc_engine.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/weight_transfer/packed_tensor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/weight_transfer/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/weight_transfer/test_packed_tensor.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/distributed/weight_transfer/factory.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/device_communicators/pyhccl.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/device_communicators/pyhccl_wrapper.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/user_guide/feature_guide/rl.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/24420b7a341af37a9bc3186e6fc6062512e0aa58/vllm/entrypoints/scale_out/factories.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/24420b7a341af37a9bc3186e6fc6062512e0aa58/vllm/entrypoints/scale_out/token_in_token_out/api_router.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/24420b7a341af37a9bc3186e6fc6062512e0aa58/vllm/entrypoints/scale_out/token_in_token_out/serving.py
  role: implementation
created_at: '2026-10-29T09:42:28Z'
updated_at: '2026-11-03T09:36:02Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- HCCLWeightTransferEngine
- NPUIPCWeightTransferEngine
- packed_broadcast_consumer
- packed_npu_ipc_consumer
- PyHcclCommunicator.close
- HCCLLibrary.HCCL_CHECK
---

# vLLM Ascend RL 权重更新：暂停、传输、版本隔离与路由回放

## 前提与统一配置

rl_config.enabled=true 应用于同卡/跨卡 rollout，强制 weight_nz_mode=0、启用开发端点并移除 allocator expandable_segments。optional cleanup、training_consistency、batch_invariant 默认 false，依赖主开关。FA3 与 batch invariance 仍各有安装和能力限制，不能用 RL 总开关替代。

## 权重更新事务

同物理 NPU 使用 ipc，Ascend 映射 NPUIPCWeightTransferEngine，配合 sleep 释放给 trainer；不同 NPU 使用 hccl，通常暂停即可。先初始化 transfer engine，再 pause、start update、分组传权重、finish update、resume，所有 worker 权重一致才恢复。HTTP IPC 示例的句柄序列化开关只在可信环境使用，不能当普通在线服务默认值。

pause=abort 默认终止现有请求；wait 排空；keep 冻结并在 resume 后继续，clear_cache 在 keep 被忽略。keep 请求可能携带旧权重 token/KV，严格单版本 rollout 使用 abort/wait，并清理旧状态。Level2 sleep 另按[恢复顺序](vllm_ascend_sleep_wakeup_lifecycle.md)先权重后 KV。

## 回放和训练数据

enable-return-routed-experts 返回 nonstream choices 的 base64 NumPy 数据，shape=(num_tokens-1,num_layers,num_experts_per_tok)；末 token 未前向无路由，不能人为补一行。未捕获或 forward 前 abort 可为 null。prompt_logprobs 不支持 streaming completion。

ceac/3164文档中的tokens-only 是实验入口；trace replay 仅 MRv2，当时普通 serve 配方需 VLLM_USE_V2_MODEL_RUNNER=1、VLLM_ENABLE_SCALE_OUT_ENDPOINTS=1 和 enable-trace-replay。强制 token 序列的 logprobs 来自真实模型分布，不等于模型自发生成这些 token。工具调用 parser 按目标模型选。X-data-parallel-rank 可定向路由；本版本没有 vllm serve router / dp-routing-config，不能给 Agent 生成不存在的命令。

## 验收与回退

记录 update version、各 worker 参数校验、暂停模式、旧请求去向、logprobs 对齐和恢复后输出；更新失败保持暂停并加载完整已知权重，不能恢复部分更新模型。训练一致性见[FA3](vllm_ascend_fa3_training_consistency.md)，跨 batch 重现另见[batch invariance](vllm_ascend_batch_invariance_validation.md)。本次未执行通信或训练。


## 平台证据待补

RL概述的A2/A3句子只修饰batch invariance局部能力，不能提升为同卡IPC、跨卡HCCL、路由回放与更新事务的整卡范围。本卡据此撤回原平台枚举，保持draft、空平台；已有机制与操作条件保留为待验证知识。取得针对本功能的明确硬件范围和组合证据后再更新状态，不能把本次修正解读为这些硬件不支持。


## RL中文全文与控制参数的传递边界

新增对照rl.md全文407行与rl.po全部90条业务译文，89条msgid完全匹配；另1条仅在六步控制流的finish与resume之间删去英文and，顺序不变，中文“以及”可保留。该对照不证明HTTP端点已注册、IPC/HCCL传输完成或全部worker已换到新权重。

rl_config.enabled只应用公共默认值，sleep_mode_extra_cleanup、enable_training_consistency、enable_batch_invariant仍各自默认false；主开关为真不自动打开全部optional能力。对照生效配置中的weight_nz_mode=0、allocator选项和开发端点，再选择同物理NPU的ipc或分离NPU的hccl；同机器/同板的称谓不代替实际设备身份与backend可达性检查。

### Sleep、pause和权重版本隔离

文档的sleep level、wake tags及pause参数都放在query string，不能把JSON body中的level当已生效。level1是CPU卸载权重并丢弃KV，level2丢弃两者；level2的顺序为/sleep?level=2、/wake_up?tags=weights、加载或传输完整新权重、/wake_up?tags=kv_cache。extra cleanup另释放HCCL/ACL图资源，恢复时需重建或重捕获，不把释放得更干净直接当净性能收益。

权重事务仍为initialize、pause、start、分组transfer、finish、resume。/pause?mode=wait&clear_cache=true是文档示例；keep会冻结请求且忽略已弃用clear_cache，旧token/KV可能跨到新权重继续运行。更新失败不自动resume部分模型；必须核实各worker版本和完成信号。HTTP IPC句柄示例需要VLLM_ALLOW_INSECURE_SERIALIZATION=1，开发端点和这种序列化仅按文档的可信环境条件使用。本批没有设置环境、调用这些端点或传输权重。

### Tokens API、R3与Trace Replay分别验收

实验性/inference/v1/generate接收token_ids，返回choices[].token_ids；示例里的logprobs、prompt_logprobs、usage或routed_experts为null不能解释成零成本、零概率或不需要训练数据。R3非流式choices[].routed_experts为base64 NumPy数据，保留文档的(num_tokens-1,num_layers,num_experts_per_tok)约束和末token未前向说明；具体prompt/output切片与padding仍须按实际接口和训练消费端核对，不能补一行虚构路由。

Trace Replay在sampling_params.trace_decode_token_ids里给定序列，例如[15,284,1026,374]，用于强制解码并获取当前推理配置下的真实logprobs；返回同一token序列不证明模型会自发生成它，也不是模型质量或不同batch完全一致的证明。普通serve需要VLLM_USE_V2_MODEL_RUNNER=1、VLLM_ENABLE_SCALE_OUT_ENDPOINTS=1和enable-trace-replay；tokens-only入口与这些显式注册/Runner条件分别记录。按[Runner选择规则](../../optimizations/rules/vllm_ascend_model_runner_selection.md)检查每个进程实际选择，不能仅凭文档的default措辞推定执行类。

X-data-parallel-rank在文档中是整数路由头，不是rank范围已验证或外部router已经运行的证明；当前没有vllm serve router或dp-routing-config命令。工具调用按目标parser/model匹配，返回tool call也不等于环境已执行工具。训练一致性的FA3包、A2/A3局部batch invariance、COMPILE_CUSTOM_KERNELS、PIECEWISE、HCCL_DETERMINISTIC=strict与LCCL_DETERMINISTIC=1各有条件；它们不补齐整项RL更新事务的硬件矩阵，继续保持draft、空平台和未执行通信/训练的状态。


## 2026-11-03 main 增量：Sparse HCCL 是原位 checkpoint 更新

本节固定新增3164adc8fe75892fbf7f99f524bb72fddf1e6efd的rl.md全文435行，不回写成ceac基线已支持的能力。该文新增sparse_hccl，用于分离NPU上替换选定checkpoint权重值；trainer与rollout必须从同一checkpoint出发。它不是稀疏注意力、MoE少路由几个专家或完整权重任意格式的传输别名。

预留trainer独立NPU，文档的transfer group大小为1+TP*DP，不再乘EP；示例TP2显式启用expert parallel，PP目前不支持。Sparse HCCL要求未量化ND权重与静态专家放置、关闭EPLB；FRACTAL_NZ、融合MC2专家weight list、draft模型和packed sparse update均未支持。传输组公式、API backend注册和数据表示是独立条件，不能只改变backend字符串就沿用原部署所有组合。

更新原位生效，失败后可能只完成部分参数；继续保持generation暂停，直至恢复baseline或重启engine，不能在finish接口异常后自动resume。仍按本卡原六阶段及worker权重版本证据验收。本节只生产这份文档的合同；未读取其外链Sparse NCCL协议全文、执行示例、校验真实patch或证明任何设备/量化组合已通过。


## ceac 实现增补：HCCL、NPU IPC 与 packed buffer 的真实生命周期

本节回到原ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，不与上一节3164的sparse_hccl混成同一实现。完整读取Main五文件：HCCL engine339、common89、NPU IPC289、packed_tensor449及注册45行；专项packed UT只读979–1064/1147–1190。另完整读取实际paired544的factory.py289行，作为配对入口约束，不计独立Native5df摄取。没有闭合Native父类全部reload/start/finish/HTTP生命周期、外部通信器或torch_npu IPC ABI，更未运行上游。

### 文档 ipc 名称与已读 factory 入口有差异

原文档称用户ipc会映射NPU IPC，但固定Main register_engine实际为worker/trainer分别注册hccl和npu_ipc，NPUIPCTrainerInitInfo.backend也是npu_ipc；paired544的factory按config.backend或init_info.backend精确查registry，没有在这两个方法里将ipc改名。不能仅由文档一句映射就宣布这套实际配对已自动选择NPU实现。其他配置预处理/安装补丁是否完成重映射未在本节闭合，保留未知并记录真实backend、factory最终类与导入版本，不把普通Native CUDA IPC类误报为NPU类。

两套registry彼此独立，重复key会ValueError，不是覆盖式注册。trainer_init从init_info.backend取后端，不从worker config推trainer配置。NPUIPC旧静态trainer_send_weights明确NotImplementedError，需走TrainerFactory及send_weights；换用户字符串或成功注册并不证明传输初始化完成。

### HCCL rendezvous、wire 参数与失败状态

HCCL只接受TCP rendezvous，拒绝nccl_unique_id_b64，world_size至少2；stateless group不使用torch默认通信组，available/disabled不满足即失败。worker rank=data_parallel_index*parallel.world_size+parallel.rank+rank_offset，sender占rank0、标准trainer设置worker offset1。这里的parallel.world_size不能不加区分替换成TP或再乘任意EP；按实际Native并行对象核对全体唯一rank。

packed及容量在init和每次update都保留None与显式False/值的区别：init显式固定值优先，与update显式冲突就拒绝；init未固定时取update或backend默认。worker默认packed=False，trainer构造默认True；正确handshake必须传一致wire参数，不能只比较构造默认。buffer/count需正整数且不能bool，dtype名称必须解析为torch.dtype。

receive先按本轮update解析wire参数，再按model对象缓存参数metadata；update省略names时可复用该model旧metadata，换模型或重启session不能复用别的model缓存。init先shutdown并重建metadata cache。HCCL接收/父update wrapper都绑定worker assigned NPU，不依赖ambient current device；unpacked发送也等当前stream完成以保持staging storage存活。

sender的worker init RPC放side thread与本地rendezvous并行，非sender trainer仍消费source以参加trainer侧collective。send_weights失败把trainer设failed并尝试释放group，后续send拒绝，closed也拒绝；需要重建engine，不原地盲重试。异步RPC线程安排不等于提供完整失败取消/事务回滚，旧权重混合风险仍按前文保持generation暂停处理。

### HCCL 软分块与 IPC 硬容量不是一个内存合同

默认target buffer为1024^3字节、HCCL两slot。HCCL producer/consumer都在加入完整tensor后检测累计字节>target才结束该chunk，因此1GiB是分块目标，不是严格峰值上限；一个大tensor可让chunk超出目标。两端需完全一致的tensor顺序、shape/dtype、buffer target及slot数，否则collective大小/顺序可能不匹配。post_iter只检查dtype与numel，展平后元素顺序仍由caller保证；转置后同numel不等于元数据仍正确。

HCCL packing可与前一次transfer交错，但同一communicator的不同stream broadcast串行化：producer在下一次broadcast前等待上一transfer stream，并把真实packing stream显式传给通信器。consumer在外部HCCL receive完成后才拆包/clone/load；不能把Python broadcast返回当buffer已可读，也不能让并发更新共享同一communicator和slot。

consumer对每个参数先clone字节，再view dtype/reshape，既给loader独立storage，也处理异dtype字节片段的对齐。峰值还包含receive buffer、一个chunk的克隆及loader保留副本，不能按两倍目标容量直接封顶。源码不提供完整权重事务回滚，load_weights部分成功后报错不能恢复generation当旧模型仍完整。

IPC producer则只分配一个严格buffer_size_bytes大小的共享uint8 buffer，一次reduce_tensor注册、跨chunk复用；单tensor超过容量立即拒绝，tensor不会拆成任意字节片段。全为zero-element但非空metadata也产一个chunk，真正空iterator无chunk。每chunk yield前同步，trainer每次_do_send后再全rank barrier及NPU同步，防止非sender先覆盖仍被同卡worker读取的buffer；不能把“一个IPC句柄”解释成无需每chunk完成握手。

### NPU 身份、metadata 与输出所有权

NPU IPC身份是缓存的host IP加ASCEND_RT_VISIBLE_DEVICES映射后的物理chip编号；trainer/worker逻辑index可以不同，但必须指同一物理NPU。它不是跨主机远程HCCL的身份替代。更换可见设备映射或网络环境后，不能假定同进程缓存会自动刷新。rebuild tuple第6位改为接收端assigned device index，需与实际torch_npu ABI匹配，本卡只读代码没有实测ABI。

packed IPC consumer在rebuild前检查本地device index、UUID、dtype、names/shapes/sizes列表等长、非负shape/size和每tensor字节精确值；rebuild后再检查总payload不超过共享buffer并只取有效前缀。每参数clone后才交loader，可保留或修改而不alias后续chunk。unpacked路径是另一组校验/生命周期，不能把packed helper的所有guard自动套给它。

本地HCCL/IPC receive都在disable_mtp_completeness_check作用域增量load_weights，允许分组或跨chunk更新；这个局部免检查不是全部必需MTP参数已经加载的证据。完整更新、模型新旧版本隔离及最终head/量化参数验收仍需实际父类与模型合同，见[配对权重loader](vllm_ascend_paired_native_weight_loader_contract.md)。

### 错误清理与验证信号

packed HCCL在finally尝试drain每slot；drain失败将仍有payload的storage留在_UNSYNCHRONIZED_BUFFERS直到进程退出。该列表不提供串行化且故障路径无界，清列表或靠Python Stream wrapper销毁回收并不能证明native async工作完成，重复故障可能耗尽内存。清理成功也不证明部分权重更新已回滚。

有界UT定义receive-before-unpack、错误传播前drain、drain失败保留storage和原异常等mock顺序；未执行，也不证明HCCL/跨进程IPC或模型精度。Agent需要保存版本对、实际factory类、物理/逻辑NPU、完整rank组、wire参数、每chunk字节、stream事件、model metadata身份与更新版本，覆盖混合dtype/未对齐片段、scalar/empty、超大tensor、复用chunk、各阶段失败和恢复后的真实输出。分别测序列化、packing/clone、collective、loader和图/缓存恢复，再报端到端rollout吞吐；API完成或少拷贝次数不能替代这些证据。

## PyHCCL底层：可用性、rank、stream与关闭不是同一状态

补充完整静态阅读Main pyhccl185行与wrapper264行，并有界核对utils606–642和hccl_common55–80，保留共享owner。wrapper的HcclRootInfo视图固定4108字节，comm/stream为void指针，count为c_size_t；该ABI来自固定源码声明，未对安装HCCL头/库实测，不能将注释里的外链版本当当前ABI验收。

HCCLLibrary按路径缓存CDLL和符号表，查找HCCL_SO_PATH优先，否则仅在torch.version.cann非None时用libhccl.so；没有构建库版本或每个ABI签名的动态能力协商。当前封装实际映射Torch的I8/U8/I32/I64/FP16/FP32/FP64/BF16及SUM/PRODUCT/MAX/MIN，枚举声明的INT16/UINT16/UINT32等并未全部由from_torch开放，bool/FP8也没有映射。所有C调用检查非0返回并经HcclGetErrorString抛错，但返回0只说明调用返回，不等于设备工作全部完成。

普通ProcessGroup必须已初始化且backend不是HCCL，用它broadcast root info；group内rank0经真实global ranks[0]作为dist.broadcast源。StatelessProcessGroup则用其group rank和broadcast_obj。HCCL communicator绑定明确NPU，每个对象与唯一device的对应是caller责任；文档中的group/device可None措辞未由构造签名或代码实现通用None缺省。

world_size1直接available=False/disabled=True；库或缺符号初始化异常也会禁用返回，此时all_reduce返回None、broadcast空返回。hccl_common实际worker初始化明确检查available和disabled，避免把静默no-op当成功传输。其他自定义caller也须执行等效guard；不能只见函数未抛错就继续加载新权重。

初始化获取/广播unique ID，再HcclCommInitRootInfo，在绑定device下做一次小all_reduce并同步stream。其all_reduce实际分配empty_like输出、把输入/输出两个指针交HCCL并返回新Tensor，不原位改输入；broadcast才原位使用同一buffer。二者仅检查device一致，未在此完整验证contiguous、跨rank dtype/count顺序或view容量。广播src直接透传HCCL root，应是此comm的rank，不把普通dist.broadcast的global源规则搬到这里。

未显式stream时用缓存current_stream，显式stream直接传npu_stream指针，不自动建立生产者/消费者跨流依赖。utils这段只展示_CURRENT_STREAM首次缓存，完整set_stream补丁与多device缓存维护未在此闭合；自定义调用要确认真实stream/device身份。collective返回后仍须按consumer需要安排wait/event或同步，并保持输入、输出、packed buffer及comm存活。

close先available=False，再对绑定device全同步并destroy，正常重复调用最多销毁一次；同步或destroy抛错时对象已标不可用，再close不会自动重试未完成清理。不要将标志False等同于native句柄已安全释放，也不重置状态继续提交。已成功初始化且关闭后all_reduce/broadcast会拒绝；初始化disabled的对象仍优先走no-op分支。故障storage、跨rank一致退出和完整更新回滚继续沿前文处理，本节未加载库、建立通信组或执行任何NPU操作。

## 2026-11-03 发布快照：TITO 注册、返回 ID 与 trace opt-in

本节固定 `5f5e25dd94db85b59251be7d3baf7c808475b6d7` 的 RL 文档，并核对实际中文 HTML。前文 `VLLM_ENABLE_SCALE_OUT_ENDPOINTS=1` 是 ceac/3164 文档配方；后续公开文档改为 CLI `--enable-scale-out`，不要混用两个版本的入口声明。Native main pin 已变为24420b7a341af37a9bc3186e6fc6062512e0aa58；本节没有以发布文档替代该 Native 的完整HTTP实现验收。

TITO `/inference/v1/generate` 有两种服务模式：`--tokens-only` 跳过 tokenizer 初始化；普通服务用 `--enable-scale-out` 保留 tokenizer。两项都不启用时，文档声明 TITO 请求返回403。客户端先完成 tokenization/chat template 并传 token_ids；默认 output_mode=tokens。tokens-only 不支持 stop strings，使用 sampling_params.stop_token_ids；text 输出另要求 tokenizer。

nonstream token 输出的 logprobs.content 按生成位置给 integer token_id、logprob、rank 与 top_logprobs；usage 无须 stream_options.include_usage。文档的 token123/456、总量3+2=5和length终止只是结构示例，非捕获的模型结果。stream=true 用 SSE 并以 `data: [DONE]` 结束；取消请求向 `/inference/v1/abort_requests` POST request_ids，必须使用服务返回的完整 `generate-tokens-…` ID，不使用原始客户端ID。

Trace Replay 仍要求实际 MRv2；普通服务同时显式 `--enable-scale-out --enable-trace-replay`。后者是接受回放请求的 opt-in，不因注册 TITO 自动开启。权重版本隔离、暂停/恢复事务与IPC/HCCL合同继续按原有各版本处理，本次没有调用端点或执行训练/通信。

对配对 Native24420 仅有界读取 scale_out factories、TITO router 和返回ID片段：普通服务未enable时确实为相关route注册403 handler；generate构造generate-tokens-前缀ID，abort将传入列表交后台async task后立即200。这个200是取消请求已接收，不是所有engine请求已经终止；仍需查询/日志确认实际退出。本节未闭合全部请求schema、采样、tokenizer或权重更新生命周期。
