---
type: Guide
title: torch_npu 自有 pipelining：pipeline() 入口、FX 追踪与边界元数据 warmup
description: 记录主线 torch_npu.distributed.pipelining.pipeline 的 mode=fx 路径：原子单元叶子、SplitPoint 注入、warmup 元数据广播、Pipe 组装与 None 占位符修剪；发布版本 无此实现。
tags:
- task.implementation
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/pipelining/_pipelining_fx.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/pipelining/_pipelining_patch.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/pipelining/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/distributed/pipelining/test_fx_tracer.py
  role: implementation
created_at: '2026-11-12T12:09:20Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# torch_npu 自有 pipelining：pipeline() 入口、FX 追踪与边界元数据 warmup

## 固定版本与适用范围

本卡依据 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `torch_npu/distributed/pipelining/` 三文件（`_pipelining_fx.py` 533 行、`_pipelining_patch.py` 355 行、`__init__.py` 5 行 re-export）全文逐行阅读。发布版本 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 没有 `torch_npu/distributed/pipelining/` 实现目录（pin 根全树 find，含 torchnpugen/ 与 test/），`_pipelining_fx|_FXPipeliningTracer|populate_boundary_metadata|inject_pipeline_splits` 全树 rg 零命中；发布 `test/distributed/pipelining/` 目录存在，但其 `test_pipe.py:6` 导入的是上游 `torch.distributed.pipelining`，不是本实现。两版不可互推。

上游 `torch.distributed.pipelining` 的 `Pipe`/`PipelineStage`/schedule 本体、`torch_mlir` 无关链路不在本卡核对范围。文档层的流水并行支持清单见[DDP/FSDP 适配卡](torch_npu_ddp_fsdp_adaptation.md)，Megatron 式 1F1B 调度 patch 是另一层，见[异构并行卡](../concepts/parallelism/hetero_parallel.md)；两者都不因本卡反向背书。静态阅读口径：未初始化任何进程组、未运行 pipeline/warmup、无设备实验，保持 draft 与空 platforms。

## pipeline() 入口的实际门槛 → 动作

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| 首次调用（`_ORIGINAL_PIPELINE is None or _IR_MODULE is None`） | `_init_pipelining_backend()`：`importlib.import_module("torch.distributed.pipelining._IR")`；成功且 `_IR.pipeline` 存在时，先装 `_modify_graph_op_device` 静默替换补丁，再记录原 pipeline 与 `_IR` 模块 | `_IR` 导入失败（ImportError）或无 `pipeline` 属性时静默返回；随后入口抛 `RuntimeError: torch.distributed.pipelining.pipeline is unavailable`。静默返回不区分具体缺失原因 |
| `split_spec` 与 `split_policy` 同时给出 | 直接 `ValueError: Cannot specify both ...` | 互斥是入口级检查，与 mode 无关 |
| `mode` 为 None 或 `"export"`，且 `atomic_units is not None` | `ValueError: atomic_units is only supported when mode='fx'.` | export 路径不接受原子单元 |
| `mode` 为 None 或 `"export"`（无 atomic_units） | 委托 `_ORIGINAL_PIPELINE`（上游 export 追踪路径） | 上游 export 行为不在本卡范围，本卡不描述 |
| `mode` 不是 None/"export"/"fx" | `ValueError: mode must be one of None, 'export', or 'fx'.` | 大小写敏感的精确匹配，无 strip |
| `mode == "fx"` | 走 `_pipeline_fx`（下节） | `pipeline` 函数带 `_torch_npu_pipelining_patch_applied` 标记属性（`_pipelining_patch.py:337`），`__init__.py` 把 `pipeline.__module__` 改写为本包名 |

## mode="fx"：追踪、warmup 与 split 注入

`_pipeline_fx` 的顺序是：`symbolic_trace_for_pipelining` → `populate_boundary_metadata` → 挂 `RealPyTreeInfo` → 可选 `inject_pipeline_splits` → `_from_fx_traced` 组装 Pipe。

FX 追踪策略（`_pipelining_fx.py`）：`_validate_atomic_units` 先校验每个原子单元名存在于 `named_modules()`，缺失即 `ValueError` 列出全部缺失名。`_concrete_args_from_examples` 用 `inspect.signature.bind_partial` 把已绑定的位置/关键字实参中**不含 Tensor** 的固化为 concrete_args——含 Tensor 判定用递归 `_contains_tensor`（Tensor/tuple/list/dict 值），嵌套容器里含 Tensor 的实参同样不固化；未绑定但有默认值的参数直接拷贝默认值，不做含 Tensor 检查；`*args`/`**kwargs` 跳过；绑定 TypeError 转为 `ValueError`。`_FXPipeliningTracer.is_leaf_module` 的判定顺序：带 `_torch_npu_pipelining_atomic_unit` 标记的模块是叶子；`nn.Sequential` 强制**非**叶子（继续下钻）；`torch.nn`/`torch.ao.nn` 前缀模块是叶子；其余走上游默认。标记在 `try/finally` 中以 delattr 清除——若用户模块本就带同名属性，结束后是被删除而非恢复原值。追踪后拷贝原模块的 `config`/`device` 属性并记录 `class_for_deserialization`。

边界元数据 warmup（`populate_boundary_metadata`，默认 `sync_per_node=True`、`clear_existing_meta=True`、`use_no_grad=True`）：

- warmup 设备按 `LOCAL_RANK`（缺省 "0"）选择：NPU 可用→`npu:{local_rank % device_count}` 并 `set_device`；否则 CUDA 同式；否则 CPU。
- warmup 成员判定 `_find_tp_group_ranks_from_model`：扫描首个 DTensor 参数/buffer，取其 mesh 的 group（`get_group()` 抛 TypeError 时回退 `get_group(0)`）返回该组的**全部全局 rank**；`should_run_warmup = 0 in tp_group_ranks`（:310）是「全局 rank 0 是否落在这个组」的成员判定——组内含全局 0 的**所有**进程都执行真实 warmup，首个 DTensor 所属组不含全局 0 的进程跳过。无 DTensor 或导入失败时返回 `[0]`，此时每个 rank 上 `0 in [0]` 恒真，全体进程都会 warmup。该判定只看首个 DTensor 的组，不遍历其余组，也不预设任何拓扑。
- `_module_has_meta_tensors` 命中**任一** meta 参数/buffer，即对整个模块 `to_empty(device, recurse=True)` 物化，随后遍历**全部** parameters/buffers：浮点/复数参数 `normal_(0, 0.02)`、其余参数与全部 buffer 置零——重初始化面是全模块而非仅原 meta 成员，混合 meta/real 模块的已实化权重同样被重置，源码未提供恢复路径。warmup 权重是随机填充，只服务元数据提取，不代表任何收敛或数值行为。example 输入经 `_move_to_device` 移到 warmup 设备，但已不含 meta 的模块在此路径**没有**自动 `module.to(device)`，不能承诺模块参数与输入设备总是对齐。
- example 输入移到 warmup 设备后，先按签名 seed placeholder 的 `meta['val']`，再在 `torch.no_grad()`（`use_no_grad=True` 时）下用 `_MetadataInterpreter`（fx.Interpreter）真实跑一遍前向，逐节点把结果经 `_tree_to_meta` 转成保 size/stride/dtype/requires_grad 的 meta tensor；`empty_strided` 失败时告警**一次**（模块级 flag）并退化为 contiguous meta。这一步会真实执行模型前向，副作用（如 dropout 之外的 RNG、缓冲区写入）未在本卡逐项核对。
- 同步协议：:307 的 rank 取自 `dist.get_rank()`（默认组全局 rank）。`sync_per_node=True` 且 dist 已初始化时先 `barrier()`（不带 group 参数，作用于全局默认进程组）；随后**全局 rank 0**（:337）把全图 `node.meta['val']` 打包成 dict 协议（`__kind__` = tensor/tuple/list/dict/scalar，dtype 存字符串）并 `broadcast_object_list(obj_list, src=0)`（:340-343，同样不带 group 参数，全局默认组、src=0 为全局 rank 0）回放，`_apply_packed_meta` 按节点名对齐写回。参数名 `sync_per_node` 不改变作用域——这不是按节点或按 TP 组的同步；`sync_per_node=False` 时不做任何 collective，只有全局 rank 0 打包。dtype 字符串非 `torch.*` 可解析类型时 `_dtype_from_str` 抛 `KeyError`。
- `RealPyTreeInfo(in_spec, out_spec)`（tree_flatten 自 example args 与 warmup meta 输出）挂到 `traced.graph._codegen.pytree_info`，其 `_replace` 用 dataclasses.replace 模拟 namedtuple 风格。

split 注入（`inject_pipeline_splits`）：`split_spec` 的目标按 FX `call_module` 节点名**等于或前缀 `目标.`** 匹配；零匹配抛 `ValueError`。`SplitPoint.BEGINNING` 在首个匹配节点前、`END` 在末个匹配节点后插入 `pipe_split` 调用（op 取 `_IR.aten_pipe_split_alias`）；其它 split point 抛 `ValueError: Unsupported split point`。最后 `graph.lint()` + `recompile()`。同一名下多个匹配节点时 BEGINNING/END 分别取首/末个，中间节点不拆分。

## Pipe 组装与 None 占位符修剪

`_from_fx_traced` 用 `_FXExportedProgramShim`（`constants={}`，`module()` 返回 traced GraphModule）顶替 ExportedProgram，并在 `_preserve_fx_call_modules_for_from_traced` 上下文里临时替换 `_IR.split_module`（捕获 子图id→子模块 映射）与 `_IR._outline_submodules`（split 后仍含 `call_module` 的子图复用原 FX 子模块，否则走原实现），finally 恢复原件。`Pipe._from_traced` 以 `MultiUseParameterConfig.REPLICATE`、`output_loss_value_spec=None`、传入的 `split_policy` 调用；其内部行为属于上游，不在本卡范围。

`_prune_none_root_placeholders` 只作用于有 `get_stage_module`/`num_stages`/`split_gm` 的 pipe：每个 stage 图中 `meta['val']` 为 Python `None` 的 placeholder 被 `replace_all_uses_with(None)` 后删除，并同步从 `split_gm` 根 `call_module` 的 args 里裁掉对应下标。两处保守跳过都发 `RuntimeWarning` 且不修改该 stage：找不到调用该 stage 模块的根节点，或待删下标超出根节点 args 长度——为了避免图不一致，而不是静默失败。裁剪后逐 stage `lint()+recompile()`，根图变更后同样处理。

`_quiet_modify_graph_op_device`（初始化时替换 `_IR._modify_graph_op_device`，带 `_torch_npu_modify_graph_device_patch_applied` 标记，原函数缺失或已打过标则不装）：递归更新 `call_function` 节点的 `device` kwarg 与嵌套 `GraphModule`/`submod.graph_module`，只有实际改动过才 `recompile()`；该替换无显式抛错分支、也不返回状态，调用方无法通过返回值判断是否改过——底层 FX 调用（`get_submodule`/`update_kwarg`/`recompile`）的异常未被捕获，不能保证不抛。

## 验证与边界

`test/distributed/pipelining/test_fx_tracer.py`（定向行段）佐证 API 面：`pipeline` 不是上游 `torch.distributed.pipelining.pipeline`、带 `_torch_npu_pipelining_patch_applied` 标记、`mode`/`atomic_units` 在签名中、`__module__ == "torch_npu.distributed.pipelining"`（:85-93），并以 `mb_args=(x_mb, None)` + `atomic_units=["block0","block1"]` 的 None 输入场景（:210-218）对应上述修剪路径。测试文件是静态引用证据，本卡未运行它。

验证方式：在真实多卡环境按 stage 数与 rank 对齐核对 split_spec 命中、stage 边界张量形状/stride 与 broadcast 后的 meta 一致性，再核对 `build_stage` 产物；`dist` 未初始化时 rank 取 0、跳过 barrier/broadcast，打包与回放都在本进程内完成。本卡不承诺任何整模型流水并行的性能或数值结论；`SplitPoint` 之外的切分粒度、动态控制流模块的追踪结果未核对。

## Evidence

- [固定源码 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/pipelining/_pipelining_fx.py)（primary）：1–533 行全文逐行。
- [固定源码 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/pipelining/_pipelining_patch.py)（primary）：1–355 行全文逐行。
- [固定源码 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/pipelining/__init__.py)（primary）：1–5 行全文。
- [固定源码 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/distributed/pipelining/test_fx_tracer.py)（implementation）：1–30, 85–100, 185–225 行段；仅 API 面与 None 输入场景佐证，不作为运行证据。
