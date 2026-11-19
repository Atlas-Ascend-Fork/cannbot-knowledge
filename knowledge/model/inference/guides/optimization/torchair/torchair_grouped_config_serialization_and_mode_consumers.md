---
type: Guide
title: TorchAir分组配置：序列化与模式消费者
description: 核对两固定版GE、实验、AOE、融合与Debug分组怎样输出local/global及被再次归一化，保留tiling归属和主线新字段差异。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/aoe_config.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/aoe_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/fusion_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/fusion_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/inference_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/inference_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/ge_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/ge_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
created_at: '2026-11-11T03:20:13Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---


# TorchAir分组配置：序列化与模式消费者

本卡绑定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的集成配置模块；主线消费者只限定Evidence所列范围。产品和完整配套未知，保持draft、空平台。赋值校验及根合并规则复用[配置入口](torchair_compiler_config_boundaries.md)；这里只证明本地值怎样流向选项和已读消费者，没有编译、设备或性能验证。

## GE、AOE、融合与推理的不同输出

| 配置组与本地默认 | as_dict的实际输出 |
| --- | --- |
| aoe_config：aoe_mode=None，候选仅字符串2；work_path=./；aoe_config_file=None | mode未设置返回两个空字典，否则复用基类，将非None字段作为local键aoe_mode/work_path/aoe_config_file；形参mode没有继续传给基类。路径赋值分别由目录/文件setter校验。 |
| fusion_config：fusion_switch_file=None | 非None时只在global写ge.fusionSwitchFile；不检查此处mode。文件内容与融合实际采用交下游。 |
| inference_config：dynamic_gears_merge_policy=zip，候选zip/product | as_dict总返回空字典对；该配置由消费者直接读取，不能按空输出断言未生效。 |
| ge_config：enable_single_stream=False，oo_level=O3且候选O1/O3，oo_constant_folding/oo_dead_code_elimination=None | global的ge.enableSingleStream用true/false小写字串，ge.oo.level直接取值；两个非None覆写分别输出ge.oo.constantFolding/ge.oo.deadCodeElimination的true/false。 |
| ge_config：export_compile_stat=字符串2，候选0/1/2；aicore_num、optimization_switch默认None | ge.exportCompileStat总输出到global；后两项非None时写ge.aicoreNum/ge.optimizationSwitch到global，此处没有单独核数范围校验。 |
| 主线ge_config额外multistream_parallel_mode=None | 非None写local的ge.autoMultistreamParallelMode；发布无此字段与输出。 |

_GEConfig.as_dict未按mode分支；oo_level=O1时还向local写ge.topoSortingMode=3（StableRDFS）。根构造顺序中ge_config晚于experimental_config，其同名local键可覆盖实验组原有排序模式。字段来自哪个组以及合并顺序会影响结果；根dict也不会完整表达所有Python级选择。

## 实验组选项的完整本地声明

| 默认及检查 | 字段 |
| --- | --- |
| False，候选True/False | cc_parallel_enable、memory_efficiency、frozen_parameter、npu_fx_pass、aot_config_enable_joint_graph、enable_ref_data、tiling_schedule_optimize。 |
| True，候选True/False | keep_inference_input_mutations、enable_view_optimize、remove_noop_ops、pattern_fusion_pass。 |
| None，IntRangeValue范围[-1,2**63-1] | static_model_ops_lower_limit。 |
| auto，候选只有auto | jit_compile。 |
| 0，无候选列表限制 | aot_config_output_loss_index。 |
| DFS，候选BFS/DFS/RDFS/StableRDFS | topology_sorting_strategy。 |

_ExperimentalConfig.as_dict在所有模式先输出local的remove_noop_ops、pattern_fusion_pass、frozen_parameter。max-autotune另将cc_parallel_enable转换为global ge.exec.enableEngineParallel；memory_efficiency转local ge.featureBaseRefreshable；topology_sorting_strategy按BFS=0、DFS=1、RDFS=2、StableRDFS=3转local ge.topoSortingMode；auto对应local ge.jit_compile=2；非None下限写local ge.exec.static_model_ops_lower_limit。

tiling_schedule_optimize是明确版本差异：发布写global的ge.tiling_schedule_optimize，主线改写local，同为1/0字符串。不能只比较键名和值而忽略所属字典。非max-autotune不输出这组GE选项，转而合并aclgraph实验子组选项。

表中keep_inference_input_mutations、npu_fx_pass、aot_config_enable_joint_graph、aot_config_output_loss_index、enable_ref_data、enable_view_optimize未由这个as_dict直接完整输出。主线AOT调用在普通非缓存分支直接读joint_graph/输出loss索引，未走joint分支时直接读keep_inference_input_mutations；索引再转int。它们不是必须出现在GE字典里的配置。其余Pass/RefData的使用继续按[FX Pass与融合控制](torchair_fx_pass_and_fusion_controls.md)、[GE运行绑定](torchair_ge_runtime_binding_and_first_call.md)核对，不在本卡推导全部消费者。

## 捕获实验子组只输出实际开启的私有能力

_AclGraphExperimentalConfig两版均声明_aclnn_static_shape_kernel=False、_aclnn_static_shape_kernel_build_dir=None、_aclnn_static_shape_kernel_sym_value_range=None、_aclnn_static_shape_kernel_sym_index=0（0..INT64_MAX），以及_super_kernel_optimize=False、两个_super_kernel_*_options字典=None。类型分别使用bool候选包装、StrOptionValue、IntListValue、IntRangeValue与DictOptionValue。

max-autotune下子组返回空字典。其他mode只有静态kernel.value为字符串1时，才输出启用项、build_dir（None变空串）、sym_value_range原列表/tuple或None，以及sym_index的字符串值。super_kernel开关为1时输出开关，两个非None字典才附带；未开启时不会仅因提供字典或目录就输出这些附加值。这里的空串转换只在序列化时，不能反推出原字段被改写为默认空串。

源码注释将sym_value_range=None解释为所有symbol值都需触发静态编译，sym_index默认0用于选择第一个symbol、检查其值是否落在指定range；这是本配置模块的注释约定，实际筛选仍需下游消费者单独核对。

## Debug字段与实际消费者的再次处理

debug.aclgraph的默认False字段为disable_reinplace_inplaceable_ops_pass、disable_reinplace_input_mutated_ops_pass、disable_mempool_reuse_in_same_fx、enable_output_clone；clone_input/remove_cat_ops默认True；static_capture_size_limit=64，范围1..INT64_MAX。这个子组as_dict只返回一个local字典，包含disable_mempool_reuse_in_same_fx、enable_output_clone、static_capture_size_limit、clone_input；两个reinplace开关和remove_cat_ops没有被此函数输出。

_DebugConfig包装graph_dump/data_dump/fx_summary，run_eagerly默认False，主线另有deadlock_check=False而发布没有。其as_dict取上述aclgraph字典，再写run_eagerly及主线deadlock_check，返回(local,{})；不在这里序列化诊断路径和过滤器。[诊断与导出](torchair_diagnostic_export_config_objects_and_paths.md)保留完整本地类型/路径行为。

主线AclConcreteGraph.normalize_config没有调用根CompilerConfig.as_dict，而是分别调用debug、dump、experimental，按debug local→dump global→实验local→dump local→debug global→实验global顺序合并。run_eagerly为1时另加sym_input_index；frozen_parameter触发按Torch版本措辞不同的地址不变警告；最后把全部值统一str化。因此原列表、None、字典在此前被接收，并不代表它们以原Python类型送入运行层。

主线GeConcreteGraph._normalize_ge_option则从根as_dict开始，追加/覆盖固定global静态内存策略与high_precision、局部输出复用、确定性、atomicCleanPolicy、动态gear、frozenInput、空Tensor与真实shape选项。其动态gear调用直接读取inference_config.dynamic_gears_merge_policy.value。构造阶段取得global后即调用initialize_graph_engine；全局选项复用与会话限制见[GE会话选项](torchair_ge_session_global_options_and_lifetime.md)。上述后续转换不属于单个配置文件的默认表。

## 版本和覆盖边界

两版AOE/fusion/inference模块完整AST一致；其余局部定义的差异包括前述tiling归属、主线multistream字段与deadlock字段。完整本地配置审阅不代表所有下游GE/ACL扩展、外部Callable、AOE文件格式或任意组合已验证。模型验收应对照mode、原配置、local/global结果和首次真实编译路径，分别记录生效、数值及性能。

## 配置实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/aoe_config.py)（primary）：1–22。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/aoe_config.py)（implementation）：1–22。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/fusion_config.py)（implementation）：1–21。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/fusion_config.py)（implementation）：1–21。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/inference_config.py)（implementation）：1–18。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/inference_config.py)（implementation）：1–19。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/ge_config.py)（implementation）：1–45。
- [固定实现 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/ge_config.py)（implementation）：1–44。
- [固定实现 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/experimental_config.py)（implementation）：1–117。
- [固定实现 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/experimental_config.py)（implementation）：1–111。
- [固定实现 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py)（implementation）：1–120。
- [固定实现 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py)（implementation）：1–118。
- [固定实现 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：374–412。
- [固定实现 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：1137–1164, 1974–2031。
- [固定实现 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：1129–1164。
