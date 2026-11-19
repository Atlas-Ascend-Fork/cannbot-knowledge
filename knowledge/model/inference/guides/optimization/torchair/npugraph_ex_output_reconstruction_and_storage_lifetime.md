---
type: Guide
title: 独立npugraph_ex输出重建：弱引用、共享Storage与逐项克隆
description: 保留输出重建消费者，补完整双版元数据、格式、浅层重建、Dump及诊断helper边界。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
created_at: '2026-11-10T12:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 独立npugraph_ex输出重建：弱引用、共享Storage与逐项克隆

## 固定路径与证据边界

本卡只定向核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c中独立npugraph_ex的输出记录、reconstruct_outputs与metadata helper；不把这些字段或布尔选项用于同名legacy/发布实现。公共开关前提仍见[内存池与clone](npugraph_ex_memory_pool_and_clone.md)。

未导入、捕获、执行设备、验证别名或测量显存/耗时；也未展开底层checkpoint allocator的完整实现。整卡平台未知，保持draft与空平台。以下解释Python实际选择的重建步骤及显式copy，不认证任意并发、输出树和存储组合。

## metadata记录Storage基址和容量

capture为Tensor输出先保存WeakRef(None)及TensorMetadata，非Tensor输出由WeakRef包装直接保存对象。WeakRef对Tensor才使用weakref.ref，类名不代表所有对象都不被持有。

TensorMetadata记录shape、stride、dtype、device、format、storage_offset，以及untyped_storage的data_ptr和nbytes。后两个是Storage基址与容量，不等于当前Tensor逻辑起始地址和numel字节数；小切片可能仍描述更大的原Storage。

reconstruct_from_tensor_metadata将这些字段交给_construct_storage_from_data_pointer与_construct_NPU_Tensor_From_Storage_And_Metadata。该Python函数没有先clone整个结果；这份裸地址重建需要随后建立正确Storage持有/释放关系，不能只把新Python Tensor对象视为新分配且隔离的数据快照。

## 优先走保留或存活Storage路线

| reconstruct_outputs条件 | 本地处理与成本 |
| --- | --- |
| 配置明确reuse_graph_pool_in_same_fx=False | 使用当前key的retained_outputs，记录非输入引用Storage后执行可选clone。 |
| 当前只有一个graph key | 同样直接使用retained_outputs，不进入多key输出重建。 |
| 多key且丢失的视图都能关联到仍存活的同址输出Storage | 构造缺失的Tensor包装，用存活Storage及原offset/shape/stride执行set_，不走完整checkpoint/deleter重建。 |
| 存在无法从存活输出取得的Storage | 进入pool状态处理、按metadata重建，再clone或关联deleter。 |

construct_outputs_based_on_ref不只处理“所有弱引用都仍活着”：某些视图对象已释放，但另一个同storage基址的输出还活着时，也能共享其Storage恢复视图。只有不能为某个重建地址找到存活Storage时才返回None进入后续路径。

因此单key、同Storage多视图和多个独立输出的Host开销不同；不能用一次输出重建的耗时代表所有key和所有输出存活模式。保持结果引用也会影响所走分支，不等于一定避免旧结果被后续设备执行改写。

## 完整重建会处理pool状态和deleter

set_to_original_state_bofore_reconstruct遍历各key的输出弱引用，仅收集当前设备、位于stale_storages_ptr集合且不是输入引用输出的存活Tensor。需要时调用_npu_setCheckpointPoolState恢复原checkpoint，并清空该stale集合；不是无条件把所有活Tensor都释放或迁移。

随后按metadata重建输出并更新弱引用。未启用clone_output时，set_reconstructed_outputs_deleter按Storage data_ptr去重，收集需要关联deleter的Storage标识，并将开启clone_input时重建的输入Storage一起交给捕获后checkpoint状态。多个Python输出共用同一数据地址时，再通过set_统一到同一个Storage对象，保留各自offset、shape和stride。

这一步建立裸地址包装与allocator状态的关联，不能任意删除或仅以Python引用计数替代。源码在相应无clone重建分支给出旧输出可能被后续执行覆盖的告警；本卡没有证明所有路径每次都会告警，也没有完成底层所有生命周期或多流安全审计。

## clone_output按返回列表逐项执行

_clone_outputs_if_enabled在开关为真时，对Tensor输出调用clone，但排除其untyped_storage()._cdata已在userinput_ref_with_output_storages_ptr中的项；其他对象原样返回。这个排除以已记录Storage对象标识为依据，不是在本helper中对本次所有用户输入重新执行通用别名分析。

克隆按输出列表每项独立进行，没有按原Storage地址去重。多个返回项即使原先是同一数据的视图，也可能发生多份显式复制；不能从这个helper假定克隆结果之间仍保留原有alias关系，最终返回结构和别名合同需要单独验证。

显式数据量可先按实际被clone各项的numel乘element_size求和，再计allocator、对齐与设备执行成本；它不是只复制一次最大共享Storage。相反，未被clone的输入引用输出也不能被当成隔离快照。clone_output更换了部分返回存储的持有方式，不等于关闭全部pool复用或免去replay前的输入copy。

## 比较时覆盖输出存活模式

分别记录单/多key、明确禁用pool复用、普通输出/视图/输入引用、哪些弱引用仍存活、是否触发checkpoint、实际clone项数与字节数，再与[输入固定缓冲复制](npugraph_ex_replay_input_buffers_and_copy_paths.md)一起计入完整调用。

检查返回Tensor的shape、stride、storage_offset、storage基址及Storage标识，并验证跨次调用保留结果的实际内容；不能只看Python对象新旧或逻辑shape判断数据已被复制、内存已缩小或生命周期已正确。本卡没有收益数据或新增verified。

## Evidence

- [独立输出重建链](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（primary）：1458–1465、1615–1635、1752–2034。
- [弱引用与metadata重建](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：42–69、88–177。

## 双版完整Host元数据与格式helper

已补完整utils.py主线545行和发布506行；原acl_graph输出重建消费者定向证据保持原范围，没有升级整份acl_graph或底层C++。两版WeakRef对非Tensor直接强持有，swap_weakref也可改变持有类型；LazyMessage每次str时重新调用所存函数，没有结果缓存。

TensorMetadata的size/stride/nbytes/dtype/data_ptr/storage_offset/device/npu_format外，还有layout默认strided、memory_format默认contiguous_format、requires_grad默认False。get_tensor_metadata记录实际layout/requires_grad，却没有把Tensor的任意实际memory_format另写进去，不能用这个默认值认证原张量连续；torch_npu未在sys.modules时format记ND，已加载时也只对NPU Tensor查询格式。非Tensor原样返回。

GraphMeta的数据字段按职责分组：graph_key/acl_graph/replay_func；outputs_meta/outputs_weakref/mem_state_after_capture；userinputs_meta/userinputs_metatensor/userinputs_weakref；captured_parameter/captured_mutated_inputs/captured_userinput_ref_with_output；retained_userinputs/captured_output_idx_ref_with_userinput；retained_outputs默认None。字典和集合用default_factory避免实例共享默认容器，但类型注解不是运行时完整合法性检查，也不自动建立Storage所有权。

reconstruct_from_tensor_metadata虽注解Dict，实际只接受TensorMetadata，否则RuntimeError；asdict后把基址、设备、容量交C++重建。reconstruct_tensor_list只接受tuple/list，返回list，仅直接Tensor项重建；reconstruct_args_kwargs也只处理外层Tensor及一层tuple/list，嵌套容器不递归。新包装不等于复制数据或保证裸指针存活，完整所有权路线仍按前文消费者核对。

Format本地枚举为UNDEFINED=-1、NCHW=0、NHWC=1、ND=2、NC1HWC0=3、FRACTAL_Z=4、NC1HWC0_C04=12、HWCN=16、NDHWC=27、FRACTAL_NZ=29、NCDHW=30、NDC1HWC0=32、FRACTAL_Z_3D=33、NC=35、NCL=47、FRACTAL_NZ_C0_2=52、C0_4=53、C0_8=54，名称均带FORMAT_前缀且末三项保留FRACTAL_NZ_前缀。这18项只列本地数值，不是产品支持矩阵。base-format集合仅NCHW/NHWC/ND/NCDHW；CPU直接True，其他设备缺torch_npu时False，否则按实际查询值判断；输入列表逐项all，空列表自然True。

## 诊断、Dump与配置解析不等于设备验收

debug_mem_state只汇总带segment_pool_id且不为(0,0)的内存段，返回device/stream/pool、block数量、active_allocated数量及total/allocated字节的字符串。timer以time.time包yield后正常返回的日志，没有设备同步或finally异常计时；二者都不是Kernel耗时/峰值显存证明。

insert_save_npugraph_tensor先快照节点，跳过output、save本身及已有save用户者；只要求meta字典有tensor_meta键，不完整验证输出是单个Tensor，也不排除placeholder。其后插npu.save_npugraph_tensor.default，路径为base_dir/node_name.pt并recompile；这里不创建目录或直接执行保存。发布要求configs的aclgraph.enableDump严格等于字符串'1'，并从aclgraph.dumpPath读目录；主线接受data_dump_path，没有相同内部开关判断，None用'./'，调用者负责开关。

run_deadlock_check取当前设备vector_core_num，再调用filter_comm_ops与deadlock_check(aivec_total=...)，这里不返回独立诊断结果，也未闭合这两个外部实现。主线parse_config对None返回None，对dict返回同一对象，其他交ast.literal_eval；不是任意eval，也不在此保证解析结果一定是dict。发布utils没有此本地parser，不据此断言其它配置入口不能解析。

原地化用户收集与流checker的完整来源段由[原地化合同](npugraph_ex_reinplace_alias_and_stream_checks.md)承接；本卡不把诊断元数据或保存节点当成多流、数值、性能已通过，也没有新增verified。

## 完整本地源码证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：1–545；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：1–506；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。

## 发布输出克隆不会覆盖所有返回路线

本节把固定发布7c6c754的reconstruct_outputs与主线对应块直接对照；只扩充这些本地返回路线，不重审底层allocator，也不把前文主线clone选项名用于发布内部字典。

| 返回路线 | 主线92e1e967 | 发布7c6c754 |
| --- | --- | --- |
| 明确禁用同FX池复用 | 取retained_outputs后经过_clone_outputs_if_enabled。 | 直接返回retained_outputs，不到输出克隆代码。 |
| 当前只有一个graph key | 取retained_outputs后经过同一helper。 | 直接返回retained_outputs，不到输出克隆代码。 |
| construct_outputs_based_on_ref返回非None | 结果经过同一helper后返回。 | 直接返回结果，不到输出克隆代码。 |
| 需要完整metadata重建 | 重建后经过同一helper；未启用clone时关联deleter。 | 仅此路线再检查enable_output_clone，启用时逐项clone，否则关联deleter并告警。 |

主线helper以clone_output键存在且值为真为条件；发布完整重建分支要求enable_output_clone键存在且严格等于字符串'1'。主线禁复用的返回条件是reuse_graph_pool_in_same_fx is False，发布则是disable_mempool_reuse_in_same_fx == '1'。这些是固定内部消费者的键名和比较方式，不应互换字段或用任意假值替代各自判断。

因此，发布即使开启该输出克隆选项，在单key、禁复用或可用存活Storage的上述早返回路径，也不能仅凭开关认定这里已制造独立结果快照；主线在相应路径有helper调用，但仍保留前文输入引用输出不clone的排除。发布完整重建的逐项clone也按Tensor和已登记Storage标识排除输入引用输出，没有按原Storage去重，也不保证克隆后仍保留全部输出alias。

比较版本或测量clone成本时，要记录实际返回路线与clone项，而非只记配置值。此处没有执行跨次覆盖、所有权、并发、数值或性能验证；外部被调实现及其他未读发布段保持独立。

## 有界版本对照来源

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（primary）：1752–1858；仅支持本节新增局部合同，不提升整模块或外部被调实现资格。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：1343–1427；仅支持本节新增局部合同，不提升整模块或外部被调实现资格。
