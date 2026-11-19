---
type: Guide
title: 独立npugraph_ex包的设计说明、Pattern与图元数据合同
description: 保留独立包设计，补完整模式注册、scope标签、事件路径分析与DEBUG结构统计，区分主线和发布实现。
tags:
- task.debugging
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/graph_transform_observer.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/core/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_pass_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/graph_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/graph_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/core/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/inference/_cache_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/dfx.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/dfx.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/data_dump.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/data_dump.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/debug_save.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/debug_save.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/dump_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/npugraphex_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/debug_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/check_platform.py
  role: implementation
created_at: '2026-11-09T17:38:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 独立npugraph_ex包的设计说明与实现差异

## 固定来源和独立包身份

来源为TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c中的npugraph_ex双语设计说明，以及npugraph_ex/npugraph_ex实现。它与同仓python/torchair具有不同导入路径、配置和产物目录；不能只因函数名相同就把所有行为套到发布子模块7c6c754b或任意torch.npu别名。来源没有本设计整体的逐产品矩阵，本卡保持draft、platforms为空。

完整读取8个小模块、1个模块的完整差异和static_kernel/acl_graph的指定局部；没有宣称两份大模块的全部语义完成，也没有导入/执行上游、编译/安装run包、访问设备或创建进程组。设计说明中的代码行号已与实际文件不一致，以下以读到的具体路径和范围限定。

## 配置值的声明与实际校验

force_eager默认False、同FX池复用/clone_input/pattern_fusion_pass默认True、clone_output/static_kernel_compile/disable_static_kernel_compile_cache默认False。设计称这些值“仅bool”，实际OptionValue做候选列表成员相等比较，不是严格type检查；Python内置0/1与False/True比较相等，因此仅凭该setter不能宣称拒绝所有数字。这是静态推断，不表示非bool输入在后续编译/Runtime都可用。

OptionValue.value保留bool，其他非None值转字符串；IntRangeValue用isinstance(v,int)再校验范围，IntListValue接受list/tuple并逐项检查int，StrOptionValue要求str或None。配置字段被接收、序列化形式和下游真正生效是不同层次；按文档传真实bool，不能以一次赋值不报错证明所有组合受支持。

## 七项设计的分层边界

| 功能 | 本设计说明与核对结果 |
| --- | --- |
| force_eager | 保留FX变换、跳过Capture/Replay，不等于原始未优化Eager；设计只列特定组合。静态编译按符号值元组去重，已读run_eagerly_compile先把shape加入集合再调用编译；集合存在不独立证明该次编译成功 |
| Pattern融合 | 同一stream、被消去中间值无额外消费者、extra_check满足shape/dtype/对齐。独立包在用户检查前还拒绝跨deterministic_scope_level/core_limit_scope；普通python/torchair管理器没有相同两项附加检查 |
| 图池与clone | 设计区分显式池、同FX自动复用和user input clone；显式池关闭同FX自动复用，parameter/mutated input不统一clone，输入别名输出不受clone_output独立保存保证。不能据此免除跨流寿命和重放检查 |
| 静态Kernel | 预编译有额外执行/编译/安装与辅助Gloo协调；独立包可指定Gloo参与组，缓存按CANN/设备、算子JSON字节及确定性/SuperKernel选项分层识别 |
| 多流 | 设计以scope与event闭环表达，融合/reinplace不得破坏依赖；tagged event记录执行顺序与record_stream的存储寿命不同。设计的自动闭环不证明任意graph break/外部流访问均安全 |
| 控核 | GE算子级与捕获流级分开。独立包Eager scope真实执行get/set，退出恢复进入时冻结的目标stream；编译路径输出携带stream与核属性的标记节点。无Python范围校验不等于任意核数合法 |
| Debug | 独立实现位于torch_compile_debug/.../npugraph_ex，不是设计正文的torchair目录；compile_fx用compile__N，普通编译用model__N，并区分forward/backward/joint等phase |

设计列出的融合候选约束包括：AddRMSNorm动态量化的view等价flatten(0,1)，cast的末维关系；转置batchmatmul输入FP16/BF16/FP32、末维128对齐、perm与K/B范围、view/expand元数据条件；静态量化输入FP16/BF16一致、尾轴32字节对齐、gamma/scales形状一致及zero_points类型限制。它们是设计文档的候选检查，不能替代当前具体pattern源码/OpPlugin接口/硬件支持；文档INT8(1)/QINT8(12)标码不当作torch.dtype整数值。

## 静态缓存与参与组的实际身份

独立static_kernel.py的_get_cache_path用CANN版本和设备名构造JSON文件名；get_op_hash按JSON原始字节计算摘要，文件空白/字段顺序改变也可能换key。_get_static_kernel_cache_key排序各算子摘要后加入规范化SuperKernel配置、全局deterministic bool与NPU deterministic level；文件名、key、缓存所指run文件存在性仍是不同检查。

_query_static_kernel_cache使用共享锁查询，_update使用排他锁、tmp与replace更新；查询到路径存在不构成数值/ABI验收。模型编译缓存的_load_run_pkg路径另核CANN/确定性/可选level与目录属主，不能把那一处ownership检查说成所有JSON查询入口都相同。

自动Gloo路径按global_rank整块划分本节点，要求LOCAL_WORLD_SIZE为正数、整除world_size，并依赖所有rank一致参与建组顺序；3分钟探测失败返回None并跳过，正式组30分钟。显式static_kernel_compile_group绕过launcher拓扑检查，必须为已初始化、包含当前rank的Gloo group_name；组由调用方持有，框架不在每次编译后销毁。调用方仍需保证节点内成员和全局建组顺序。

文档说编译并行度“默认16”，实际_compute_opc_compile_jobs正常返回os.cpu_count()，未知返回1，异常才退回16。CANN>=9.0路径给op_compiler追加-f true，不能把源码中的fallback数当所有机器固定并行度。

## Debug记录的实际范围

core/utils在导入时按TORCH_COMPILE_DEBUG是否等于"1"决定日志级别；_init_debug_logging创建FileHandler，_set_dynamo_run_dir_name包装get_debug_dir，在分布式已初始化时追加rank后缀。模型/compile计数和文件序号是类级，只有phase放在线程局部，不能据threading.local断言所有计数/路径均为多线程唯一或原子。

GraphTransformObserver调用Pass、保留其返回值供调用者决定，但dump的是持有的gm；不能以Observer返回值推定编译器会自动替换gm。dump_fx_safety先走PathManager检查再写，debug.log另用FileHandler；不能从设计的统一权限表断言所有输出都使用同一显式mode或路径检查。未读取的C++日志及完整路径检查实现不作已审阅声明。

- [捕获与Eager定界](npugraph_ex_capture_controls.md)
- [图池与别名](npugraph_ex_memory_pool_and_clone.md)
- [静态编译的模型侧条件](../../../optimizations/rules/npugraph_ex_static_kernel_compile.md)
- [多流依赖](graph_multistream_dependencies.md)
- [控核与确定性](torchair_core_limits_and_determinism.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/_option_base.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/__init__.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/graph_transform_observer.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/core/utils.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_util.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_pass_manager.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）

## 完整独立包Pattern与图元数据实现

完整审阅固定主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的pattern_pass_manager.py、pattern_util.py及graph_utils.py。以下补完整本地定义与版本差异，前文8个小模块的历史审阅范围保留；不将所有同名TorchAir函数自动视为同一对象，没有导入或执行规则注册、图改写、FakeTensor或事件。

manager以惰性全局单例保存PatternMatcherPass，没有本地互斥。构造通过__init__.__code__.co_varnames判断是否传pass_name；fwd_only导入失败才换inference_graph。register_pattern直接判断torch.__version__ >= "2.7.0"，成立时透传skip_duplicates，否则不传；本地没有强制转str，比较语义由所加载版本对象实现决定。apply_pass只委托上游apply，不在此自动重建GraphModule或认证数值。

stream检查只看match中的call_function：None按默认流，多个非None标签或None与非None混合拒绝；没有这类节点时返回True。一个非None的字面标签恰为'default'仍按非默认值计，不因调试分组的显示名相同变成None。主线再检查deterministic_scope_level和core_limit_scope集合，None与某值也计不同配置；之后才调用用户extra_check。发布这个manager没有后两项检查。局部True不证明底层流、确定性或控核已实际生效，异常也没有统一转成False。

独立pattern_util在torch.__version__ < "2.6"成立时告警并返回，否则按动态量化普通/flatten、Cast、BMM转置、静态量化顺序注册；该条件同样直接比较版本对象，再标注元数据并apply；此处没有普通TorchAir的mode!=max-autotune注册条件。主线调用add_scope_metadata_to_node_meta，发布只调用add_stream_label_to_node_meta；example_inputs/config没有在该函数直接改变注册列表。每条规则各自的lru_cache和条件仍按对应卡核对，共享manager不因一次调用结束而清空。

## scope标签的完整赋值与嵌套边界

legacy stream helper在enter更新当前流后标注enter节点，exit先标当前流再弹栈；主线识别npugraph_ex.scope_enter/exit，发布识别air.scope_enter/exit，不推定两命名空间恒为别名。stream key存在时实际取args[1][0]，并非按key位置查值；需要符合源码所假设的节点结构。

主线综合helper先给节点写进入前的stream/deterministic/core标签，再处理enter/exit，因此enter标注时机与legacy helper不同。它以dict(zip(keys,values))读属性；确定性值int转换，任一核属性出现就把整个core tuple重设为(aic,vector)，未提供的另一项是None，不自动沿用外层该项。每层保存旧状态、exit有栈才恢复，末尾graph.lint；这里没有另写属性长度、重复key、所有scope平衡或任意坏参数的完整验证。

verify_nodes_on_same_stream对少于两个节点直接True；其余要求每个节点显式有stream_label，再比较集合。_is_inplace_node是源码承认的名称后缀启发式（字符串或可取得的overloadpacket名字），不是完整Schema alias分析。_find_mutated_user_inputs还使用外部graph_pass.inplaceable_npu_ops的准确索引，取直接实参Node.name与placeholder.target比较；不遍历所有view、嵌套容器或Storage别名，结果也不承诺去重。该外部表的完整定义不在这6文件中闭合。

## 事件保护检查是图位置分析

主线verify_cross_stream_event_protected要求原地节点已有stream_label；用户缺标签以None比较，没有跨流用户时返回True。它收集全图位置及四个tagged_event_record/wait（含on_stream）target的首个tag和meta流，完全没有record或wait则False。

正向固定点从原地节点位置开始：已知流上的record必须严格晚于该阈值，同tag的wait更新目标流最早阈值，用户位置须严格晚于它。反向从同一位置起，wait须严格早于界限，同tag record把来源流界限扩到record位置+1，用户须严格早于界限。每个跨流用户满足任一方向才True，可以沿tag链传播；这只是所存节点/元数据的可达性判定，不认证tag创建、真实事件语义、全部别名用户、设备完成或异步存储寿命。发布文件没有这个本地函数，不据此否定其他发布模块的事件处理。

## DEBUG计时和结构差异不等于优化验收

debug_time仅DEBUG时用perf_counter包正常函数返回，不同步设备，异常没有finally完成计时。debug_compare_fx_graphs寻找位置参数GraphModule，否则尝试绑定方法的graph对象；前后快照名字、op和pretty target计数，返回原函数结果。缺快照告警跳过比较，其他检查异常没有在这里统一吞掉。

_get_node_info、_merge_diff_list和_tabulate只生成结构统计：总数、集合增删、各op/target前后差，集合键顺序无排序保证，首列左对齐、其余右对齐、缺项补空、最小宽度2。_tabulate任意空data的max没有独立保护，内部merge至少有total行。这些日志既不比较Tensor数据/Storage，也不是设备耗时、数值等价或性能改善证明。

准确post-grad驱动定向证据另见下列npu_fx_compiler范围：主线读取平铺配置、条件图遍历及对应Pass调用，发布读取experimental_config内字段；本卡只绑定所列区间，不升级两份编译器整文件资格。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py)（implementation）：1–182。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py)（implementation）：1–37。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/graph_utils.py)（implementation）：1–540。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py)（implementation）：1–145。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/pattern_util.py)（implementation）：1–35。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/graph_utils.py)（implementation）：1–358。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：320–382。
- [固定实现 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：300–330。


## 设计文档C++传路径承诺与独立包源码的核对

主线 design_principles.md:222（_en.md 同行）承诺 `_init_debug_logging()` 创建 FileHandler“同时通过 `_torchair.SetDebugLogPath()` 将路径传递到 C++ 层”，并称 C++ Logger 析构时把日志追加到同一文件形成双端统一日志。核对主线独立包 `npugraph_ex/npugraph_ex/core/utils.py`（133 行全文复核）：`_init_debug_logging`（29–44 行）只创建 FileHandler 并挂到 logger，整个独立包源码 rg `SetDebugLogPath` 零命中（仅两份设计文档命中）——该传路径调用只存在于集成 python/torchair 副本（其 21–23 行）。静态口径结论：固定主线上独立包未实现文档所述的 C++ 传路径机制；不排除其他版本或路径，也不宣称 C++ 侧完全无法获得日志路径。design_principles.md:223 的 rank 包装句与实现一致（`_set_dynamo_run_dir_name` 加 `_TORCHAIR_RUN_NAME_PATCHED` 幂等标志）。

独立包两 pin 的 core/utils.py 副本呈版本分化：发布副本（77 行全文）为导入期急切初始化——`_debug_log_path = _create_debug_log_paths()`（22 行）加 `file=_debug_log_path`（75 行），没有 `_init_debug_logging`/`_set_dynamo_run_dir_name`，也不调用 `_torchair` 原生绑定；其 debug 目录名仍用 "torchair"（16 行），logger 名为 NPUGRAPH_EX，`_get_logger` 会先清空已有 handlers。主线副本为延迟初始化（模块级 file=None），由编译入口调用：npu_fx_compiler.py 801、977 行与 inference/_cache_compiler.py 668 行调 `_init_debug_logging`，`__init__.py:26` 调 `_set_dynamo_run_dir_name`；主线副本已正确 `import warnings`。不能把任一副本的目录名、初始化时机或 handlers 清空行为写成独立包跨版本通用规则。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/core/utils.py)（implementation）：1–77 完整读取。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/inference/_cache_compiler.py)（implementation）：24、668 单行定位。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/__init__.py)（implementation）：26 单行定位。
- 既有来源 9（主线 `npugraph_ex/npugraph_ex/core/utils.py`）1–133 全文身份与内容复核；既有 primary design_principles.md 复核 218–226 窗口（222/223 行）。
## dfx 文档组的入口页与 data_dump 选项配对

`docs/zh/npugraph_ex/dfx/dfx.md` 两 pin 均为仅一行标题的占位页（字节一致），「DFX功能」聚合实际由三个子页实现：data_dump.md、deadlock_check.md（仅主线 pin 存在）、debug_save.md。deadlock_check 子页与独立包触发链的配对由[死锁工具链](torchair_gegraph_check_deadlock_toolchain.md)修正后承载。本节把 data_dump 子页的参数表与产物承诺同两版配置面逐项配对：

| 文档承诺 | 实现核对（静态读到） | 边界 |
| --- | --- | --- |
| options 三参数 dump_tensor_data / data_dump_stage / data_dump_dir | 主线为 CompilerConfig 平铺字段（compiler_config.py:50–52，data_dump_dir 为 MustExistedPathValue("./")），options 按 hasattr 白名单校验、未知项 ValueError（:183 起）；发布为 dataclass 平铺字段（npugraphex_config.py:25–27）经 `OPTIONS_TO_CONFIG_MAP` 翻译进嵌套 `dump_config.enable_dump / data_dump_stage / dump_path`（:56–58），未知项按 ALLOWED_OPTIONS 拒收（:77/:104–123） | 同名平铺参数两版都接受、都拒未知项，但落点不同：主线直接写 CompilerConfig 属性，发布写嵌套 dump_config 子树；两版 `as_dict` 都只在 dump 开启时输出（主线 141–144 输出 `data_dump_path` 为 worldsize 段拼接后的整路径；发布 dump_config.as_dict 输出 `aclgraph.enableDump='1'` / `aclgraph.dumpPath` / `aclgraph.dumpStage`） |
| data_dump_dir「路径需要确实存在」 | MustExistedPathValue setter 对不存在或非目录路径抛 FileNotFoundError（_option_base.py 主线 150–160/发布 142–152） | worldsize 子目录由实现 makedirs 创建（exist_ok）；存在性要求只针对用户配置的根路径 |
| 目录 `worldsize1_global_rank0`（多卡生成多个） | 主线 `_data_dump_full_path` 69–77 / 发布 `full_path`（dump_config.py:26–36）同构：dist 初始化且 world_size>1 拼 `worldsize{N}_global_rank{R}`，否则硬编码 `worldsize1_global_rank0` | 前缀条件与集成包 fx_dumper 同语义，但这里是独立包自身的配置对象方法 |
| data_dump_stage=original「eager mode 只执行最原始的 fx 图，不会进入 aclgraph 模式」 | 两版都在 `_gen_compiled_gm` 内、aclgraph 生成前直接 `return insert_save_npugraph_tensor(gm, …)`（npu_fx_compiler.py 主线 722–725 传 `config._data_dump_full_path()`；发布 614–618 传 `dump_config.as_dict()` 选项字典） | 实现是在每个 tensor 类型 FX 节点后插 `torch.ops.npu.save_npugraph_tensor`、落盘 `{node.name}.pt`（utils.py 主线 490–527）；output 节点、已插 save 的节点与非 tensor 节点不插——产物「与 fx 图上的节点名称一一对应」只对 tensor 输出成立；发布版插入前再查 `configs.get('aclgraph.enableDump','0')!='1'` 即跳过（utils.py 454–459），是配置写入之外的第二道门，主线无此门 |
| data_dump_stage=optimized（默认） | 在 `_optimize_fx` 后、codegen 前向优化后的 fx_graph 插 save 节点（fx2acl_converter.py 主线 545–551 传 `configs.get('data_dump_path')`；发布 326–333 传整个 configs） | 开启 SuperKernel 时仅告警且不插 save 节点（两版 warning 文案与文档约束句同义：dump_tensor_data 配置失效）；主线文档第 9 行给出该约束，发布页第 9 行改写为产品型号说明——发布文档删去约束但代码仍告警跳过 |
| 场景2 torch_npu.save_npugraph_tensor 单算子 dump | 与场景1共用同一 save op 与 `.pt` 产物形态；`task_breaker_bypass=1` 的 SuperKernel 规避属 torch_npu 侧配置 | save_npugraph_tensor 的接口契约按 TorchNPU 自定义 API 核对，本仓静态源不闭合 |

Eager Dump 联动的版本分野：设计文档「数据 Dump 联动 = force_eager + dump_tensor_data 同时开启」只对应主线实现（npu_fx_compiler.py:695–701，`_NpuFxDumper(gm, config=self.config)`）；发布版同一 eager 回退门改查 `debug.data_dump.enabled`（`type.value is not None`，即 npy 类型已设置，:590–596，`_NpuFxDumper(config=self.config.debug.data_dump)`），而 `OPTIONS_TO_CONFIG_MAP` 没有任何平铺参数映射到 `debug.data_dump`——发布版文档场景1的三个参数不会打开这条 eager Dump 路，需按嵌套配置另行设置，两版同页文档下行为不同。debug_save 子页（TORCH_COMPILE_DEBUG 复用、产物树、compile_fx 不产 dynamo_out_graph.txt、分布式 rank 后缀、CANN≥8.5.0）的行为配对已由[图 Dump 与 Eager 定界](../torch_npu/torchair_graph_dump_and_run_eagerly.md)与[compile_fx](../../../apis/torchair/npugraph_ex_compile_fx.md)承载；本卡只记录该页两 pin 文档差：主线信息表写「原始 *.json 及用于可视化的 *.aligned.json」，发布写「算子执行图信息（*.json 文件）」不提 aligned.json——发布页措辞收窄不构成产物面变化结论，以实现与既有卡为准。

发布独立包配置层（npugraphex_config / debug / dump / experimental / aclgraph 5 个 release-only 文件与 _option_base 两版差异）的完整闭合仍是独立包专项缺口；本节只读与 dfx 配对直接相关的窗口（dump_config 全文、debug_config 类清单与 dump/deadlock 相关窗口、npugraphex_config 映射与 options 处理），不宣称整层已核。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/dfx.md)（constraint）：1 行全文。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/dfx.md)（constraint）：diff 零输出。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/data_dump.md)（constraint）：1–82 全文（约束 9、options 参数表 20–29、目录与命名 34–39、save_npugraph_tensor 场景 42–60）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/data_dump.md)（constraint）：与主线 diff——行 9 约束改产品型号说明、行 46–49 链接措辞收窄、行 18 行尾空白；参数表与产物命名同义。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/debug_save.md)（constraint）：1–82 复核（信息表 17、compile_fx 边界 21–22、目录树 44–59）。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/debug_save.md)（constraint）：与主线 diff——行 17 发布无 aligned.json 措辞、行 21–22 compile_fx 措辞差异。
- [新增来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：窗口 505–560（normalize_config 调用 539、optimized 门 545–551）。
- [新增来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：窗口 320–352（optimized 门 326–333、normalize_config 342–352）。
- [新增来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：`insert_save_npugraph_tensor` 490–527 全函数。
- [新增来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：454–501（enableDump 第二道门、dumpPath 取值、无 return gm）。
- [新增来源 11](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/dump_config.py)（implementation）：1–43 全文（字段 12–22、full_path 26–36、as_dict 38–43）。
- [新增来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/npugraphex_config.py)（implementation）：20–123（字段 25–27、OPTIONS_TO_CONFIG_MAP 35–60、ALLOWED_OPTIONS 77、_process_kwargs_options 104–123）。
- [新增来源 13](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/debug_config.py)（implementation）：17–121（`_DebugBase.enabled/full_path` 17–39、`_DataDump` 55–70、`_DebugConfig` 106–121）。
- [新增来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/_option_base.py)（implementation）：142–152（MustExistedPathValue）。
- 既有来源补读窗口：npugraph_ex configs/compiler_config.py 主线 40–90（dump/deadlock 平铺字段 50–52/58、`_data_dump_full_path` 69–77、`_eager_data_dump_full_path` 80–90）、100–102、135–144、183–210（hasattr 白名单）；npugraph_ex npu_fx_compiler.py 主线 694–726（联动门 695–701、original 门 722–726）、发布 586–618（eager 门 590–596、original 门 614–618）。全部静态读取，未 import/运行上游。
## 独立包 _utils 枢纽与集成的分化

独立包`_utils/__init__.py`（主线477行/发布467行）是独立侧的torch猴子补丁枢纽，与集成`python/torchair/_utils/__init__.py`逐文件`diff -w`后分化集中在`add_npu_patch`与allgather注册三处：

- 主线独立包在注册`aten.to.other`的`AutogradPrivateUse1`替换前先查`if DispatchKey.AutogradPrivateUse1 not in aten.to.other.py_kernels:`，集成侧无此守卫。
- 集成在`compiler_config.experimental_config.npu_fx_pass`为真时追加`npu_patch_fx_pass(decompositions)`，独立包两pin均无此分支——独立包配置树没有这个开关的消费，不能把集成的npu_fx_pass行为推给独立包。
- 独立包注册`torch.ops.npu_define.allgather`分解前先查`if torch.ops.npu_define.allgather not in decomposition_table:`，集成直接注册。patch函数导入源也不同：独立包从`npugraph_ex.ops._hcom_*`取`npu_all_to_all_patch_dist`等，集成从`torchair._ge_concrete_graph.ge_converter.experimental.hcom_allgather`取；`adjust_traceable_collective_remaps`本身两树仅此导入源差异。

另：主线独立包`check_platform.is_arch35`只按设备名查`Ascend910_95`与`Ascend950`，集成主线同函数还含`Ascend350`；两包发布版均只查前两种。独立包主线的SoC门控消费方（graph_pass、grouped_matmul等镜像转换器）在Ascend350设备上不启用对应分支，与集成主线行为不同。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/__init__.py)（implementation）：全文件与集成主线`diff -w`（33行差异）+头部1–30、add_npu_patch区440–477定向阅读。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/__init__.py)（implementation）：全文件与集成发布`diff -w`（29行差异），分化同上三处。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/check_platform.py)（implementation）：1–10完整读取；与集成主线diff为注释与`Ascend350`分支。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/check_platform.py)（implementation）：1–9完整读取；与集成发布`diff`零输出。
