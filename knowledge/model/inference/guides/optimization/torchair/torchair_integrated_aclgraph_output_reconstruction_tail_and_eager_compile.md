---
type: Guide
title: 集成AclGraph输出重建尾部与run_eagerly_compile
description: 记录集成acl_graph.py的construct_outputs_based_on_ref存活引用快路径、set_to_original_state跨key陈旧复位、set_reconstructed_outputs_deleter共享存储与deleter注册、reconstruct_inputs，以及run_eagerly_compile的sym值门控静态kernel编译。
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

# 集成AclGraph输出重建尾部与run_eagerly_compile

本卡闭合集成`python/torchair/_acl_concrete_graph/acl_graph.py`（主线1882行/发布1588行）此前未覆盖的尾部组：`construct_outputs_based_on_ref`（1677–1713）、`set_to_original_state_bofore_reconstruct`（1715–1754，源码即此拼写）、`set_reconstructed_outputs_deleter`（1765–1835）、`reconstruct_inputs`（1837–1851）、`run_eagerly_compile`（1853–1882，文件末尾）。上层调度`reconstruct_outputs`四路分发与`_clone_outputs_if_enabled`排除集归[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)，本卡只写它调用的三个尾部helper；WeakRef/`get_tensor_metadata`/`reconstruct_from_tensor_metadata`定义见[utils工具卡](torchair_integrated_aclgraph_reinplace_stream_checker_and_utils.md)；独立包同名重建机制归[npugraph_ex输出重建](npugraph_ex_output_reconstruction_and_storage_lifetime.md)，不跨命名空间互推。只读静态，未执行重建、未触碰真实内存池。

## construct_outputs_based_on_ref：存活引用快路径的三种结局

（1677–1713/发布1421–1456）逐输出取weakref：存活项直接进返回列表，Tensor项同时按`untyped_storage().data_ptr()`登记`alive_outputs`；死引用按metadata重建并按同一data_ptr分组。随后对每个重建组：该ptr在`alive_outputs`**无**对应存活tensor时整个方法返回None（调用方退回完整重建+deleter路线）；有对应则对组内每个tensor `set_(alive_outputs[ptr]的storage, offset, shape, stride)`——把重建tensor重新挂回存活存储（如`return x, x.view(-1), x[0]`的共享存储输出恢复同一别名关系）。全组可挂接时返回"存活+重建"混合列表且不设deleter。两个分组字典都以存储data_ptr为键：共享存储的不同输出tensor在重建组里必然同组，但在alive侧只有首个存活Tensor被登记（dict覆盖语义），同存储多存活tensor取其一。两pin仅`.keys()`显式化差异。

## set_to_original_state_bofore_reconstruct：跨key存活输出的陈旧复位

（1715–1754/发布1458–1494）遍历**全部**graphs_meta（不只当前key）：存活（非None、Tensor、device匹配）且storage._cdata已在`stale_storages_ptr`、且输出下标**不在**该meta的`captured_output_idx_ref_with_userinput`（别名输入输出保护集）中的输出，收进`other_graph_stale_storages`；非空才调`_npu_setCheckpointPoolState(device, _original_mem_state, other_graph_stale_storages, [])`——把其他key仍被用户持有的输出存储复位为stale，随后`stale_storages_ptr=set()`**整体清空**（不只是已复位项）；空列表时不调、不清。设计注释：输入在replay后即释放、无存活输入，输出才可能被用户持有。`_original_mem_state`是compile时保存的池快照（[捕获准备](torchair_integrated_aclgraph_capture_body_and_recapture_prep.md)）。两pin仅迭代风格差异。

## set_reconstructed_outputs_deleter：deleter注册与共享存储归一

（1765–1835/发布1496–1550）对未开输出克隆路线的重建输出做四步：1) 收集`storage._cdata`不在`userinput_ref_with_output_storages_ptr`（别名输入输出不注册，与克隆排除同集）的输出，按data_ptr去重分组——每组首个的`_cdata`进注册表，组内其余tensor后续归一；2) `clone_input=='1'`时额外调`reconstruct_inputs(graph_key)`并把每个device匹配的Tensor输入存储`_cdata`追加进注册表（输入重建tensor也不保活，靠deleter回收）；3) `_npu_setCheckpointPoolState(device, mem_state_after_capture, stale_storages=[], 注册表)`——第三参数恒为空列表（注释"Currently we deallocate on instead of allowing stale recordings"），第四参数是deleter注册列表，docstring说明重建tensor的data_ptr只是裸指针、注册后memory_snapshot才能返回正确块状态；4) 同组（len≥2）的重建tensor逐一`set_`到组首tensor的storage，使共享存储的多个Python tensor持有同一storage对象；最后`stale_storages_ptr.update(注册表)`。deleter/allocator的实际回收行为与`mem_state_after_capture`快照的运行时语义未审。两pin仅`.keys()`显式化差异。

## reconstruct_inputs：输入侧的同构重建

（1837–1851/发布1552–1566）对`userinputs_meta`逐项：weakref为None**或**为Tensor（即capture时置None的Tensor输入、已被释放或需要重建）则按metadata重建并`swap_weakref`，注释"replay结束后输入weakref即None、无人保活"；非Tensor存活对象原样返回。两pin此函数AST相同。注意与[process_input](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)的区别：process_input按clone_input分支选metatensor/retained作copy目的端，本函数是deleter注册时的输入重建路径，两者不共享调用。

## run_eagerly_compile：sym值门控的一次性静态kernel编译

（1853–1882/发布1568–1589）`cur_sym_value=tuple(args[idx] for idx in self.sym_input_index)`（发布为tuple([…])，等价）；未见于`compiled_shape`时过门：`checked_sym_value_range is None`（不设范围即全编译），或`checked_sym_index < len(sym_input_index)`且`cur_sym_value[checked_sym_index] in checked_sym_value_range`（只对指定下标的sym值范围编译）。过门则`compiled_shape.add(cur_sym_value)`并调`compile_static_kernel(fx_forward, *args, build_dir=_aclnn_static_shape_kernel_build_dir, super_kernel_optimize=_super_kernel_optimize, **kwargs)`，不过门仅info日志跳过。无返回值；调用点在`__call__`的`run_eagerly=='1'`且`_aclnn_static_shape_kernel=='1'`组合内（字符串消费者表见[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)），与`__init__`条件属性创建是同一门控，方法体本身不兜底——绕过`__call__`直接调用而未开这对配置会AttributeError。`compile_static_kernel`工具链与两路径差异见[静态Kernel消费者](torchair_integrated_and_standalone_static_kernel_consumers.md)。`compiled_shape`按sym值tuple去重，同一组合只编译一次；越界下标（checked_sym_index超len）表现为静默不过门、不编译。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py)（primary）：1676–1882连续实读（1677–1882为任务书段；1575–1675调度段为[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)覆盖段，本卡仅引用不重述）。
- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：1421–1589逐段对照（AST：reconstruct_inputs相同；construct_outputs_based_on_ref/set_to_original_state_bofore_reconstruct/set_reconstructed_outputs_deleter仅.keys()/迭代风格差异；run_eagerly_compile仅GeneratorExp vs ListComp差异，均行为等价）。
- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/utils.py)（implementation）：get_tensor_metadata/reconstruct_from_tensor_metadata/WeakRef语义定位核对（utils卡覆盖段内）。
