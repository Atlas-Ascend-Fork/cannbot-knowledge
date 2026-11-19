---
type: Guide
title: torch_npu 主线 npu_compare 精度对拍与 _inductor/profiler.py：三后端对拍链、msprof 导出转换与 mspti 批量测量
description: 记录主线独有的 npu_compare.py（300 行全文）与 _inductor/profiler.py（186 行全文）：compare_outputs/_report_mismatch 的容差与样本诊断、check_accuracy_triton 的 SymInt 标量配方反推与失败快照（不对拍后覆写输出）、MLIR/DVM 两条对拍链；SimpleProfilingAnalyzer 的 msprof.py 导出子进程与 op_summary→kernel_details.csv 表头转换、simple_trace_handler 失败回退、mspti_batch_benchmark 的 LD_PRELOAD 门槛与精确计数校验；附与发布版内联 check_accuracy 的语义差异锚（equal_nan、覆写副作用）。
tags:
- task.implementation
- topic.graph_execution
- task.debugging
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/npu_compare.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/profiler.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py
  role: implementation
created_at: '2026-11-12T13:15:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 npu_compare 精度对拍与 _inductor/profiler.py：三后端对拍链、msprof 导出转换与 mspti 批量测量

## 固定版本与适用范围

两个文件均为**主线 pin（ac0e1564）独有**：发布 pin（f3ecfe4a）全树 rg `npu_compare|SimpleProfilingAnalyzer|mspti_batch_benchmark|simple_trace_handler` 在 Python 面零命中（`mspti` 字样仅命中 `csrc/profiler/mstx_mgr.cpp:243` 的 `libmspti.so` 库名字符串）；发布版对应功能是 npu_triton_heuristics.py 内联的 `check_accuracy`（`:806-860`，[发布版类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)已记）。本卡覆盖：npu_compare.py 300 行全文（头部 `:1-30` 曾由基准类体卡先读）与 profiler.py 186 行全文；后者同时承载[主线基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)声明的未覆盖项「mspti_batch_benchmark 来自 ..profiler，其本体未读」。消费端锚：runtime/triton_heuristics.py `:95` import、`:1887` 调用（调试族窗口，归发布版 autotuner 类体卡的主线对照读窗）、dvm/__init__.py `:15`、ascend_npu_ir meta_compiler.py `:9/:117`、lowering_fx.py `:485`（配方生产端注释）。纯静态阅读：未导入/执行任何上游代码、未运行任何对拍或 profiler；draft、platforms 为空。

## `compare_outputs` 与 `_report_mismatch`（`:24-86`）

- `compare_outputs`（`:24-46`）：非张量对直接跳过；`expected.dtype != actual.dtype` → expected 先 cast 到 actual 的 dtype；容差取 `tolerances.get(actual.dtype, tolerances["default"])`（main 侧实际传入 `npu_config.acc_comp_tol` 或 `anir_config.acc_comp_tol`）；`torch.isclose(actual, expected, rtol, atol, equal_nan=True)`——**发布版内联 check_accuracy 是 `equal_nan=False`**（release `:848`），同为容差对拍但 NaN 语义相反（diff 锚）。不匹配 → `_report_mismatch` 并记 failed_indices；返回"无失败下标"布尔。
- `_report_mismatch`（`:49-86`）：`abs_diff` 先按原 dtype 算、`RuntimeError` 再双双升 fp32；`expected_abs` 非浮点/复数 → 升 fp32；`rel_diff = abs_diff / clamp(expected_abs, min=1e-20)` 且把匹配位置填 0；统计失配总数/占比、最大相对差与绝对差；取前 5 个失配下标、前 3 个 `unravel_index` 回原形状打印 actual/expected 样本值（6 位科学计数）；`print(..., flush=True)` 直出，非 logger。

## `get_triton_fx_graph_call` 与 `check_accuracy_triton`（`:89-222`）

| 步骤 | 动作 | 失败/边界 |
| --- | --- | --- |
| dump 定位（`:89-100`） | `traced_graph_hash` 缺失或 dump 目录/路径不存在 → 返回 `(None,)*4`（调用方直接 return None，**不阻断 kernel 正常执行**）；存在则 `sys.path` 临时插入后 `importlib.import_module(traced_graph_hash)` | dump 的生产端（目录如何写出）不在本卡；hash 必须是合法模块名 |
| `fx_graph_call`（`:108-122`） | 输入按 `non_contiguous_indices['inputs']` contiguous、按 `mismatch_indices_shapes`（仅下标 < num_inputs）reshape；`model.forward` 后把输出 reshape 成 kernel 输出槽形状，非连续输出 `copy_`、其余 `out2.data = out1.data` | `fallback_call`（`:124-126`）按 `call_args_mapping` 重排参数后复用 fx_graph_call（`auto_fallback=True` 时返回它） |
| `check_accuracy_triton`（`:133-222`） | ①先构造 fx 参数：`call_args_mapping` 中 `idx == -1` 的 SymInt 标量用 `scalar_resolved_from[pos] = (kernel_arg_idx, dim)` 配方从 `args[kidx].shape[d]` 反推具体 int（注释原义：配方在 create_compile_kwargs 求解、序列化为具体 int，不依赖 pos==dim 假设）；int 直传；非张量 `torch.tensor(arg).npu()`；bf16 `clone_preserve_strides(arg).float()`，其余 clone。②`fx_graph_call(*fx_args)` 先跑参考，③`launcher(*args, stream=stream)` 后跑被测 kernel。④`compare_outputs`（实际输出取 args 输出槽，期望取 fx_args[num_inputs:]） | **与发布版内联版的核心语义差**（diff 锚）：发布版不匹配时用 fx 结果**覆写实际输出**（`actual.copy_(expected)`，发布版卡读窗 `:850-856`）；主线 `check_accuracy_triton` 只报告/落盘、**不覆写**——调用方拿到的是 kernel 自身输出。顺带：批内 fx→launcher 的执行次序与发布版一致（先 fx 后 launcher） |
| 失败留证（`:193-218`） | 不匹配且有 dump_path → 输入快照（cpu 副本）存 `dump_path/data_fail_{invocation}.pth`（`_call_counter` 按 kernel 名计调用次数）；带配方时打区分诊断：反推值出现在 kernel int 实参里 → "Likely a real kernel bug"，不在 → "Likely a tool artifact (scalar resolution mismatch)" | 诊断措辞为源码原义，不构成定位结论承诺 |

生产端对位：`lowering_fx.py:485` 注释"运行期从输出 tensor shape 反推其值（见 npu_compare.check_accuracy_triton）"即上述 `scalar_resolved_from` 配方的序列化来源（该文件本体不在本卡逐行范围）。

## MLIR 与 DVM 对拍链（`:225-300`）

- `check_accuracy_mlir`（`:225-255`）：`launchers[1]` 是 fx launcher、`launchers[0]` 被测 launcher；输入/输出先 `clone_for_accuracy`（非张量原样、bf16 升 float）；fx 参考跑完，`dynamic=True` 时被测参数表按每张量 `(arg, arg, 0) + arg.size() + arg.stride()` 展开再调 launcher；`compare_outputs` 容差取 `ascend_npu_ir` 的 `anir_config.acc_comp_tol`；返回 `(output, result)` 二元组。消费端 meta_compiler.py `:117`。
- `check_accuracy_dvm`（`:279-300`）：`_load_fx_model`（`:258-276`）从 `TORCHINDUCTOR_CACHE_DIR/traced_graph_cache/{device_index}/{traced_graph_hash}` import FX 模块类并实例化，缓存在 `acc_meta['_fx_model']`；fx 前向输出与 `kobj.run(*args)` 的实际输出比对（同样 `anir_config.acc_comp_tol`）。消费端 dvm/__init__.py `:15`。

文档契约（INDUCTOR_ASCEND_CHECK_ACCURACY 的版本范围与阈值表）由[精度检查卡](torch_npu_inductor_accuracy_check.md)持有，本卡只记实现；`npu_config.acc_comp_tol` 的取值表不在本卡重写。

## `SimpleProfilingAnalyzer` 与 `simple_trace_handler`（profiler.py `:22-139`）

- `simple_trace_handler`（`:137-139`）被 `@no_exception_func()` 装饰：构造 `SimpleProfilingAnalyzer(dir_name, worker_name)`（构造即 `ProfPathCreator().init(...)`）并返回其 `trace_ready`——即 torch_npu.profiler 的 `on_trace_ready` 回调工厂。主线 `create_profiler`（runtime/triton_heuristics.py `:177-191`）与 fasta 批量测量都用它；**发布版用的是 `torch_npu.profiler.tensorboard_trace_handler`**（release `:85-99`，diff 锚）。
- `trace_ready`（`:117-133`）：trace 就绪时定位 `$ASCEND_HOME/tools/profiler/profiler_tool/analysis/msprof/msprof.py`（`_get_msprof_py_script_path`，`.._inductor.cpp_builder.get_ascend_home`；不存在返回 None）；在 `prof_inst.prof_if.prof_path` 下找 `PROF*` 目录，先删旧 `mindstudio_profiler_output`；`subprocess.run([sys.executable, msprof.py, "export", "summary", "-dir", prof_dir], capture_output=True)`，returncode != 0 → `RuntimeError`；导出后 glob `op_summary*.csv`/`op_statistic*.csv`（无 op_summary → `RuntimeError`）。
- `_convert_op_summary_to_kernel_details`（`:67-98`）：把 op_summary 转写成 `ASCEND_PROFULER_OUTPUT/kernel_details.csv`——单文件走**纯文本表头替换** `',Op Name,'→',Name,'`、`',Task Duration(us),'→',Duration(us),'`，表头无变化 → `RuntimeError`；多文件用 pandas 合并按 `Task ID` 排序再改名。这就是主线各 `read_device_time`/`_profile_batch_benchmark`/`do_bench_using_profiling_npu` 读到的 `kernel_details.csv` 的**生成源头**。
- `_convert_op_statistic`（`:100-115`）：单文件拷贝、多文件 pandas 合并，落 `ASCEND_PROFILER_OUTPUT/op_statistic.csv`。
- 任何异常 → `print_warn_msg` + `use_custom_analyzer=False` + `prof_inst.prof_if.analyse(async_mode=False)` 回退（源码注释原义 "fullback to default tensorboard_trace_handler"——拼写原样）。

## `mspti_batch_benchmark`（`:142-186`）

门槛→动作：`mspti` 包不可导入（`KernelMonitor is None`）→ `ImportError('mspti package not found.')`；`LD_PRELOAD` 不含 `libmspti.so` → `RuntimeError`。可选 `profiling_clear_l2` 时从 triton driver 取空缓存 buffer（否则 None）。`callback`：clear_l2 时跳过名字含 `zero`/`zeroslike` 的记录（排除清缓存 kernel 自身）；`filter_list` 要求 `any(x in data.name for x in filter_list)`；命中则记 `data.end - data.start`。`KernelMonitor()` 起停包裹 `warmup+active`（默认 5+30）轮 `fn()`（clear_l2 时每轮前 `cache.zero_()`），前后 `torch.npu.synchronize()`。**精确计数校验**：记录总数必须恰为 `kernel_cnt × (warmup + active)`，否则 `RuntimeError("A call to kernel_func should result in exactly one kernel record. Consider use filter_list argument.")`；每 kernel 取 active 窗口均值后 `/1000`（记录单位按 ns 折算 µs）。消费端：`_benchmark_kernel_funcs_batch` 以 `filter_list=["triton"]` 调用（[主线基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md) `:1538-1546`，其"warmup/active 默认值未覆盖"的保留至此闭合：5/30）。发布版无此函数（负证据，见开头）。

## 相邻卡边界

[发布版 autotuner 类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)（发布侧内联 check_accuracy/fallback_to_fx 与覆写副作用）；[主线基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)（mspti→profiler→单 bench 三级回退链的消费端）；[主线 Grid/launcher 卡](torch_npu_main_inductor_grid_and_launcher_generation.md)（`create_profiler`/`read_device_time` 的计时工具面）；[FASTA 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)（fasta 批量测量的 `simple_trace_handler` 引用）；[精度检查卡](torch_npu_inductor_accuracy_check.md)（env/阈值/版本文档契约）；[DVM 后端卡](torch_npu_dvm_mlir_codegen_and_fallback.md)与[MLIR/DVM 分解卡](../../../../training/guides/torch_npu_mlir_dvm_decomposition_registry_and_training_math.md)（两条对拍链的后端语境）。

## 失效边界与静态口径

- 全部为静态源码事实：msprof.py 导出子进程、mspti 回调与 LD_PRELOAD 门槛均未执行验证；`data.end - data.start` 的单位（ns→µs 的 `/1000`）是按源码算式记录，未对实测数据核量纲。
- `equal_nan=True/False` 的差异只说明两 pin 对拍谓词不同，不评价哪种语义"更正确"；文档契约归[精度检查卡](torch_npu_inductor_accuracy_check.md)。
- `check_accuracy_triton` 不覆写输出的结论限定本文件读到的函数体（`:133-222`）；调用方 `:1887` 之后对返回值的处理归[发布版 autotuner 类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)的主线对照读窗（返回 True 照常继续）。
- msprof 导出依赖 `$ASCEND_HOME` 布局与 ProfPathCreator 状态，安装差异不在本卡；发布版不存在本文件，不能用主线行为反推发布版。

## Evidence

- [主线 npu_compare.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/npu_compare.py)（primary；`:1-300` 全文）
- [主线 profiler.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/profiler.py)（primary；`:1-186` 全文）
- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（implementation；消费端锚 `:95`、`:101`、`:177-191`、`:1887` 均在既有读窗内）
- [发布版 npu_triton_heuristics.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py)（implementation；equal_nan=False 对照锚 `:848`、内联 check_accuracy `:806-860`、create_profiler `:85-99`）
