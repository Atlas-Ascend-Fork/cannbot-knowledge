---
type: Guide
title: 集成TorchAir graph_pass：原地化与控核Pass的装配、门槛与两版差异
description: 记录集成路径fx2acl转换器对graph_pass各Pass的实际装配顺序与开关门槛、多输入原地化注册表、控核scope改写与静态Kernel冲突门，并区分主线与发布快照及独立npugraph_ex实现。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/graph_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
created_at: '2026-11-12T21:16:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成TorchAir graph_pass：原地化与控核Pass的装配、门槛与两版差异

本卡绑定集成`python/torchair/`两固定pin：主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`与发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`的`_acl_concrete_graph/graph_pass.py`及`fx2acl_converter.py`调用点。只读静态源码，未运行FX改写、FakeTensor传播或流操作；整卡平台未知，保持draft、空平台。事件闭包与record/wait插入侧（主线576–712/发布579–709）由[流事件命名空间](torchair_integrated_stream_event_namespaces_and_cache.md)与[多流依赖](graph_multistream_dependencies.md)覆盖，本卡不重述；独立npugraph_ex同源Pass见[独立原地化](npugraph_ex_reinplace_alias_and_stream_checks.md)与[独立控核](npugraph_ex_core_limit_stream_targets_and_static_kernel_gate.md)，本卡只写集成侧事实与两版差异。

## Pass装配顺序与门槛（两版相同）

`AclConcreteGraph.optimize_graph_without_runtime`（主线232–337/发布221–304，两版逐门相同）按下序执行，每步后经observer落`graph_after_*` dump：

| 步骤 | 实际门槛 | 动作 |
| --- | --- | --- |
| 内存池防复用 | `aclgraph_config.use_custom_pool is not None` | 强制`debug.aclgraph.disable_mempool_reuse_in_same_fx=True`（主线243–250/发布231–238） |
| Cat消除 | `debug.aclgraph.remove_cat_ops`（默认真） | `optimize_cat_with_out_tensor`，细节见[Cat切片](torchair_integrated_aclgraph_cat_out_slices.md) |
| 事件闭包 | 无条件 | `apply_event_closure_with_multi_stream`返回`multi_stream_enabled` |
| 事件record | 无条件 | `apply_event_record`；随后把`_GLOBAL_SCOPE_TAG_TO_EVENT`中新增tag并入`_aclgraph_cache_info.tagged_event_names`（主线277–282/发布260–265） |
| 死代码消除 | 无条件 | `eliminate_dead_code`（“需FakeTensor元数据、无meta注册的Pass应在其后”的注释前提在主线284–286/发布267–269） |
| 中间Tensor原地化 | 非`debug.aclgraph.disable_reinplace_inplaceable_ops_pass` | `_reinplace_inplaceable_ops_pass(gm, multi_stream_enabled, *sample_args)` |
| 输入mutation原地化 | 非`debug.aclgraph.disable_reinplace_input_mutated_ops_pass` | `_reinplace_input_mutated_ops`；`decompose_auto_functionalized`在同一门槛内随后执行（两版均把“LAST”注释写在reinplace_input_mutated分支内，主线300–309/发布280–288） |
| 动态workspace | 无条件 | `replace_dynamic_workspace_ops` |
| 控核改写 | 无条件 | `replace_core_limit_nodes(gm, config)` |
| 默认流标记解析 | 无条件 | `resolve_default_stream_markers`（入口/白名单已由[流事件命名空间](torchair_integrated_stream_event_namespaces_and_cache.md)覆盖，主线1330–1427/发布1358–1447） |

因此`inplace_pass`/`input_inplace_pass`平铺别名（经[配置边界](torchair_compiler_config_boundaries.md)反向映射到上述两个disable开关）在转换器内的实际生效点是这一段；两开关独立，只关一个不会跳过另一个。`multi_stream_enabled`只传入原地化Pass，控核Pass不接收它。

## 多输入原地化注册表与异常文案

两版注册表逐字节相同：`register_inplaceable_npu_op`先`hasattr(torch.ops.npu, inplace_op_name)`再取`.default`，三项注册为`npu_kv_rmsnorm_rope_cache_v2_functional`（改参[5,6]）、`npu_mla_prolog_v3_functional`（[9,10]）、`npu_add_rms_norm_v2_functional`（[0,1]），默认extra_check为多输入流检查（主线134–177/发布126–170）。torch<2.6时`compute_overlapping_tensors`、`ReinplaceCounters`、reinplace内部工具导入失败仅落debug日志，`_HAS_INTERNAL_REINPLACE_TOOL=False`会让原地化Pass告警返回原图（主线52–73/发布51–72）。

门槛→失败边界：`_reinplace_inplaceable_ops_pass`先`add_stream_label_to_node_meta`打流标签再进入try；`NotImplementedError`直接抛出；其它异常在`torch.__version__ < '2.5.0'`时抛RuntimeError，建议文案为`config.debug.aclgraph.disable_reinplace_inplaceable_ops_pass=True`（主线543–548/发布542–547），≥2.5.0仅warning_once返回`original_gm`——`original_gm=gm`是同一对象引用，返回它不是事务回滚，已发生的部分改图不撤销。独立包同名Pass的文案建议`config.inplace_pass=False`（见[独立原地化](npugraph_ex_reinplace_alias_and_stream_checks.md)），两处文案指向各自配置层的不同开关名，不能互推。

`multi_stream_enabled`形参在该函数体内没有用于关闭流检查；实际流检查经`check_multi_stream_for_*`委托`ReinplaceStreamChecker`（utils.py侧）。

## 与独立包同构的算法体和一处主线专属过滤

对主线两文件做去注释/空白归一比较：`_mutated_input_reinplace`（194–515）、`register_inplaceable_npu_op`、`reinplace_with_multi_stream_check`（810–1327）与独立包主线版本0差异行；两个包装函数仅import路径（`torchair._utils` vs `npugraph_ex._utils`）与上述异常文案不同。因此单输入/多输入/auto_functionalized三分支、Storage身份、view_scatter消除、后续使用检查的全部算法事实按[独立原地化](npugraph_ex_reinplace_alias_and_stream_checks.md)消费，本卡不重复。

集成两版之间有一处真实行为差异：主线453行的普通单输入分支带`and (node.op not in ("placeholder", "get_attr"))`过滤，发布464行没有——发布版`to_replace_targets`命中时可对placeholder/get_attr节点尝试`_maybe_get_inplace_op`改写，主线版直接跳过。这与独立包两版的同向差异一致；其余两版差异为排版（含发布把reinplace_with_multi_stream_check内被主线注释掉的调试打印块留成无操作字符串字面量、`type(...) != torch.TensorType`与`isinstance`写法互换、`.keys()`显式化），行为等价。

## 控核scope改写：air命名空间、快照恢复与流切换继承

`replace_core_limit_nodes`（主线716–741/发布710–736）只认`air.scope_enter.default`/`air.scope_exit.default`字符串目标（独立包主线认`npugraph_ex.*`，发布独立包与集成同风格，见[独立控核](npugraph_ex_core_limit_stream_targets_and_static_kernel_gate.md)）。识别与动作：

- 控核scope：键集同时含`_op_aicore_num`与`_op_vectorcore_num`才处理（缺一按普通scope压占位）；在节点前插入`torch.npu.current_stream`→`get_stream_limit`→两个`operator.getitem`（`cube_core_num`/`vector_core_num`快照）→`set_stream_limit(stream, int(aicore), int(vectorcore))`，scope_enter被set节点整体替换并删除；栈记录[流节点,两个快照节点,配置两值]。
- 流切换scope（键集含`_user_stream_label`+`_user_stream_priority`，仅读键名不读值）：仅当已处于某控核scope内才处理——在新流上先应用“最近一层”核数配置、再取新流快照入栈，scope_enter节点保留不删。控核外遇流切换只压"other"占位。
- scope_exit：弹scope_enter栈；"other"直接返回（节点保留）；其余弹出快照栈，在节点后插入`set_stream_limit(cur_stream, 原aicore节点, 原vectorcore节点)`——恢复用的是入栈时捕获的快照节点输出，不是退出时重新读流；仅`core_limit`类exit被恢复节点替换并删除，流切换类exit节点保留。

集成两版此段行为逐门相同（归一比较仅排版差异）。与独立包主线差异：集成版无`gm.graph.lint()`/`recompile()`收尾（独立包主线有），且直接遍历`gm.graph.nodes`而非`list()`快照；这些差别不推断生成代码或外层行为等价性。`torch.npu.get_stream_limit`/`set_stream_limit`的运行语义属torch_npu仓，本卡未审。

## 静态Kernel冲突门：嵌套配置路径与告警文本

任一控核scope出现后`enable_core_limit=True`；此时若`config.experimental_config.aclgraph._aclnn_static_shape_kernel`启用，经`torch_npu.npu.utils._is_gte_cann_version("9.0.0", module="CANN")`判断，低于9.0.0则把该嵌套开关整体设False并warning“only core limit will take effect, static shape kernel will be disabled. CANN 9.0.0 or later supports enabling both features.”（主线730–741/发布721–736）。集成读嵌套路径，独立包主线读平铺`config.static_kernel_compile`（发布独立包亦读嵌套路径，[独立控核](npugraph_ex_core_limit_stream_targets_and_static_kernel_gate.md)已闭合该对比及文档8.5.0/实现9.0.0的门槛差异）；集成告警不标注触发子图位置（独立包主线告警标root/cond路径）。该门只改写传入的共享config对象，不影响本卡上文Pass装配顺序的执行。

## 边界

本卡只覆盖集成graph_pass.py的1–575、716–810、810–1327与fx2acl_converter.py调用点；事件侧（576–712/579–709）、resolve_default_stream_markers（1330–1427/1358–1447）、auto_functionalized分解、cat消除、动态workspace、`replace_stream_event.py`全文分别由所列关联卡覆盖。全部为静态读取；两版归一比较为字节级证据，单行锚点已逐项实读；未执行任何FX图、未创建设备Tensor，运行时流与核数行为未验证。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/graph_pass.py)（primary）：连续实读1–579与710–1427；主题事实取自1–575（可用性门槛、注册表、Storage身份、_mutated_input_reinplace、两个Pass包装）、716–810（replace_core_limit_nodes与两个scope handler）、810–1327（reinplace_with_multi_stream_check）。576–712与1330–1427作为相邻上下文经过，语义归[流事件命名空间](torchair_integrated_stream_event_namespaces_and_cache.md)等关联卡，本卡不为其新增结论。
- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/graph_pass.py)（implementation）：126–190（注册表与Storage身份）、460–472（无placeholder/get_attr过滤的单输入分支）、508–566（replace_dict收尾与包装函数）、700–800（record/wait收尾、控核Pass与handler、reinplace头部）；其余行为一致性由两pin全文去注释/空白归一比较闭合（仅排版差异+453/464过滤差异+调试打印块形态），函数清单经def索引核对两版同构。
- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：232–337（optimize_graph_without_runtime完整Pass装配顺序与门槛）。
- [固定实现来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：221–304（同上发布版装配顺序，逐门对照）。
