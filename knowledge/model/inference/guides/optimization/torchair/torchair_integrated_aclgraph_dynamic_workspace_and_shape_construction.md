---
type: Guide
title: 集成AclGraph动态workspace改写与符号shape构造
description: 记录集成acl_graph.py的StaticWorkspaceReplaceFunc/UpdatedNodeInfo契约、construct_fx_node_shape四分支与eval+全局表达式缓存、workspace/out节点构造及replace_dynamic_workspace_ops改写边界，并闭合Cat卡遗留的外部shape构造器资格缺口。
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
created_at: '2026-11-12T21:53:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成AclGraph动态workspace改写与符号shape构造

本卡闭合集成`python/torchair/_acl_concrete_graph/acl_graph.py`（主线1882行/发布1588行）此前未覆盖的动态workspace改写组：数据类（主线41–89）、`construct_and_add_workspace`/`construct_fx_node_shape`/`construct_and_add_output`/`replace_dynamic_workspace_ops`（主线652–823）。`_REPLACE_FUNC_MAP`注册表与签名检查（108–186）由[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)覆盖；本卡同时闭合[Cat切片](torchair_integrated_aclgraph_cat_out_slices.md)声明的"外部shape构造器、全局表达式缓存未资格化"缺口。独立包同名改写见[npugraph_ex任务更新捕获](npugraph_ex_task_update_capture_and_streams.md)（该卡明确不回推集成路线）；本卡只写集成侧锚点与两pin差异，全部为只读静态比较，未执行FX改写、eval或算子。

## 两个数据类：注册契约与生成代码的填充对象

`StaticWorkspaceReplaceFunc`（41–62）：`get_workspace`/`out_operator`两个Callable、`workspace_keys`/`output_keys`/`updated_param_keys`三个键列表、可选`updated_param_indices`——正是注册表四项（FIA×2带workspace+out、ATB×2仅updated_param_indices，见任务更新卡表格）的结构。`UpdatedNodeInfo`（63–89）：`node_name`/`updated_func`/`updated_param_name`/`args`/`kwargs`/`handle`/`event`/`core`及可选`updated_param_index`——fx2acl生成代码`from torchair._acl_concrete_graph.acl_graph import UpdatedNodeInfo`后构造的正是这些字段（fx2acl主线731、819，生成文本见[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)）；acl_graph.py 1351注释"Clear _updated_node_infos(list of UpdatedNodeInfo objects) before capture"指向同一对象。字段声明不证明handle/event/core的运行时语义，原生task-group/event实现未审。

## construct_fx_node_shape：四分支与eval+模块级缓存

（684–723/607–644）对输出shape逐维分流：`is_constant`（int/float/bool，187定义）直通；`str(dim.node.expr).isdigit()`时`int(dim.node.expr)`（sym(5)数字符号）；单个`sympy.Symbol`必须在`sym_inputs`中，否则RuntimeError `Unexpected sym output shape`；其余符号表达式（如`32*(s0//32)`）走缓存+eval分支：按`graph_id`（调用方传入`id(graph_module)`）查模块级全局`_GLOBAL_SYM_EXPR_2_NODE_MAP[graph_id][str(dim)]`，未命中时把每个自由符号写进本模块`globals()[str(sym_i)] = Proxy(sym_inputs[sym_i])`后`eval(str(dim))`取`expr_proxy.node`入图并回填缓存。三个静态要点：

1. **缓存无淘汰**：`_GLOBAL_SYM_EXPR_2_NODE_MAP`在整个python/torchair树只有定义（681）与此处写入，没有任何清理路径；条目按`id(graph_module)`键控、进程生命周期保留。GraphModule被GC后CPython可能复用同一id，此时同图id的新图会命中旧图的FX节点——这是Python语义层面的陈旧缓存可能性，本卡未运行复现，不能宣称必然出错，也不能宣称缓存安全。
2. **eval分支假设至少引用一个自由符号**：到达该分支但`free_symbols`为空的维度（如str形式非digit的负常数符号）会让`eval`返回普通Python对象，随后`.node`属性访问不成立。该边界只在异常形态维度出现，是否可由真实模型触发未验证。
3. **globals注入是进程级副作用**：符号名被写进acl_graph模块globals并在后续eval中隐式解析；与缓存条目一样跨图共存。

[Cat切片](torchair_integrated_aclgraph_cat_out_slices.md)的符号shape构造（cat_optimization.py 161/175）调用本函数，其`sym_inputs`来自`_build_sym_inputs_from_placeholders`的标量符号placeholder映射；workspace路径的`sym_inputs`来自`meta_inputs`与占位符顺序对齐（见下节）。两条路径共享同一缓存与globals注入。

两pin差异：发布在表达式分支多一行未使用的`proxy_nodes = {}`（死变量），其余为`.keys()`显式化与排版——行为等价（AST差异仅由死变量与格式引起）。

## workspace与out节点构造

`construct_and_add_workspace`（654–676/580–606）：注册`workspace_keys`为空直接返回None跳过；否则用原节点的args/kwargs调`get_workspace`建FX节点，返回值归一tuple/list后长度必须与注册workspace键数一致，否则RuntimeError `The lengths of the returned workspace nodes ... do not match`；逐键写入`kwargs_dict[workspace_keys[i]]`。`construct_and_add_output`（726–764/646–683）：注册`output_keys`为空返回None；`node.meta['val']`归一tuple/list后个数必须与注册输出数一致，否则RuntimeError；逐输出经construct_fx_node_shape构造shape后`torch.empty(shape, dtype=..., device=...)`建FX节点；单输出`kwargs_dict["out"]=节点`，多输出为列表。两个构造都不验证out重载的运行时适用条件，只对齐注册长度与meta个数。

## replace_dynamic_workspace_ops：准入、改写与无条件lint

（768–821/685–730，`@debug_compare_fx_graphs(pass_name="replace_dynamic_workspace_ops")`装饰）先按图顺序收集placeholder，再把`meta_inputs`中`is_sym`的项按下标对齐到placeholder（`sym_inputs_2_node[meta.node.expr] = input_node[idx]`——依赖[parse_input](torchair_integrated_aclgraph_parse_inputs_and_cache_keys.md)按占位符顺序累积`_meta_inputs`，错位会建立错误的符号→节点映射）。遍历节点仅处理：target在`_REPLACE_FUNC_MAP`中、注册`output_keys`非空、`meta`含`'val'`——ATB两项注册output_keys为空，本函数直接跳过，不为它们建workspace或输出。命中节点在`inserting_before`内：workspace节点（可为None）+ out输出节点 + `out_operator(args=node.args, kwargs=node_kwargs)`调用，然后`replace_all_uses_with(out_run_node)`，循环后统一erase并**无条件`lint()`**——即使全图零替换也会lint（与集成控核Pass无lint/recompile形成对照，见[集成graph_pass](torchair_integrated_graph_pass_reinplace_and_core_limit.md)）；本函数自身不recompile，统一recompile在调用方fx2acl（349）。调用点是fx2acl`optimize_graph_without_runtime`中无条件的"动态workspace"步（主线311–313/发布290–292），即集成Pass装配表中该行的实现体。两pin差异：发布以`output_node =`捕获`construct_and_add_output`返回值而主线丢弃（死赋值），行为等价。

## 边界

本卡只覆盖集成acl_graph.py的41–89、652–823及导入段相邻上下文（1–37，`Proxy`来自`torch.fx`）；注册表、签名检查、`is_arg_param_match_index_by_operator_schema`、`get_unupdated_sym_input_index`/`get_updated_ops_rulers_param`及AclGraph类方法分别由[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)、[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)、[静态Kernel消费者](torchair_integrated_and_standalone_static_kernel_consumers.md)覆盖。eval/Proxy图构造、lint与实际算子行为均未执行；workspace查询与out重载的运行时充足性（对所有变化长度/产品）不在本卡范围。acl_graph.py其余分散缺口（capture主体、compile_for_graph_key、输出重建尾部等）见批次剩余清单，未由本卡闭合。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py)（primary）：41–89、652–823连续实读（两个数据类、construct_and_add_workspace、_GLOBAL_SYM_EXPR_2_NODE_MAP、construct_fx_node_shape、construct_and_add_output、replace_dynamic_workspace_ops）；1–37导入段与108–215（注册表/is_constant/is_sym）为相邻上下文，108–186归[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)覆盖段，不为其新增结论。
- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：34–80、580–730逐函数对照（AST相同：34–80对应41–89、646–683对应726–764；construct_fx_node_shape与replace_dynamic_workspace_ops的AST差异分别为死变量`proxy_nodes={}`与死赋值`output_node=`，另加`.keys()`显式化）。
- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：311–313（replace_dynamic_workspace_ops调用点）。
- [固定实现来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：290–292（发布版replace_dynamic_workspace_ops调用点核对）。
