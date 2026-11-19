---
type: Guide
title: npugraphs Dynamo backend 接线与旧式 ACLGraph 捕获路径
description: 记录 utils/_graph_tree.py 的 backend 注册、inductor cudagraphify 替换双分支、四类跳过条件与
  CPU 例外通道、旧式静态输入捕获实现，主线惰性接线与发布导入期接线的差异，以及 dynamo "npu"/"npugraph_ex" backend 注册、TorchAir
  惰性 sys.modules 代理与错误重放。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_graph_tree.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_compat/inductor.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/dynamo/test_torchair_lazy.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/dynamo/test_torchair_no_init.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/dynamo/test_npu_backend.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_graph_tree.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py
  role: implementation
created_at: '2026-11-12T05:41:05Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npugraphs Dynamo backend 接线与旧式 ACLGraph 捕获路径

## 固定版本与适用范围

`torch_npu/utils/_graph_tree.py`两版都在：主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`为 410 行、发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`为 381 行，全文逐行读并做完整 raw diff（差异在下文逐条给出）。它一层管接线（注册 backend、替换 inductor 的 cudagraphify）、一层留旧式捕获实现（`triton.cudagraph_trees=False` 时用）。树管理本体（`npu/_graph_tree.py`）与 mark_step 代际状态已由[图下沉](../torchair/torchair_inductor_ascendc_graph_tree.md)与[训练代际](../../../../training/guides/torch_npu_npugraph_training_lifecycle.md)两卡覆盖，本卡只闭合接线与旧式路径。静态阅读：未注册 backend、未捕获图、未运行任何 Dynamo 编译。draft、platforms 为空。

## 接线：注册了什么、何时生效

`_apply_npugraph_tree_methods()` 做四件事：`register_backend(name="npugraphs", ...)`；把`torch._inductor.compile_fx.cudagraphify`替换为本文件`npugraphify`；把`torch._inductor.cudagraph_utils.check_multiple_devices_or_any_cpu_nodes`替换为本文件同名函数；把`torch.compiler.npugraph_mark_step_begin`暴露为本文件包装。触发时机两版不同：

| 项 | 发布 | 主线 |
| --- | --- | --- |
| 触发点 | `torch_npu/__init__.py` 导入期在`_apply_class_patches()`里直接调用（第 187 行） | 惰性：`_lazy_inductor_setup()`（`@run_once`）内调用；触发面不止 npugraphs/mlir 两处——(1)`dynamo._NpugraphsBackendEntryPoint.__call__`（选 npugraphs backend 时：先`_lazy_dynamo_setup`+`register_inductor_npu`再`_lazy_inductor_setup`）；(2)`utils/_dynamo.py`打过补丁的 torch.compile wrapper init 的 mlir 分支（backend 解析为"mlir"时）；(3)同一补丁把`_TorchCompileInductorWrapper.__call__`换成`new_call`，每次 wrapper 调用先经`_compat/inductor.py`的`compat_prepare_inductor_backend_for_call`，其`>=2.15`与`<2.15`两个版本分支末尾都执行`_lazy_inductor_setup`（前者仅在已加载过其他 backend 时先`register_inductor_npu`，后者无条件先`register_inductor_npu`）——凡经该 wrapper 编译（含默认 inductor backend）首次调用即触发；(4)wrapper init 还调`compat_prepare_dvm_backend_on_wrapper_init`，`<2.15`且 backend 为"dvm"时也执行同一 setup |
| 注册对象 | `NpugraphsBackend()`实例直接注册 | 先查`_COMPILER_FNS`防重复，注册`torch_npu.dynamo._npugraphs_backend_entrypoint`（惰性入口对象） |
| get_manager 重定向 | 无 | 把`torch._inductor.cudagraph_trees.get_manager`替换为转发`torch_npu.npu._graph_tree.get_manager`的包装 |
| reset | `NpugraphsBackend.reset`直接调`reset_npugraph_trees()` | 转发入口对象 reset：`sys.modules.get("torch_npu.npu._graph_tree")`已导入才调`reset_npugraph_trees`，未导入则静默不动 |

主线把接线挪到惰性路径，但触发面覆盖所有经补丁 wrapper 的编译：默认 inductor backend 的首次 wrapper 调用经`new_call`的 prepare-for-call 钩子同样执行该 setup，不能用“默认 backend 不触发”推断`cudagraphify`保持上游原状；只有从未构造并调用过打过补丁的`_TorchCompileInductorWrapper`（也未被 npugraphs entrypoint 触发）时，`torch._inductor.compile_fx.cudagraphify` 才保持上游原状——不能从“导入了 torch_npu”直接推出“inductor 的 cudagraphify 已被替换”。发布版则导入即替换。两版都在`npugraphs`编译函数里把 fw/bw/推理编译器挂进`aot_autograd`（`inference_compiler`均为`partial(forward_npugraphs, is_inference=True)`），但发布`forward_npugraphs`在构造图节点时硬编码`is_inference=False`、主线才把该标志传入`npugraphify_impl`：发布推理路径的节点`is_inference`标志与调用方式之间的关系需以实际代码为准，不按形参名推断。

## npugraphify 双分支与缓存

`npugraphify`（替换后的 inductor cudagraphify 入口）按`config.triton.cudagraph_trees`分流：开→`npu/_graph_tree.npugraphify_impl`（树路径，partial 注入 device/stack_traces/占位符/变异索引；主线另传`compile_id=torch._guards.CompileContext.current_compile_id()`与 torch 2.14 传入的`kernel_free_cudagraph`/`user_visible_output_idxs`——注释声明两字段有真实转发语义：`kernel_free_cudagraph`让树管理器对 kernel-free 分区跳过图捕获、`user_visible_output_idxs`opt-in 启用 live outputs 的生成克隆；仅在旧 torch 版本上兼作签名兼容收下）；关→本文件旧式`npugraphify_impl`。首捕获结果缓存方式不同：发布用闭包`nonlocal compiled_fn`（全线程共享），主线用`threading.local()`（线程各自首捕获一次），dynamo_timed+preserve_rng_state 只包首建。

## 旧式捕获实现（cudagraph_trees=False 的实际行为）

1. 对齐与静态化：`get_input_idxs_to_check`/`remove_unaligned_input_idxs`/`copy_misaligned_inputs`（上游 helper，按名引用未展开内部）；非静态 Tensor 用`static_input`重分配、静态索引用`x.detach()`；展开维经`get_expanded_dims`记录并`index_expanded_dims_and_copy_`拷入。
2. warmup：`torch.npu.synchronize()` → 新建旁路`torch.npu.Stream()`并`wait_stream(current)` → 模型跑一遍（若`torch_npu.npu.aclnn._use_static_aclnn_kernel`为真，外面再包一层`StaticKernelCompiler`上下文，见[静态 aclnn kernel](torch_npu_inductor_static_aclnn_kernel_lifecycle.md)）→ `stream.synchronize()` → `current.wait_stream(stream)` → 再次全同步。
3. 捕获：`torch.npu.NPUGraph()` + `torch.npu.graph(graph, stream=stream, capture_error_mode="thread_local")`；捕获内模型收`list(static_inputs)`副本，输出统一 tuple 化。
4. run 双路径：`config.size_asserts`开时逐项断言输入数一致、静态索引`data_ptr`相等、动态项逐槽拷贝，否则用预算的`copy_indices`只拷动态槽；两者都`new_inputs.clear()`后`graph.replay()`返回静态输出。最后经`align_inputs_from_check_idxs(..., mutated_input_idxs=OrderedSet())`包装——旧式路径按“无输入变异”假设对齐，与 npugraphs backend 的跳过检查一致。

## 四类跳过条件与 CPU 例外

`npugraphs`编译器在 fw/bw 都先`check_for_skip`：(1) 输入变异（`check_for_mutation_ignore_cuda_graph_managed_tensor`，`torch._dynamo.config.cudagraph_backend_support_input_mutation`开时跳过该项）；(2) CPU 节点或多设备（见下）；(3) 首个不兼容 cudagraph 节点（`get_first_incompatible_cudagraph_node`）。fw 命中即`BoxedBool.disable`（后续 bw 直接返回 aot 图不捕获）并返回 boxed_nop 解释执行；仅 bw 命中时包一层`fn`：先`manager.set_to_running_backward()`再跑 aot 图——manager 以`create_if_none_exists=False`获取，取不到直接`RuntimeError`（此时若 fw 也已跳过则不会走到这里，因为`not do_npugraphs`提前返回）。设备索引来自`get_device_index`：去掉 CPU 键（受同一 config 门）后取第一个设备，类型非 npu 直接`RuntimeError`。

`check_multiple_devices_or_any_cpu_nodes`的 CPU 键有三个例外通道：`npugraph_trees.disable_cpu_input_check`（两版；该 config 的 setter 行为见[Inductor config 解析](torch_npu_inductor_config_parsing.md)，含真值写回注释与实现相反的坑）；主线额外把`torch.device("meta")`键无条件弹出、并在`is_using_cudagraph_partition()`为真时也弹 CPU。单设备且为 npu 通过；多设备生成`multiple devices: ...`跳过消息。跳过消息经上游`format_default_skip_message`格式化；主线另用 artifact logger（`torch_npu.npugraph`/cudagraphs）把跳过消息打 INFO，并补`NPUGRAPH DFX Fix`系列提示——CPU 节点的`use .to('npu')`（带栈）是 DEBUG 级，多设备的`ensure all tensors on same NPU device`与通用`check skip reason above...`才是 WARNING 级；排障时默认直接可见的是 WARNING 两条，DEBUG 那条需调低日志门槛；发布用普通`logging.getLogger("torch_npu.aclgraph")`且 fw 跳过经`log_cudagraph_skip_and_bump_counter`计数，没有这组提示语。meta 设备与 cudagraph 分区例外是主线新增：不能把“主线容忍 meta 节点”回推发布。

## mark_step 与复位

两版都把`torch.compiler.npugraph_mark_step_begin`指到`mark_step_begin`（主线从`npu/_graph_tree_state`取、发布从`npu/_graph_tree`取——发布把状态内联在同一文件）。该标记的代际语义（显式负数标记优先于 pending backward、不是无副作用提示）见[训练代际](../../../../training/guides/torch_npu_npugraph_training_lifecycle.md)。复位协议差异见表格：主线对“树模块尚未导入”的 reset 静默跳过，发布直接调用并要求模块可导入。

## 边界

- 未实际执行 Dynamo/Inductor：四类跳过条件的覆盖面以上游 helper（`get_first_incompatible_cudagraph_node`等）的当前行为为准，本卡不重审其内部；跳过后的性能差异未测量。
- 旧式实现假设“无输入变异”：这是配合跳过检查的组合事实，单独使用`npugraphify`（不经`npugraphs`编译器）时调用方需自证无变异，源文件未在旧式路径重复检查。
- 主线惰性接线本轮核到的触发面共四处（npugraphs entrypoint、wrapper init 的 mlir 分支、wrapper`new_call`经`_compat/inductor.py`两版本分支的 prepare-for-call 钩子、`<2.15`的 dvm wrapper-init 钩子）；`_compat/inductor.py`本轮只读 491–551 行段，不排除上游版本变化或其他调用方带来新路径，本卡不据此写“永远只有四处”。
- aclgraph 计划（主线）在旧式路径完全不参与：`npugraphify_impl`（本文件）没有计划读取逻辑，npugraphs backend 也不生成计划（[ACLGraph update plan](torch_npu_aclgraph_update_plan_codegen_and_validation.md)的缺失报错把 npugraphs backend 列为显式不支持项）。


## dynamo 'npu' backend 注册与 TorchAir 惰性代理（主线）

`_lazy_dynamo_setup()`（utils/_dynamo.py:624-625 经 `_run_dynamo_setup_step("backends", ...)`）调用 `torch_npu.dynamo._register_backends`（dynamo/__init__.py:231-236），向 Dynamo 注册两个名字：`'npu'`（默认 backend）与 `'npugraph_ex'`。因此 `torch._dynamo.optimize('npu')` 是 torch_npu 注册的入口，不是上游别名。

- **'npu' 的实际构成**（`_get_default_backend` :180-192、`_lazy_exec` :174-177、`_exec` :194-198）：先调 `_install_lazy_torchair()`；失败（本仓不含 torchair 目录）时返回 `_eager_npu_backend` 并按 warning 开关提示 "Register eager implementation for the 'npu' backend of dynamo, as torch_npu was not compiled with torchair."；成功时记 `_global_backend_name='npu'` 并返回 `_lazy_exec`——它经 `npugraph_ex.CompilerConfig(mode=NPUGRAPH_EX_BACKEND)` 取 backend。即有 torchair 时 `backend='npu'` 实际进入 npugraph_ex 编译栈，不构成独立的 eager 优化器；无 torchair 时仅是 eager 等值包装。
- **重注册去重**（`_register_npu_backend` :204-228）：同名且 `__module__` 已是本模块则跳过；setuptools entry point 载入中（`_BACKENDS` 已有 pending EntryPoint 但 `_COMPILER_FNS` 未登记）时留给 `lookup_backend` 以避免双注册；否则先删 `name` 的 `_BACKENDS` 旧条目再注册。entry point 路径另有 `compat_attach_dynamo_backend_init`（torch PR #192345，`>=2.15`）挂 `_dynamo_backend_init` 钩子。
- **sys.modules 惰性代理**（`_LazyBackend`/`_LazyTorchair`/`_LazyNpuGraphEx` :60-172、`_install_lazy_torchair` :133-141）：torchair 目录存在且 `'torchair'` 不在 `sys.modules` 时把 `sys.modules['torchair']` 置为 `_LazyTorchair` 代理；`add_dynamo_methods()`（utils/_dynamo.py:694-706）同理对 `'npugraph_ex'` 置 `_LazyNpuGraphEx`。代理的 `_allowed_list` 仅 `__spec__`/`__path__`：初始化前取任何其他属性抛 `AttributeError`（"Try to get <pkg>'s attr ... before ... is initialized." 追加静态 `[ERROR] ... ERR00005 PTA internal error` 文案——注释说明 pta_error 懒初始化会在 `for m in sys.modules` 遍历中出错，故用静态码）。首次真实 import 失败时把异常包成 `_LazyException` 存 `_exception`，下次属性访问先重放原异常；成功后 `_bind_lazy_submodules` 把已加载子模块同时绑到代理与真实包，且对已初始化代理的 AttributeError 分支重绑后再取。
- **测试侧镜像**（本节来源 7-9，静态阅读、未运行）：test_torchair_no_init.py 断言未初始化时 `torchair._torchair is None`、`torchair._exception is None`、`"torchair.npu_fx_compiler"` 不在 `sys.modules`（注释记录 Python 3.8.1 的 getattr warning registry 触发 bug）；test_torchair_lazy.py 断言 `torchair.get_npu_backend()` 触发真实导入后代理变为真实 `torchair` 且 `torchair.npu_fx_compiler` 已载入；test_npu_backend.py 断言 `torch._dynamo.optimize('npu')(relu)` 与 eager 等值。
- **边界**：本节只闭合主线 `torch_npu/dynamo/__init__.py` 的注册与代理行为；发布 pin 同文件结构不同（模块级直接 `from torch._dynamo import register_backend` 导入并另行组织），代理与 eager 回退语义未按发布树核对，两 pin 不互推。backend 名与提示语不构成稳定 ABI；`_LazyNpuGraphEx` 的 `"npugraph_ex"` 顶层模块名与 `torch_npu.npugraph_ex` 子包是两个入口，也不据代理行为推断任何 npugraph_ex 编译产物语义。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_graph_tree.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_graph_tree.py)（primary）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/__init__.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_compat/inductor.py)（implementation；491–551 行段的 prepare-for-call/dvm 兼容钩子在 pre-freeze 修订中实查）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/dynamo/test_torchair_lazy.py)（primary；测试侧镜像，静态阅读未运行）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/dynamo/test_torchair_no_init.py)（primary；测试侧镜像，静态阅读未运行）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/dynamo/test_npu_backend.py)（primary；测试侧镜像，静态阅读未运行）
