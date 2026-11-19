---
type: Guide
title: 集成AclConcreteGraph的输入解析、簿记与图键材料
description: 记录集成fx2acl转换器AclConcreteGraph的初始化契约、parse_symlist/parse_input/parse_node/parse_output簿记、优化尾段的键材料提取顺序，以及主线与发布在非Tensor占位符记法上的真实差异。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
created_at: '2026-11-12T21:53:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成AclConcreteGraph的输入解析、簿记与图键材料

本卡绑定集成`python/torchair/_acl_concrete_graph/fx2acl_converter.py`两固定pin：主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`与发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。闭合此前未覆盖的类初始化与工具段（主线27–151）、compile委托（216–231）、optimize尾段键材料（338–373）与parse_*族（414–531）；normalize_config（374–412）由[分组配置序列化](torchair_grouped_config_serialization_and_mode_consumers.md)覆盖，序列化与dump插入窗口（346–351）由[FX缓存序列化](torchair_acl_fx_cache_serialization_and_graph_state.md)覆盖，本卡只补其余事实。独立npugraph_ex同名方法的结论见[值包装元数据](torchair_fx_value_pack_metadata.md)，相同方法名不能跨命名空间互推；本卡全部为两pin只读静态比较，未运行解释器、未创建Tensor。

## 初始化契约与两个空上下文

模块头（28–41/28–40）`decompose_auto_functionalized`按torch版本可用性try导入，失败置None仅落debug日志；`_optimize_decompose_auto_functionalized`包`debug_compare_fx_graphs`装饰器。`AclConcreteGraph.__init__`（57–94/57–85）构造即`import torch_npu`，ImportError转RuntimeError且文案引用`config.mode.value`——该类不能在无torch_npu环境实例化。初始状态：`_meta_inputs=[]`、`_fx_input_names=[]`、`_all_sym_input_idx={}`、`_all_meta_tensor_input={}`、`_fx_graph/_fx_forward/_aclgraph_manager=None`、`_tensor_constant_dict={}`、`_serialized_gm=None`，并一次性构造`AclGraphCacheInfo(pool,stream,capture_error_mode,num_warmup_iters,fx_graph_name=name,user_inputs_mapping=OrderedDict(),parameter_user_inputs=[],mutated_user_inputs=...)`——`__init__`签名里的pool/stream等只进cache_info，不在此创建图对象。两pin此段AST相同。

`context()`与`converter_context(*, node)`（136–149/127–140）都是`try: yield finally: pass`的空contextmanager（源码TO DO注释自认无设备上下文）。消费点在npu_fx_compiler：`with self._graph.context():`包住`super().run()`（主线182/发布160），`converter_context(node=n)`在逐节点转换处进入（主线167/发布145）；fx2acl版`converter_context`忽略node形参、不提供任何行为，`_record_asc_ir`的op计数发生在converter的`_wrap`内（主线224–231）而不是这个上下文里。`__call__`（96–111）纯委托`self.graph(*args,**kwargs)`（AclGraph.__call__语义见[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)）；`compile`（217–230/206–219）同样纯委托`self.graph.compile`。`dump`（151–162/142–152）只接受`.py`后缀，否则NotImplementedError并提示检查`config.debug.graph_dump.type`；写文件前经`PathManager.check_path_writeable_and_safety`。

## 优化尾段：键材料的固定产出顺序

`optimize_graph_without_runtime`尾段（338–372/312–341，Pass装配顺序见[集成graph_pass](torchair_integrated_graph_pass_reinplace_and_core_limit.md)）按注释"Must not optimize fx_graph after this"后固定执行：先`get_unupdated_sym_input_index(fx_graph, self._all_sym_input_idx)`写入`cache_info.unupdated_sym_input_index`，再`get_updated_ops_rulers_param(fx_graph, self._meta_inputs)`写入`(ops_update_rulers, updated_ops_param)`（两者实现由[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)闭合）；随后`normalize_config()`→`fx_graph.recompile()`→`SerializableGraphModule(...).convert_to_bytes()`。这两组提取的输入正是parse_input在解释期积累的`_all_sym_input_idx`与`_meta_inputs`——解析期簿记错位会直接进入图键与更新规则。`data_dump_stage=optimized`门内（353–361/326–333）`_super_kernel_optimize=='1'`时告警dump失效，否则`insert_save_npugraph_tensor(self.fx_graph, configs)`（实现见[Reinplace检查与utils](torchair_integrated_aclgraph_reinplace_stream_checker_and_utils.md)）。最后`_codegen_fx_forward`生成前向文本、`AclGraph(fx_graph, config=configs)`构造并`graph.load(cache_info)`。

## parse_symlist：ValuePack展开与int判据

（414–436/379–401）逐项：`ValuePack`取`.npu`；其余必须`isinstance(sym, int)`否则RuntimeError `Unsupported case with non constant value`。注意Python判据下`bool`是int子类，纯布尔列表也会通过；`True`并不能证明对应动态尺寸语义。全部int直接返回；否则仅debug日志后原样返回——非全int不报错。两pin行为等价（`all(生成器)`与`all([列表推导])`形式差异）。消费点：npu_fx_compiler`_unpack_npu`在`_is_symlist`命中时调用（主线195）。

## parse_input：三路簿记与两版真实差异

（438–475/403–434）每次占位符解释执行三步：`_meta_inputs.append(meta_outputs)`；Tensor且带`_dynamo_static_input_type`/`_torchair_is_parameter`属性或本身是`nn.Parameter`时把索引追加进`parameter_user_inputs`，普通Tensor则`user_inputs_mapping.setdefault(target, idx)`（同名占位符只记第一次出现）；`_fx_input_names.append(target)`。随后符号/张量登记：`is_sym`（SymInt/SymFloat/SymBool，acl_graph.py 191定义）时把`meta_outputs.node.expr`映射到索引写入`_all_sym_input_idx`。

两版在非Tensor非sym占位符上分歧：主线（465–474）`elif isinstance(meta_outputs, torch.Tensor)`才写入`_all_meta_tensor_input`，其余（如纯Python int/float/str入参）走else仅记`Skip non-tensor and non-symint placeholder input`debug日志；发布（430–433）没有elif，非sym一律写入`_all_meta_tensor_input`。该字典有三个下游消费者且都按Tensor用法消费：parse_output的`torch._C._is_alias_of(fx_input_meta, arg.meta)`循环、`_codegen_assert_size_stride`的`meta.numel()/shape/stride()`（662–673/614–624，[集成codegen](torchair_integrated_acl_codegen_kernel_first_run_and_runtime_hooks.md)已闭合该生成器）、`_codegen_example_input_run`的`rand_strided(tuple(meta.shape), meta.stride(), device=..., dtype=...)`（904–911）。因此发布版非Tensor条目会进入这三个消费者的输入集合，主线的排除发生在parse_input处；非Tensor条目在这些消费点是否报错属运行时行为，本卡不推断，也不能把两版的输出别名分析或生成代码断言为一致。

## parse_node与parse_output

`parse_node`（477–494/436–453）直接`return target(*args, **kwargs)`——FX解释器语义执行，无本地优化（注释"do some optimization in fx for some ops"自认未做）。`parse_output`（496–530/455–487）要求args是长度恰为1的list/tuple，否则RuntimeError（文案两版有拼写差异：主线"equal to 1"、发布"euqal to 1"）；对唯一集合内每个arg，无`meta`或meta为None直接跳过但仍累加`output_idx`；其余与`_all_meta_tensor_input`逐条`torch._C._is_alias_of`比对，命中则把输出下标追加进`userinput_ref_with_output[fx_input_idx]`。这个字典随后成为[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)所消费的userinput_ref关系来源；比对基于FakeTensor元数据的alias关系，不验证运行时Storage实际重叠。

## 边界

本卡只覆盖集成fx2acl_converter.py的上述行段与npu_fx_compiler四个调用窗口（167/182、195、249–251、310–314）；`_codegen_*`生成器、任务更新规则、normalize_config、序列化、dump配置对象、独立包同名方法分别由所列关联卡覆盖。全部静态读取：未执行FX解释、未构造ValuePack/Tensor，`_is_alias_of`/`rand_strided`/`numel`的运行时行为未验证；`user_inputs_mapping`/`parameter_user_inputs`进入图键后的实际键语义见[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（primary）：27–151、216–231、338–373、414–531连续实读（类初始化、属性、空上下文、dump、compile委托、优化尾段、parse_symlist/parse_input/parse_node/parse_output）；374–412（normalize_config）为[分组配置序列化](torchair_grouped_config_serialization_and_mode_consumers.md)覆盖段的相邻上下文，不为其新增结论。
- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：27–153、206–219、312–342、379–488逐段对照；除parse_input的elif/else结构差异与parse_output错误文案拼写差异外，其余函数AST相同（28–37/57–85/113–132/133–149/151–162/217–230/374–412/477–494归一比较）。
- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：167、182、190–200、224–232、249–251、310–314（四个parse_*调用点、context/converter_context进入点与_record_asc_ir计数位置）。
- [固定实现来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)（implementation）：145、160、171、204、223、286（四个parse_*调用点与context/converter_context进入点索引核对）及158–170窗口实读。
- [固定实现来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：187–193（is_constant/is_sym判据定义），[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)覆盖段内的定向重读。
