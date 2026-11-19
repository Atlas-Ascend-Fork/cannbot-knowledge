---
type: Guide
title: 独立npugraph_ex资源scope：控核、确定性与静态编译门控
description: 连接完整scope入口、Eager get/set、编译标记与threadlocal属性栈，核对目标流恢复、确定性和共享静态编译门控。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/_scope.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/replace_stream_event.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/_lib.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/_scope_attr.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/scope/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/scope/_lib.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/scope/_scope.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/scope/_scope_attr.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/cond_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/limit_cores.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/advanced/limit_cores.md
  role: constraint
created_at: '2026-11-11T02:55:19Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 独立npugraph_ex控核：流目标恢复与静态编译门控

## 固定版本与采用范围

本卡仅绑定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c中npugraph_ex/npugraph_ex独立包的选定调用链。平台及完整配套未知，保持draft、空平台。公开控核参数和各命名空间文档版本条件继续见[控核与确定性](torchair_core_limits_and_determinism.md)。本次完成静态源码审阅，部署验证仍需记录产品、CANN和实际后端。

## 编译标记携带目标流

limit_core_num在编译时返回_CoreLimitScope，核数以属性字符串保存。stream为None时进入普通scope_enter；传入stream时使用_core_limit_scope_enter，把Stream对象与两项核属性放在同一标记调用中。该函数带_is_core_limit_scope_marker元数据，前AOT流事件Pass据此识别。

replace_stream_event_pass记录current_stream调用当时的符号流。若显式stream解析到图入口流，标记写入完整DEFAULT_STREAM_ID_MARKER、DEFAULT_DEVICE_INDEX_MARKER、DEFAULT_DEVICE_TYPE_MARKER三元组。其余显式流需要取得完整身份，再写入三项_op_stream属性，解析失败会抛RuntimeError。原标记最终改为npugraph_ex.scope_enter.default。

这使“未传stream”和“显式传入图入口current_stream快照”具有不同的后续选择点，嵌套普通流scope时应按来源调用方式核对。

## Pass以三条路径选择运行目标

_insert_core_limit_stream_node按属性选择插入的FX调用。

| 属性 | 所读消费者 |
| --- | --- |
| 三项stream属性均不存在 | 在scope位置插入torch.npu.current_stream，运行时取该处当前流。 |
| 三项均为对应的默认流marker | 复用带is_default_current_stream标记的节点，缺少时在当前GraphModule开头插入current_stream。 |
| 三项均为具体身份 | 用整数stream_id/device_index/device_type构造torch.npu.Stream调用，并在FX节点标记is_core_limit_stream。 |

属性只出现一部分，或具体值混入不一致的默认marker时，helper直接报错。此处以身份构造Python流句柄，实际底层对象的可用性仍须在对应进程和设备核验。

## 混合scope栈保存与恢复同一目标

replace_core_limit_nodes按scope_enter/scope_exit维护一个栈。遇到同时含_op_aicore_num与_op_vectorcore_num的入口，先插入get_stream_limit，再把cube_core_num、vector_core_num提取为FX值，随后插入set_stream_limit应用请求值。栈保存目标流节点及原值节点。

遇到普通流切换等其他scope时压入None，使相应exit仅弹出占位。控核exit则在原scope_exit后插入对保存流的set_stream_limit恢复，并以恢复节点替换该标记。恢复通过图内后继调用表达，运行异常、图断点和未配对标记的处理需按实际路径验证。

后续_build_npu_runtime_funcs为current_stream、带专用元数据的Stream、get_stream_limit和set_stream_limit生成实际Python调用。root和cond分支生成器均调用该映射。用户流scope的with生成及事件闭包继续复用[cond多流闭包](npugraph_ex_cond_stream_event_closure_and_scope_keys.md)。

## 局部分支可以修改整个图的静态编译选择

该Pass只有同时遇到控核scope、且config.static_kernel_compile当前启用时，才调用_is_gte_cann_version("9.0.0", module="CANN")。helper返回False后，将传入config.static_kernel_compile设为False，并在警告中标明触发位置是root还是cond子图。

AclConcreteGraph的局部Pass驱动为root和cond子图传入同一个self.config，并把路径交给控核Pass。因而一个分支触发的赋值会保留在共享配置中，作用延续到后续root和其他分支，不能只按是否实际执行该条件分支判断静态编译选择。

CompilerConfig.as_dict仅在static_kernel_compile仍为真时写出静态编译及辅助组等相关选项。后续normalize_config调用它，代码生成也以这个共享值决定是否合入静态编译扩展配置。应同时保存配置原值、Pass警告中的子图路径及最终序列化选项，定位首次编译路径。

上述9.0.0是这个固定独立Pass传给版本helper的条件。公开接口文档、同仓集成TorchAir和发布快照仍需各自的来源和消费者证据。

## 模型侧验收

固定输入图，分别覆盖无stream、显式图入口流、显式其他流及嵌套普通scope，核对生成代码的目标、get/set顺序与恢复值。cond场景同时核对最终static_kernel_compile配置、首轮产物和实际采用路线。数值、资源占用、异常恢复、重捕获及性能仍需运行验证。本次没有执行上游、图变换、生成代码、捕获或设备测试，没有新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py)（primary）：771–918, 1494–1507。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/__init__.py)（implementation）：17–54, 75–84。
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/_scope.py)（implementation）：34–60。
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/replace_stream_event.py)（implementation）：6–9, 35–42, 132–197。
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：280–313, 469–483, 563–565, 735–765, 1046–1048, 1177–1180, 1363–1387。
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py)（implementation）：39–41, 90–128。

## 完整资源scope与发布局部差异

完整graph_pass两版读取补齐栈与未配对边界。主线只在两项核属性同时存在时识别控核，一项缺失按普通scope占位；读取键值用dict(zip(...))，不在这里完整校验长度/重复键。scope_exit直接pop，未配对标记没有通用恢复。get_or_insert_default_current_stream_node只复用第一个带标记的节点，不另验证target或处于图首；这项前提应与自定义Pass一起核对。

发布7c6c754的控核实现不同：用core_limit_stack和scope_enter_stack，控核入口直接取两值并作用当前流；控核内遇用户流切换时在新当前流读取旧值、应用最近一层请求核数，退出时恢复。普通scope只压占位；控制标记与流切换标记的保留规则各自不同，不套用主线三条显式目标选择。发布读experimental_config.aclgraph._aclnn_static_shape_kernel，主线读static_kernel_compile；两者本地CANN门控都传9.0.0。发布该helper没有主线末尾的lint/recompile调用，不等于外层调用者也不生成代码。

主线replace_stream_event完整定义也已核对：core scope marker只认3实参，当前流快照在原调用位置映射，入口快照和显式流身份分别写marker与_op_stream三属性；不是简单在后续scope位置再查询一次流。未读外部调用者/运行时不因这条映射提升资格。

## 主线确定性scope是另一套图内恢复

主线replace_deterministic_nodes遍历节点快照，普通scope压('other',None,None)，确定性入口按key位置取值并int转换，在标记前插_get_deterministic_level和set_deterministic_level，将原标记替换/删除；相应出口后插恢复旧FX值并替换/删除出口。普通节点取栈中最内层确定性level写deterministic_scope_level，函数并没有对scope外所有旧metadata统一清空。

退出同样假定栈平衡，没有对任意坏属性或异常后半改图做事务回滚；末尾lint/recompile，config形参没有直接驱动该函数内部判断。发布所存graph_pass没有这些本地定义，仅记录文件级差异，不由此否定发布其它模块的确定性能力，也不把局部level转换等同公开参数全域校验或运行确定性证明。

## 完整本地源码证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py)（primary）：1–1631；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py)（implementation）：1–1441；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。

## 完整scope包：Eager和编译入口的返回对象

完整读取独立scope包主线与发布各__init__、_scope、_scope_attr和_lib共8个模块；前文graph_pass及转换器消费者仍保留其原审阅范围。主线__init__已在早期完整覆盖，重读并按本卡新字节重绑，其余文件据完整本地定义提整文件资格；不将被导入的Torch、NPU或其他包实现自动纳入。

主线limit_core_num按torch.compiler.is_compiling区分：Eager返回_EagerLimitCore，进入时才选显式stream或当前流，冻结该目标，读取原cube/vector限制再set请求值；退出始终对保存的同一流恢复，函数体切换当前流不会把恢复改向另一流。__enter__返回self，__exit__无真值返回，不主动吞掉body异常；这不构成进入失败、恢复调用失败或任意并发改流的事务保证。核数保留原输入，本入口没有另加完整正数/产品范围检查。

编译时返回_CoreLimitScope：无显式stream用普通scope_enter，有stream用带语义标记的_core_limit_scope_enter，把对象与核属性放同一FX调用供前文前AOT降低。_core_limit_scope_enter本体虽暂不使用stream参数，仍以allow_in_graph和has_side_effect保留该标记；_is_core_limit_scope_marker属性使不同加载路径产生的Python对象也能被下游识别。它不是在此立刻对目标流完成get/set。

主线deterministic先要求level属于(0,1,2,3)，Eager返回保存原level、应用新level并退出恢复的_EagerDeterministic；编译返回带字符串_op_deterministic_level的普通_Scope。该成员检查不是type(level)is int，实际后续转换与公共参数条件仍须核对。发布所存__init__只定义_Scope及无stream形参的limit_core_num，始终发射两项核字符串标记，没有主线这些本地Eager/确定性分支；不由这4个发布文件推导完整软件栈不支持相应能力。

## need_execute控制真实Host属性栈

_scope注册scope_enter(keys,values,need_execute=False)和scope_exit(need_execute=False)，主线Library命名空间为npugraph_ex FRAGMENT，发布为air FRAGMENT；对应op已存在时不会在此强制覆盖。两op均标side effect，并注册CPU、PrivateUse1、BackendSelect以及Meta。

这些实现只有need_execute为真才调用_scope_attr的scope_enter/exit；Meta同样会按该标志修改Host属性栈，不能将本模块Meta一律写成完全无副作用，也不能把写栈等同已执行NPU控核。默认False不执行该栈操作，图优化何时改成True仍由前文消费者证明。_npu_scope_enter与显式流helper只zip解包attrs、转两列表并调用标记，没有通用长度/空属性防御；_Scope.__enter__/exit返回这些op的结果，不与Eager返回self混成统一对象合同。

## threadlocal属性不是通用配置继承

ScopeAttrs的栈属于threading.local：enter用dict(zip(keys,values))压入，短列表截断、重复key覆盖，不先全面验证；exit仅在已建栈且非空时pop。top只返回最后一层字典，scope_attr_info直接返回原栈对象，不生成不可变快照。has_scope_attr只检查栈非空，不能拿它证明任意key都在最内层。

apply_scope_attr遍历传入ops并应用所有栈层，但当前ScopeAttrs.apply只处理_super_kernel_scope的空字符串：从op.attr安全删除_super_kernel_scope与_super_kernel_options，命中该层后break。它没有在此将所有任意key/value写入op，也没有自行执行控核或确定性API。各算子属性的真实消费者需要另读，不能从函数名补出通用属性继承。

guard_with_user_stream_scope只看top层是否有_user_stream_label；缺少就直接调用原func(self,node)，不会向外层栈搜索同名标签。即使外层有流标签，内层其他属性也不能由本wrapper自动继承为目标流。标签存在时，从进程级_GLOBAL_TAG_TO_STREAM缓存取/建Stream，再在with torch.npu.stream(target_stream)中调用函数并透传结果；threadlocal属性栈与这个全局流表的生命周期不同。

_npu_get_or_create_stream_with_tag在锁内查同tag、缺少时导入torch_npu并新建Stream，保存后复用；没有在此按scope退出清表、更新已存在流的身份或透传优先级。_safe_remove_attr只在key存在时删除并记日志，不重写其他属性。两版此处主要是空白、无插值日志及dict成员判断写法差异，完整读取未执行任何栈操作、导入注册、流创建、控核或确定性改变；平台与verified保持原值。


## 完整scope来源

- [固定scope 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/__init__.py)（implementation）：1–95；完整本地定义，不扩外部实现。
- [固定scope 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/_lib.py)（implementation）：1–3；完整本地定义，不扩外部实现。
- [固定scope 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/_scope.py)（implementation）：1–82；完整本地定义，不扩外部实现。
- [固定scope 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/_scope_attr.py)（implementation）：1–98；完整本地定义，不扩外部实现。
- [固定scope 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/scope/__init__.py)（implementation）：1–19；完整本地定义，不扩外部实现。
- [固定scope 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/scope/_lib.py)（implementation）：1–3；完整本地定义，不扩外部实现。
- [固定scope 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/scope/_scope.py)（implementation）：1–67；完整本地定义，不扩外部实现。
- [固定scope 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/scope/_scope_attr.py)（implementation）：1–95；完整本地定义，不扩外部实现。


## 文档8.5.0与实现9.0.0是两个门槛

两版`docs/zh/npugraph_ex/advanced/limit_cores.md`的使用约束同文：CANN≤8.5.0时静态Kernel与控核同时开启优先保证控核、静态Kernel失效；整页没有给出可共存的版本下限。固定实现却按9.0.0门控：主线与发布的控核Pass都向torch_npu的版本helper传"9.0.0"。因此CANN落在(8.5.0, 9.0.0)时，图中出现控核scope仍会禁用静态编译，不能据文档8.5.0推断该区间可共存；告警文本自身也写明9.0.0起支持同时开启。8.5.0是npugraph_ex文档的运行优先级表述，9.0.0是此固定独立Pass的实现条件；GE与集成TorchAir的门槛另按[控核与确定性](torchair_core_limits_and_determinism.md)核对，版本helper本体在torch_npu仓未审。

## 禁用值沿共享配置传播到真实编译入口

主线`CompilerConfig.as_dict`只在static_kernel_compile仍为真时写出该键及组、符号范围等辅助键；被置False后这些键整体从序列化结果消失。normalize_config消费as_dict返回值，AclConcreteGraph两条构造路线都用它：捕获路线把configs直接传入AclGraph，代码生成路线把configs逐键写进生成init代码的compile_configs，且仅当共享值仍为真才合入extend_config扩展键。

AclGraph以`self.config.get('static_kernel_compile', False)`作实际入口门，键缺失即回落False：`compile`捕获路线据此决定是否在dump上下文中调用compile_static_kernel并传入整个配置dict；force_eager分支据此进入run_eagerly_compile，其中对每个新符号取值再触发compile_static_kernel。一个cond分支触发的False因此同时切断as_dict输出、扩展配置合入与最终编译调用，无需额外标志位。

同一共享值还有两个旁路消费者：cond_structure_summary按`bool(self.config.static_kernel_compile)`在[cond][summary]记录static_kernel=on/off(both_branches)；AclGraph初始化对cond图在super_kernel_optimize开启而static_kernel_compile为False时告警，控核触发的禁用会连带使super_kernel_optimize在该路径失去作用。

## 发布侧入口使用另一组键名

发布npugraph_ex的AclGraph以`_aclnn_static_shape_kernel`为键：force_eager分支与字符串'1'比较，捕获分支truthy判断后在调用点逐项解包缓存键并显式传参，不像主线传整个配置dict。发布控核Pass的禁用告警不标触发子图路径，主线告警标明root或cond子图；两版门控都向版本helper传9.0.0。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/cond_utils.py)（implementation）：590–625，[cond][summary]的static_kernel字段。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：1016–1028, 1059–1082, 1199–1212, 2041–2062。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：805–826, 926–948。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/limit_cores.md)（constraint）：1–79完整读取，≤8.5.0约束在第20行。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/advanced/limit_cores.md)（constraint）：1–79完整读取并与主线raw diff，约束段同文，使用方法段缺stream参数。
- 复核范围（既有来源）：主线graph_pass 771–918, 1494–1507；发布graph_pass 701–800；主线fx2acl_converter 280–340, 463–478, 563–590, 734–768, 935–1121, 1363–1388；主线compiler_config 31–215。
