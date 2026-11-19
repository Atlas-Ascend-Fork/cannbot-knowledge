---
type: Guide
title: 集成AclGraph捕获主体与重捕获准备
description: 记录集成acl_graph.py的compile_for_graph_key地址簿记与池状态复位、主线独有的_set_stream_limit恢复、capture输入/输出簿记主体、super kernel优化与debug dump，以及get_stale_list_from_weakref/reset_captured_graph生命周期。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-12T14:24:05Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成AclGraph捕获主体与重捕获准备

本卡闭合集成`python/torchair/_acl_concrete_graph/acl_graph.py`（主线1882行/发布1588行）此前未覆盖的捕获组：`get_stale_list_from_weakref`/`reset_captured_graph`（1154–1192）、`compile_for_graph_key`（1207–1317）、`_set_stream_limit`（1318–1335，**主线独有**）、`capture`主体（1358–1462，含1390–1462）。命名空间边界同[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)。compile()的容量/回退触发、`_save_stream_core_limits`方法体行为、`is_need_to_recapture`比对、process_input复制路径归该卡，本卡不重述；`node_info`/`is_capturing`列表交接的共享引用语义归[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)；`UpdatedNodeInfo`字段契约见[动态workspace改写](torchair_integrated_aclgraph_dynamic_workspace_and_shape_construction.md)。只读静态，未执行捕获或回放。

## compile_for_graph_key：地址簿记与池状态复位

（1207–1317/发布1054–1136）每次为新graph_key：先`get_stale_list_from_weakref()`取存活陈旧存储；构造全新`GraphMeta`（新`NPUGraph`、其余字段空，字段定义见[utils工具卡](torchair_integrated_aclgraph_reinplace_stream_checker_and_utils.md)）；`counters["npugraph_ex"]["captured_"+name]=len(_graphs_meta)`。随后四段地址簿记，全部`setdefault`（首捕获定桩）：

- `captured_parameter[idx]=args[idx].data_ptr()`——遍历`_parameter_user_inputs`；
- `captured_mutated_inputs[idx]=data_ptr()`——遍历`_user_inputs_mapping`中`_mutated_user_inputs`命中的项，即[重捕获差异](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)比对的桩；
- 别名输入三联动：`captured_userinput_ref_with_output[idx]=args[idx]`（保活原tensor）、`_userinput_ref_data_ptr[idx]=data_ptr()`、`userinput_ref_with_output_storages_ptr.add(storage._cdata)`（输出克隆排除集的写入点）；
- `captured_output_idx_ref_with_userinput`＝`_userinput_ref_with_output`全部值的扁平set（输出重建时保护别名输出，见[输出重建尾部](torchair_integrated_aclgraph_output_reconstruction_tail_and_eager_compile.md)）。

池复用门（`disable_mempool_reuse_in_same_fx`存在且=='1'才禁用）且已有多于1个key时：`_npu_setCheckpointPoolState(device, _original_mem_state, stale_storages, [])`把池复位到捕获前快照、仅把仍存活的陈旧存储列为stale，再从`stale_storages_ptr`逐一discard。主线随后调`_save_stream_core_limits(graph_key)`（1289，行为见io卡）；发布**无此调用**，直接进入`record_function("acl_graph_capture")`内的capture。捕获后`mem_state_after_capture=_npu_getCheckpointState(device, pool)`；`clone_input=='1'`时`retained_userinputs.clear()`（用户输入不保活，注释说明由重建承担）；池复用且多key时`del captured_outputs`（本key输出不保留），否则`retained_outputs=captured_outputs`。**两pin唯一差异即主线多调_save_stream_core_limits**，其余AST相同。

## _set_stream_limit：主线独有的捕获流限核恢复

（1318–1335）发布整段不存在（全文件rg `set_stream_limit`仅剩CapturedGraphUpdateAndReplay内的更新调用）。逻辑：`self.stream is None`则warning后跳过；否则从`_graphs_meta[graph_key]`读`captured_cube_core_num`/`captured_vector_core_num`（`getattr`缺省None），两者均非None才`torch.npu.set_stream_limit(self._stream, cube, vector)`，异常仅warning吞掉。它在capture入口（1347）先把捕获时保存的限核恢复到捕获流上再进图上下文——与[graph_pass控核改写](torchair_integrated_graph_pass_reinplace_and_core_limit.md)（FX图内按scope插set/get_stream_limit节点）和独立包控核配置（npugraph_ex_core_limit卡）是三个不同层面，互不覆盖；`torch.npu.set_stream_limit`运行语义属torch_npu，未审。主线在线路径load到的`self.stream`可能是[CacheInfo卡](torchair_integrated_aclgraph_cache_info_contract_and_load.md)所述占位字符串而非None，该None门是否命中在线场景未运行验证。

## capture主体：输入三路簿记与输出weakref分型

（1336–1468/发布1137–1247，两pin除主线1347的_set_stream_limit调用外AST相同）进入`torch_npu.npu.graph(graph[key], pool, stream, capture_error_mode)`后，对`_user_inputs_mapping`逐项三路：mutated输入直接continue（不建metatensor，由保活路径承担）；别名输出输入continue；Tensor输入置`WeakRef(None)`并在`clone_input=='1'`且`is_npu`时用`torch.empty_like(…, memory_format=contiguous_format)`换新data_ptr（注释：保证aclgraph记录新指针、输入间不共享，False则记录原指针），再`retained_userinputs.setdefault`保活；非Tensor输入置`WeakRef(原对象)`。随后每项统一写`userinputs_weakref`、`userinputs_meta`（get_tensor_metadata）与`userinputs_metatensor`（reconstruct_from_tensor_metadata）——后两者正是[process_input](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)复制路径的目的端。`_updated_node_infos`先clear再随`fx_forward(*args_list, node_info=…, is_capturing=True, **kwargs)`交给生成代码（共享列表语义归任务更新卡）。

出图上下文后三个后置段：`_super_kernel_optimize`真值门内用`ast.literal_eval`解析`_super_kernel_optimize_options`/`_super_kernel_debug_options`（缺省None）并调`NPUGraph.super_kernel_optimize(optimize_options, debug_options)`；`TORCH_COMPILE_DEBUG==1`环境门内按`{name}_id_{id}_rank_{device}_pid_{pid}_ts_{时间戳}.json`调`graph.debug_dump`（DebugContext目录，异常仅logger.exception不中断）；输出簿记（1449–1455/1231–1238）**Tensor输出置`WeakRef(None)`**（每次运行重建，不保活）、非Tensor输出置`WeakRef(原对象)`（保活），全部outputs_meta由get_tensor_metadata记录。最后组装`replay_func=CapturedGraphUpdateAndReplay(graph, _updated_input_func, _updated_node_infos)`（归任务更新卡）并返回captured_outputs。是否真正成功捕获、句柄/事件可用性是运行时性质，本卡不认证。

## 存活陈旧清单与整实例重置

`get_stale_list_from_weakref`（1154–1166/发布1023–1035）：跨全部graphs_meta收集**仍存活**（weakref非None、是Tensor、device.index匹配）且storage._cdata已在`stale_storages_ptr`中的输出存储——只有这些会在池复位时仍占块，才需要作为stale传给setCheckpointPoolState；已死引用自然跳过。两pin仅`values()`vs`items()`迭代风格差异，行为等价。

`reset_captured_graph`（1168–1192/发布1037–1052）：先`torch.npu.synchronize()`再动作（注释：与捕获前同样先同步）；pop计数器——**主线3项**（captured_、recapture_due_to_mutated_input_change_、recapture_due_to_global_limit_core_change_），**发布2项**（无global_limit项，与其整体缺失限核重捕获机制一致）；逐`graph_meta.acl_graph.reset()`、`_graphs_meta={}`、`gc.collect()`、`torch.npu.empty_cache()`；前后用`LazyMessage(debug_mem_state)`记录内存态（九处消费者见utils卡）。触发条件（static_capture_size_limit命中fallback）归[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)；empty_cache的全局作用与allocator行为未审。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py)（primary）：1153–1350、1351–1468连续实读（其中1194–1205、1288–1299、1351–1357、1387–1389、1463–1468为此前已读段相邻上下文，不为重述；652前forward尾652–653为空行）。
- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：1023–1053、1054–1136、1137–1247逐段对照（AST：compile_for_graph_key唯一差异=缺_save_stream_core_limits调用；capture唯一差异=缺_set_stream_limit调用；get_stale_list仅迭代风格；reset_captured_graph差异=发布少pop一个计数器）。
- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/utils.py)（implementation）：GraphMeta字段与WeakRef/LazyMessage语义定位核对（utils卡覆盖段内）。
