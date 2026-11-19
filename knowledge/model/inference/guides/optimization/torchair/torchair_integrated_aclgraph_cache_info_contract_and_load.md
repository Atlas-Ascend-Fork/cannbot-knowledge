---
type: Guide
title: 集成AclGraph构造契约与CacheInfo载入
description: 记录集成acl_graph.py的AclGraphCacheInfo数据类契约、pool校验与主线stream字符串占位、AclGraph.__init__成员布局、属性组、fx_run_eagerly直通、load字段拷贝与默认池，以及主线无调用点的check_all_sym_updated校验器。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph_cache_utils.py
  role: implementation
created_at: '2026-11-12T14:24:05Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成AclGraph构造契约与CacheInfo载入

本卡闭合集成`python/torchair/_acl_concrete_graph/acl_graph.py`（主线1882行/发布1588行）此前未覆盖的构造与载入组：导入段（主线1–15、38–40）、`check_all_sym_updated`（555–597）、`AclGraphCacheInfo`数据类与`__post_init__`（823–858）、`AclGraph.__init__`（861–923，含残留905–923）、属性组与`fx_run_eagerly`（948–999）、`load`（1001–1029，随相邻实读一并闭合）。命名空间边界同[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)：只讨论集成实现，不是独立`npugraph_ex/`同名类；`__call__`/`compile`主体分别归该卡与[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)。全程只读文本/AST比较，未导入、未运行、未建设备对象。

## AclGraphCacheInfo：15字段契约与__post_init__两道校验

（主线823–858/发布731–758）15个字段：`pool`、`stream`、`capture_error_mode`、`num_warmup_iters`、`fx_graph_name`、`user_inputs_mapping`，及缺省None的`parameter_user_inputs`/`unupdated_sym_input_index`/`updated_ops_param`/`ops_update_rulers`/`mutated_user_inputs`，和四个`field(default_factory=…)`项`tagged_event_names`（list）、`user_stream_label`（set，注释"保证cache_compile场景下npu_stream_switch取得正确stream"）、`user_stream_info`（dict，注释值形如`{stream_id, device_index, priority}`）、`userinput_ref_with_output`（输入输出同tensor字典）。转换器写侧（fx2acl主线83构造、`_codegen_init`生成侧）见[parse_inputs与缓存键](torchair_integrated_aclgraph_parse_inputs_and_cache_keys.md)与[生成代码装配](torchair_integrated_acl_codegen_kernel_first_run_and_runtime_hooks.md)。

`__post_init__`两版共有pool校验：pool非None时必须是长度2、两元素均int、且乘积为0的tuple，否则`TypeError: Invalid graph pool handle type`。**主线独有**stream分支：`stream is None`时把`self.stream`置为字面量字符串`"torch.npu.Stream()"`（847），发布无此分支、stream保持None。区分序列化在场与下游消费：

- 在场：占位字符串仅出现在主线本处与其npugraph_ex镜像（全pin rg仅2处定义，0处其他写入）；
- 下游消费：仓内唯一识别到的消费者是fx2acl生成代码的f-string插值`stream={self._aclgraph_cache_info.stream}`（主线582/发布对应段）——占位字符串插出的文本是`stream=torch.npu.Stream()`，即dump重建代码里真实构造一个默认Stream；发布插出`stream=None`。在线路径里转换器默认`stream=None`（fx2acl 62，npu_fx_compiler不传stream），load后该字符串经`self.stream`进入`torch_npu.npu.graph(..., stream=...)`（compile 1072/capture 1356）——torch_npu对该字符串的运行时解析在本pin外，未审；`acl_graph_cache_utils.py`全文无stream处理（rg 0命中）。不能由占位存在推导在线捕获必然新建流，也不能推导字符串安全。

## AclGraph.__init__：构造门、成员布局与条件属性

（主线861–923/发布761–821）三道构造门：`import torch_npu`失败抛RuntimeError（文案引用`config.mode.value`，提示该mode需要`torch_npu.npu.NPUGraph()`）；`fx_forward`与`fx_graph`必须恰好提供一个（两者同None或同非None都触发AssertionError，两版仅f-string包裹差异、文案相同）；`config`缺省为空dict（后续`config.get('run_eagerly','0')`等字符串消费才成立，见[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)的字符串消费者表）。成员分三组：npugraph组（`_device=torch_npu.npu.current_device()`构造时快照、`_graphs_meta`、公开属性`stale_storages_ptr`/`userinput_ref_with_output_storages_ptr`两个set）；capture组（`_fallback_to_eager`/`_captured=False`、更新规则、`_user_inputs_mapping=OrderedDict()`、`_updated_node_infos=[]`等，由AclConcreteGraph经load提供）；run_eagerly×静态kernel组——仅当`run_eagerly=='1'`**且**`_aclnn_static_shape_kernel=='1'`时才用`ast.literal_eval`解析`_aclnn_static_shape_kernel_sym_index`（缺省'0'）、`_aclnn_static_shape_kernel_sym_value_range`（缺省'None'）、`sym_input_index`（缺省'[]'）并生成`compiled_shape`/`sym_input_name`。这些属性是条件创建，方法体不做兜底（见run_eagerly_compile尾部，[输出重建尾部](torchair_integrated_aclgraph_output_reconstruction_tail_and_eager_compile.md)）。

## 属性组、fx_run_eagerly与load

属性组（948–995/847–894）全部为直通只读：`config`/`graphs_meta`/`name`/`pool`/`stream`/`capture_error_mode`/`num_warmup_iters`/`device`/`fx_graph`/`fx_forward`/`fallback_to_eager`；`graph`属性每次按`{graph_key: graph_meta.acl_graph}`即时重建dict（非缓存视图）。`fx_run_eagerly`（997–999/896–898）纯直通`fx_forward(*args, **kwargs)`，注释"无需区分在线与缓存case"。`load`（1001–1029/发布900–926）把cache_info15字段逐一拷到实例；pool为None时`self._mempool = torch.npu.graph_pool_handle()`——未指定池的两次load各拿新池句柄；`self._stream`原样接收（主线在线路径即上一节的占位字符串）；NB注释（1013–1020）声明设计约束：不随意新建捕获流，未显式指定stream时所有图共用默认流，使同池多图的内存块在同一流上组织、池内复用才可能成立——这是注释承诺，运行时是否兑现未验。

## check_all_sym_updated：定义完整、主线无调用点

（555–597/发布488–523）先把`ops_update_rulers`里每个op的全部`("index", idx)`规则项收进`all_updated_index[op_name]`集合；再遍历`graph_module.graph.nodes`的placeholder并逐个递增`data_idx`（**对所有**placeholder计数，位置与meta输入顺序对齐），对`is_sym(node.meta['val'])`且有user的输入：任一user在`all_updated_index`中含该`data_idx`即通过；user不在规则表时按`# TO DO: add check here`直接continue（静默放过），全不命中则RuntimeError指明第几个meta输入是sym、被哪些节点使用、不在哪些更新索引中。**两pin全树（含tests）rg均无调用点**：该函数是定义完整但未接线的校验器，其RuntimeError保护在本pin的主线里实际不生效；"图形sym输入全被更新规则覆盖"不能作为已验证性质引用（`get_updated_ops_fn`薄包装550–552归[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)）。两pin仅`.keys()`显式化差异，行为等价。

## 导入段与两pin杂项差异

主线1–15/发布1–13为纯标准库导入（含`pickle`/`functools`/`deque`，消费者均在此前已读段）；主线首行`# pylint: disable=too-many-lines`发布没有；主线25行`guard_with_user_stream_scope`在本文件仅导入未使用（定义在`torchair/scope/_scope_attr.py:112`，本文件0使用——死导入）；发布27与29行重复导入`reconstruct_args_kwargs`（运行无害的文本差异）。38–40为空行+`@dataclass`装饰行，随相邻实读闭合，无独立结论。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py)（primary）：1–15、38–40、553–599、823–923（824–903为任务书段，905–923为__init__尾随相邻实读闭合）、947–1029连续实读（947–1000为任务书段，1009–1029为load尾随相邻实读闭合；1001–1008归[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)覆盖段）。904、652–653、1469–1470为已读/空行级相邻上下文一并核过。
- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：1–33、483–523、726–899、900–926逐段对照（AST结论：get_updated_ops_fn/fx_run_eagerly AST相同；check_all_sym_updated仅.keys()差异；__init__仅f-string包裹差异；AclGraphCacheInfo唯一实质差异=发布无stream占位分支）。
- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：52–90（cache_info构造与stream=None默认）、577–600（生成代码stream插值消费者）。
- [固定实现来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：生成侧stream插值对应段交叉核对。
- [固定实现来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph_cache_utils.py)（implementation）：全文件rg核对stream/Stream 0命中（负向）。
