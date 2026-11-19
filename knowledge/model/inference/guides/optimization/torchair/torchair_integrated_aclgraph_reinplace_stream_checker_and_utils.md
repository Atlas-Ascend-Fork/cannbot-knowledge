---
type: Guide
title: 集成AclGraph utils：ReinplaceStreamChecker判据与重建/转储工具
description: 记录集成_acl_concrete_graph/utils.py的ReinplaceStreamChecker三入口判据（仅verify_nodes_on_same_stream、无事件保护）、用户收集范围、WeakRef/GraphMeta/重建工具与insert_save_npugraph_tensor的第二道门，并对照独立包同名检查器。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/utils.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/graph_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-12T21:53:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成AclGraph utils：ReinplaceStreamChecker判据与重建/转储工具

本卡闭合集成`python/torchair/_acl_concrete_graph/utils.py`（主线495行/发布476行）除63–136（TensorMetadata/get_tensor_metadata，[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)已读）外的剩余段。此前集成graph_pass只经`check_multi_stream_for_*`委托点间接引用本文件（见[集成graph_pass](torchair_integrated_graph_pass_reinplace_and_core_limit.md)），检查器实现体本卡首读。独立npugraph_ex同名文件的结论见[独立原地化](npugraph_ex_reinplace_alias_and_stream_checks.md)与[独立包设计合同](npugraph_ex_standalone_design_contracts.md)，同名不互推；本卡全为两pin只读静态比较，未执行FX改写、未创建Tensor/流/事件。

## ReinplaceStreamChecker：三个入口与同一个判据

（主线386–447/发布379–429，两pin AST相同）三个公开入口与graph_pass的三个委托函数一一对应（graph_pass主线87–123：`check_multi_stream_for_single_reinplace`/`_multi_reinplace`/`_auto_functionalize`各自惰性导入本类再调用对应方法）：

| 入口 | 输入下标来源 | 判据 |
| --- | --- | --- |
| `check_single_reinplace(node)` | 固定`[0]` | `_check_reinplace_streams(node, [0])` |
| `check_multi_reinplace(node)` | `inplaceable_npu_ops.get(node.target)`查表，查不到直接`False` | 命中后取`inplace_op.mutated_arg` |
| `check_auto_functionalize(node, mutated_arg)` | `get_inplace_op_mutated_input_users(node, mutated_arg)`（单节点分支） | 直接`_verify_and_log(..., "multi_stream_auto_functionalize")` |

`check_multi_reinplace`查不到注册表项返回False的含义是"不做原地化"，不是"检测到多流"。`_check_reinplace_streams`按输入个数取名`multi_stream_single_reinplace`/`multi_stream_multi_reinplace`，逐输入的用户列表全过`_verify_and_log`才True；任何一路失败立即返回False。

`_verify_and_log`（425–447/415–429）只调用`torchair._utils.graph_utils.verify_nodes_on_same_stream(users)`：少于两个节点直接True；任一节点无`meta['stream_label']`返回False；流标签集合多于一个返回False（graph_utils主线58–88）。三个静态要点：(1)**受检列表只含被改输入的用户，原地节点本身不在列表内**；(2)**没有事件保护分支**——跨流但已被record/wait事件保护的使用不会被该判据放过；(3)失败与成功都只落debug日志并返回布尔，不抛错、不告警。因此集成路径的原地化流门槛是保守的"全部收集用户同流（且各有标签）"。

对照独立包：独立包主线`ReinplaceStreamChecker._verify_and_log`用`verify_cross_stream_event_protected(node, users)`（原地节点参与、跨流依赖有事件保护即可通过，见[独立包设计合同](npugraph_ex_standalone_design_contracts.md)）；独立包发布与集成同为`verify_nodes_on_same_stream(users)`（[独立原地化](npugraph_ex_reinplace_alias_and_stream_checks.md)已记录独立侧）。即集成两pin都不具备独立包主线的事件保护放宽，不能把独立包主线的"事件保护可过"搬到集成路径。

## 用户收集范围：copy_替换与getitem穿透

`get_inplace_op_mutated_input_users`（285–348）与`_collect_single_node_users`（351–383）决定上面"用户"到底是谁：输入节点的直接用户中`aten.copy_.default`被记为copy_node并跳过（copy_将被原地化结果替换）；若copy_node的第二实参是`operator.getitem`（函数化多输出），把该getitem的非copy用户并入；copy_node自身的用户也全部并入。多输入分支先用`meta["fake_result"]`经`torch.utils._pytree.tree_leaves`展开计算总输出数，取尾部`n_inplace`个输出下标建立`input_output_map`，再对每个命中输入额外收集`_get_getitem_users_for_output`（251–282：`getitem(original_node, output_idx)`的非copy用户，可选`min_node_idx`按`meta["node_idx"]`过滤）；pytree展开异常时回退空map，仅保留直接用户。输入下标越界只warning后continue——该输入的用户检查被整体跳过，不是失败。这套收集与独立包同构，但收集结果仅供上面的同流判据消费，不遍历嵌套view或Storage别名。

## WeakRef、LazyMessage与内存快照

`WeakRef`（18–45）：Tensor持weakref（取回时原对象已释放则得到None，源码注释自认），非Tensor对象直接持引用；`swap_weakref`原地换目标。`LazyMessage`（48–60）：延迟到`str()`才调用函数——acl_graph.py多处`LazyMessage(debug_mem_state)`（1175/1191/1275/1283/1307/1748/1762/1810/1834）使`torch.npu.memory_snapshot()`快照只在日志真正格式化时才计算。`debug_mem_state`（191–210）跳过`segment_pool_id==(0,0)`的默认池分段，按device/stream/pool_id汇总block数、active_allocated数与分配量。`timer`（213–217）是info级耗时contextmanager。`is_inputs_base_format`/`is_op_input_base_format`（228–248）：CPU张量直接True；无torch_npu环境info日志后False；NPU格式不在`{NCHW,NHWC,ND,NCDHW}`集合则False（acl_graph.py 1529在process_input的copy判定中消费，该消费段归[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)）。

## GraphMeta与重建工具

`GraphMeta`（84–104）按`graph_key`聚集一张捕获图的全部元数据：`acl_graph`/`replay_func`/`outputs_meta`/`outputs_weakref`/`mem_state_after_capture`及默认工厂字典`userinputs_meta`、`userinputs_metatensor`、`userinputs_weakref`、`captured_parameter`、`captured_mutated_inputs`、`captured_userinput_ref_with_output`、`retained_userinputs`、`captured_output_idx_ref_with_userinput`、`retained_outputs`；其按key存取与`swap_weakref`换锚由acl_graph.py消费（消费行为见[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)）。`reconstruct_from_tensor_metadata`（139–153）：非TensorMetadata输入直接RuntimeError；否则`asdict`后经`torch_npu._C._construct_storage_from_data_pointer(data_ptr, device, nbytes)`与`_construct_NPU_Tensor_From_Storage_And_Metadata`重建——TensorMetadata文档串自认重建张量释放时不做任何事（无deleter），重建即外部存储的别名视图。`reconstruct_tensor_list`/`reconstruct_args_kwargs`（156–188）递归替换Tensor、透传其余。消费：acl_graph.py模块导入（28）与生成代码的`from torchair._acl_concrete_graph.utils import reconstruct_args_kwargs`（fx2acl主线730，[集成codegen](torchair_integrated_acl_codegen_kernel_first_run_and_runtime_hooks.md)）。

## insert_save_npugraph_tensor：第二道门与插入规则

（450–495/431–476，两pin AST相同）入口先查`configs.get('aclgraph.enableDump','0')!='1'`即整图跳过——这是调用方`enable_dump`+`data_dump_stage`配置门（fx2acl 353–361）之外的第二道字典门；键来自dump_config.as_dict的global输出（[诊断导出配置](torchair_diagnostic_export_config_objects_and_paths.md)）。`base_dir`取`aclgraph.dumpPath`缺省`./`。遍历快照节点：跳过output节点、save算子自身、已有save用户的节点、`meta`字典无`tensor_meta`键的节点；其余每个tensor节点后插入`torch.ops.npu.save_npugraph_tensor.default(args=(n,), kwargs={'save_path': os.path.join(base_dir, f'{n.name}.pt')})`，最后`recompile`返回。对照独立包：独立包主线签名为`(gm, data_dump_path)`、调用方负责开关且无内部字典门，独立包发布有同样enableDump门（[独立包设计合同](npugraph_ex_standalone_design_contracts.md)）——集成两pin均带门是集成侧事实。本函数不创建目录、不执行保存，运行落盘行为未验证。

## 边界

本卡只覆盖集成utils.py的1–62、83–106、139–449、450–495（63–136由[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)覆盖）；graph_pass侧三个委托包装、注册表与原地化算法体见[集成graph_pass](torchair_integrated_graph_pass_reinplace_and_core_limit.md)。全文件两pin函数级归一比较：除日志f-string写法、`.keys()`显式化与排版外行为等价（LazyMessage/timer/assert段AST相同）。静态读取，未运行任何检查器或改写；`verify_nodes_on_same_stream`的stream_label由`add_stream_label_to_node_meta`预打（graph_pass卡已覆盖），本卡不重述其打标顺序。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/utils.py)（primary）：1–62、83–106、139–495连续实读（WeakRef/LazyMessage/GraphMeta/重建三函数/debug_mem_state/timer/格式检查/用户收集/ReinplaceStreamChecker/insert_save_npugraph_tensor）；63–136为已覆盖段，仅作相邻上下文。
- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/utils.py)（implementation）：18–476逐函数归一比较（AST相同：18–46/48–60/84–106/139–153/156–166/169–188/191–210/213–217/251–282/285–348/351–383/386–447/450–495；差异仅为get_tensor_metadata/is_op_input_base_format两处logger消息的f-string排版、`.keys()`显式化与空行）。
- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/graph_utils.py)（implementation）：58–88（verify_nodes_on_same_stream完整语义：<2节点True、缺stream_label False、多标签False）。
- [固定实现来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/graph_pass.py)（implementation）：87–123（三个check_multi_stream_for_*委托包装）。
- [固定实现来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：410–472（独立包主线ReinplaceStreamChecker对照：verify_cross_stream_event_protected与mutated_arg描述分支）。
