---
type: Guide
title: torch_npu 发布版 NPUCachingAutotuner 类体：Grid/launcher 生成、fx 调试回退与 run 决策树
description: 记录发布 pin npu_triton_heuristics.py 的 NPUCachingAutotuner 类体（全文 1397 逻辑行）：GridNpu 家族按 split_axis/split_blocks 算 grid、exec 生成 Python launcher、_make_launchers 全败 RuntimeError、save_npu_kernel 的 npubin 入 CudaKernelParamCache、bench 的 spill 罚与 rep=1、fx 图 dump/fallback_to_fx/check_accuracy/debug_kernel_in_run 四条调试链、maybe_run_debug 互斥优先级与 run() 决策树（launchers[0] 空表前置次序）；附 28 行 npu_triton_helpers shim 与主线 runtime 版对照（aclgraph 冲突抛错、check_accuracy 外移、force_fallback 配置整体缺席）。
tags:
- task.implementation
- topic.graph_execution
- task.debugging
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_helpers.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_helpers.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/npu_compare.py
  role: implementation
created_at: '2026-11-12T08:39:57Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 发布版 NPUCachingAutotuner 类体：Grid/launcher 生成、fx 调试回退与 run 决策树

## 固定版本与适用范围

发布 pin（f3ecfe4a）`npu_triton_heuristics.py` 逻辑行数 1397（`wc -l` 1396，末行无换行符；末逻辑行 `:1397` 是文件末尾 `cached_autotune(...)` 调用的收尾右括号），本卡全文覆盖（类头/precompile 与装饰器/benchmark 面、Grid/launcher/调试/run 类体、尾段）。同文件 28 行 `npu_triton_helpers.py`（全文）由本卡一并覆盖。主线对照（ac0e1564）为 `runtime/triton_heuristics.py`（4160 行）的**定向段**（`:1817-2016` 调试族与 run 头）与 `runtime/triton_helpers.py`（119 行全文）；[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)在主线侧只覆盖选择性段（imports/注册接线、`cached_autotune` 决策树 `:3236-3373`、FASTA 设置与预算段），主线各 autotuner 类体（Grid/launcher/cost model/symbolic grouped 等）在该卡与本卡均为显式声明的未覆盖面，本卡不重复。纯静态阅读，未导入/执行任何模块。draft、platforms 为空。

## Grid 家族（`:159-242`）

| 类 | 行为 | 失败/版本边界 |
| --- | --- | --- |
| `GridNpu`（`:159-186`） | `generate` 从 meta 读 `split_axis`/`split_blocks`（缺任一即 `RuntimeError`，`:167-170`）；`grid_fn(i)`：i 超界返回 "1"；block 为 None/1 返回原始 numel（**不做 ceil-div**）；python 模式 `({numel} + {block} - 1) // {block}`，cpp 模式整除表达式 `((numel + (block-1)) / (block))` | split_blocks 由 `triton_config_npu_index` 注入（见[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)），两模式语义相同、仅文本不同 |
| `GridExprNpu.from_meta_and_set_numel`（`:189-207`） | 按 `inductor_meta["grid_type"]` 从模块 globals 取类，断言为 `GridNpu` 子类 | 字符串驱动的类查找，静态记录 |
| `PrecomputedGridNpu`（`:211-222`） | 在 `inductor_meta["precomputed_grids"]` 里找与当前 config 全等的前置计算 grid，找不到 `AssertionError` | 预计算表由 codegen 侧生成（表生成面不在本卡） |
| `FixedGridNpu`（`:226-240`） | 固定三值 grid；`setup_grid_as_args` 声明 `_grid_0/1/2` 为 `extra_launcher_args` | extra_launcher_args 在 `make_launcher`/`_interpret_args_grid` 两端配套消费（`:363-364`、`:1002-1003`） |

## launcher 生成（`TritonCompileResultNpu.make_launcher` `:243-409`、`_precompile_config` 尾 `:521-583`、`_make_launchers` `:585-611`）

`make_launcher` 用 `exec` 拼出 `def launcher(def_args, stream)`：先由 `GridExprNpu` 算 grid 三轴文本（`:371-378`），再 `runner(...)` 直调（`:383-385`）。兼容面：triton attrs-dict 版本的 `num_warps`/`num_stages` 特殊隐参改写（`:261-277`）；`launch_metadata` 有无两个 torch 时代的 runner 参数序（`:328-361`）；`extra_launcher_args` 追加进 def_args（`:363-364`）。launcher 上挂 `n_regs/n_spills/shared/store_cubin`（`:388-391`）；`store_cubin` 为真时再存 `fn/bin/def_args/call_args` 供 AOTI 侧保存（`:394-408`）。

`_precompile_config` 尾（`:521-583`）：cfg kwargs 里属于 `fn.arg_names` 的项写入 `compile_meta["constants"]`；`compile_meta["debug"]` 三重门槛 = env `INDUCTOR_ASCEND_DEBUG` ∈ {true,1} 且 `assert_indirect_indexing`（缺省 True）且非 is_hip（`:535-539`）；无 `ASTSource` 即 `RuntimeError("Installed triton version too old, please upgrade")`（`:545-546`）；`GPUTarget(type, cc, warp=32)`（`:556-561`，warp 恒 32）；`triton.compile` 失败仅 log.debug（kernel_name/src/compile_meta）后**原样重抛**（`:573-582`）。

`_make_launchers`（`:585-611`）：已有则幂等返回；在 `DeviceGuard` + `device_interface.synchronize`（初始化上下文）下逐 `compile_results.make_launcher()`，**逐个捕获异常**；`len(launchers)==0` 时 `RuntimeError("No valid triton configs. ...")` 并附最后异常栈（`:608-610`）——任一成功即通过，与[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)记录的 precompile 串行全败抛 `NoTritonConfigsError` 是两级不同的失败面。

## 基准与缓存落盘（`:613-690`）

- `save_npu_kernel`（`:616-652`；`save_gpu_kernel` 为别名 `:613-614`）：`kernel_name` 缺失 `RuntimeError`；参数包（mangled_name/num_warps/shared_mem/stream/meta/config/inductor_meta/triton_meta/def_args/call_args）+ `bin.asm["npubin"]` 一起经 `CudaKernelParamCache.set(key, params, binary, bin_type='cubin')` 落盘（`:646-650`）——payload 是 npubin 而 `bin_type` 参数仍传 `'cubin'`（torch 上游缓存键的复用，静态记录）；`cuda_kernel_saved=True`。
- `bench`（`:655-677`）：非 custom kernel 且 `launcher.n_spills > spill_threshold`（meta 缺省 16）→ `inf`（`:658-661`）；`profile_bandwidth_with_do_bench_using_profiling` meta 为真走 `do_bench_using_profiling_npu(kernel_call, rep=1)`，否则 `benchmarker.benchmark_gpu(kernel_call, rep=1)`。模块级 `do_bench_using_profiling_npu`（`:132-155`）：warmup 2、`rep+10` 次带 `prof.step()`、profiler 结果目录 `profile_result/triton_{md5}`、读 `kernel_details.csv` 的 `Duration(us)`；其调用的 `read_device_time`（`:103-118`）签名带 `triton_only` 参数但**函数体未使用该参数**（静态观察，逐行核对无引用）——与 `benchmark_all_configs` 内部 pandas 侧的 `Name` 前缀过滤（见[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)）不是同一处。
- `autotune_to_one_config`（`:680-690`）：`benchmark_all_configs` 计时（其整批 inf 语义见[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)）→ `launchers=[min(timings)]`；总耗时=precompile+benchmark 写 `save_cache_hook`。

## fx 调试族（`:692-904`）

前提是 `inductor_meta` 带 `traced_graph_hash/traced_graph_dir` 的 fx 图 dump（由 dump 侧机制产出，本卡只读消费端）。`get_fx_graph_call`（`:701-740`）从 dump 目录 import 模块，重建 `fx_graph_call`：按 `non_contiguous_indices` 对输入 contiguous、按 `mismatch_indices_shapes` reshape、输出 reshape/copy 或 data 替换；`auto_fallback=True` 时改给按 `call_args_mapping` 映射的 `fallback_call`。

| 调试链 | 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- | --- |
| `fallback_to_fx`（`:760-803`） | `npu_config.force_fallback_kernel_id`（release config `:87` 缺省 `[]`，注释给出 `'all'`/`[1,2,10]` 用法）为 `'all'` 或 list；list 时从函数名尾段 parse kernel id（失败记 -1）且 id 在表内 | bf16 参数 `clone_preserve_strides(...).float()` 升 fp32 后跑 fx 图（`:791-796`），输出按 `call_args_mapping` 回拷并做 dtype 回转（`:797-800`） | 配置既非 `'all'` 也非 list → `RuntimeError`（ErrCode.VALUE，`:766-768`）；无 dump → 返回 None 照常走 kernel；**主线该配置整体缺席**（main config.py 无此键，全树 rg `force_fallback_kernel_id` 零命中，负证据） |
| `check_accuracy`（`:806-860`） | `npu_config.check_accuracy`（env `INDUCTOR_ASCEND_CHECK_ACCURACY`，release config `:74`） | 先跑 fx 图再跑 launcher（`:820-826`）；msprobe 可导入则 `api_accuracy_checker`（静态方法，msprobe 面见[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)）；否则按 `acc_comp_tol`（release config `:89-95` 字面表：fp32/default rtol 1.3e-6、fp16 1e-3、bf16 1.6e-2，atol 1e-5）`torch.isclose(equal_nan=False)` | 不匹配仅 `log.warning`（含最大相对差）并**用 fx 结果覆写实际输出** `actual.copy_(expected)`（`:850-856`）——检查后的张量值被替换，继续使用需知晓此副作用；阈值文档契约见[精度检查卡](torch_npu_inductor_accuracy_check.md)，主线阈值经 `INDUCTOR_ASCEND_CHECK_ACCURACY_RTOL_ATOL` 解析构建（main config `:286-337`） |
| `debug_kernel_in_run`（`:862-881`） | `npu_config.aot_inductor.debug_kernel_in_run` | kernel 前后 `torch.npu.synchronize()` + `torch.save` 参数张量到 `dump_path_py/{idx}_{fn}_before/after.pt`（全局 `kernel_idx` 计数） | 供与 AOTI cpp runtime dump 对拍（源码 docstring 原义） |
| `maybe_run_debug`（`:883-904`） | 互斥优先级：`dump_fx_graph`（data_dump，`:886-887`，不返回）→ `check_accuracy`（返回即止）→ elif `force_fallback_kernel_id` → elif `debug_kernel_in_run` | 返回模式字符串或 None | release config `:79-82`：`dump_fx_graph = env or check_accuracy or aot_inductor.debug_kernel`——**dump 触发链包含 aot debug_kernel**；主线无第三项（main config `:282` 仅 `or check_accuracy`） |

主线对照（定向读 `:1817-2016`）：`maybe_run_debug` 在 `dump_fx_graph` 且 `torch_npu.npu.is_current_stream_capturing()` 时**直接 `RuntimeError`**（aclgraph 不兼容，`:1870-1876`）；dump 前剥离尾部 runtime_block 参数避免回放双追加（`:1877-1884`）；`check_accuracy` 外移到 `npu_compare.check_accuracy_triton`（import `:95`，模块 300 行只读头 1-30：`clone_for_accuracy` 同款 bf16→float 语义）；`data_dump` 只在首次调用落盘（`_dump_counter`，`:1841-1849`）；`get_fn_name` 多一层 `kernel_name` 回退（`:1851-1860`）；主线**无** `fallback_to_fx`/`force_fallback_kernel_id` 调试链。

## run() 决策树（`:906-980`）与 `_interpret_args_grid`（`:982-1004`）

按序：①`triton_interpret` → 用 `configs[0]` 解释执行，kwargs 弹掉 `split_axis/split_blocks`（`:909-919`）。②`launchers[0]` 有 `fallback` 属性（extern/回退 launcher）→ 直调（`:921-925`）。③`len(launchers)!=1`：0 个先 `precompile()`（计时），>1 个 `autotune_to_one_config`（`:927-933`）。④非 `found_by_coordesc` 且 meta 开 `coordinate_descent_tuning` → `coordinate_descent_tuning` 单候选（`:935-942`）。⑤`store_cubin` 且（非 benchmark_run 或未保存过）→ `save_gpu_kernel`（`:945-946`）。⑥`dump_launch_params` → `_dump_launch_params`（`:948-949`）。⑦`maybe_run_debug` 命中任何模式即**直接 return**（`:952-955`；check_accuracy 模式里 launcher 已在函数内跑过）。⑧`autograd_profiler._is_profiler_enabled` 时 `RecordFunctionFast`（kernel_file/hash/backend/stream 元数据）包裹 launcher，否则直调（`:959-980`）。`_interpret_args_grid` 用含 `extra_launcher_args` 的名字表 zip 参数后 `eval_slow` 出 grid，并从 args 尾部剥掉 extra 项（`:982-1004`）。次序注意：②的 `self.launchers[0]`（`:921`）在③的空表 precompile 分支（`:927-931`）**之前**执行——launchers 为空且非 interpret 模式时，`:921` 先抛 `IndexError`，到不了③的 `precompile()`。即 `run()` 直调可用的本地前置是 launchers 非空（或调用方先 precompile）；静态记录该局部次序，不断言后端整体损坏，也不排除调用方先 precompile 的常规路径。

主线 run 头（`:1900-1984`）对应演进：②门槛加 `len(self.launchers)==1` 前置（`:1921-1925`，release 版无此判空）；③④合并为 `self.autotuner(...)` 调用 + `best_launcher`（`:1927-1928`，主体 `:1986-2016`：best_launcher 缓存命中即返回、`candidate_plan`、单候选免测、确定性归约跳过测量——该段在 `:1817-2016` 定向读窗内，细节不在此展开；主线 autotuner 类体其余部分仍未读，见失效边界）；launch 前经 `_build_runtime_launch_args` 组 runtime blocks（`:1934`）；调试门 `is_run_debug()`（lru 缓存）且排除 `USER_AUTOTUNE`（`:1953`）。

`NPUDebugAutotuner`（`:1007-1039`）：`regex_filter` 过滤 `_find_names` 最长名；run 后 `bench` 一次并缓存 `(ms,num_gb,gb_per_s)`，append `collected_calls` 并 `print` 带宽串——供 profile_bandwidth 模式（`NPUDebugAutotuner` 装点见[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)）。

## npu_triton_helpers shim（release 28 行全文 vs 主线 runtime 版 119 行全文）

release 版只做三件事：`libdevice` 双重回退导入（先 `triton.language.extra.cann.libdevice` import，失败退 `extra.ascend.libdevice`；再用属性访问复核一次，`:4-13`）；定义 `@triton.jit` 的 `maximum/minimum` 薄包装（`:16-25`）；**把 torch `triton_helpers.maximum/minimum` 模块属性替换为上述包装**（`:27-28`）。生成代码经 `gen_triton_ext_imports` import 本模块（见[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)），import 副作用即完成 patch。

主线 `runtime/triton_helpers.py` 不再 patch 上游属性，改为 `from torch._inductor.runtime.triton_helpers import *` 再导出，并新增四个语义修正函数（docstring 原义）：`frexp`（fp32 位级分解，处理 ±0/inf/nan 与 fp16/bf16 精确升档）、`_extremum`/`max_with_index`/`min_with_index`（整数 argmin/argmax 时 `tl.min/tl.max` 结果可能不等于任何输入 lane、双源 `tl.reduce` 会返回 lane 坐标而非携带索引——拆成极值 reduce + 最小携带索引两步）、`welford`（NPU Triton 编译器 `TritonOpConverter.cpp` 断言 `srcs.size() <= 2`，三源 `tl.reduce` 拆三个单源 reduce）。主线隔离树 `triton_experimental/npu_triton_helpers.py`（Bool/NaN 比较族）已由[实验数值 helper 卡](torch_npu_experimental_triton_numeric_helpers_and_nan_bool.md)闭合，与本节不是同一文件，不互推。

## 失效边界与静态口径

- 本卡全部为静态代码事实；`isclose` 阈值、spill 16、rep=1 等数值以源码常量为准，未做任何设备复算或测量。
- `check_accuracy` 的覆写副作用、`force_fallback_kernel_id` 的 kernel id 尾段 parse（函数名末段非数字记 -1）都是调试路径行为，不构成对正常执行流的影响承诺。
- fx dump 的**生产端**（dump 目录如何写出、`traced_graph_hash` 如何进入 inductor_meta）未在本卡范围；主线 `npu_compare.py` 只读了头部 1-30 行，`check_accuracy_triton` 本体未逐行读。
- 主线 `runtime/triton_heuristics.py` 除 `:1817-2016` 外的类体（Grid/launcher/cost model/symbolic grouped/debug autotuner/cached_autotune 等约 3900 行）不在本卡范围；[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)在主线侧同样只覆盖选择性段（imports/注册/`cached_autotune` 决策树/FASTA），这些类体在其卡内也是显式声明的未覆盖面。
- release `npu_triton_helpers` 的属性替换只影响导入时点之后经该模块属性取值的调用方；`libdevice` 双回退的可用性取决于安装的 triton-ascend 版本，未验证。

## 相邻卡边界

[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)（`:412-520` 类头/precompile、`:1041-1396` 装饰器/benchmark_all_configs/triton_config_npu_index、gen_triton_ext_imports 装点；本卡覆盖该文件的类体，互链不重写）；[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)（主线 monkey-patch、注册与 `cached_autotune` 决策树、FASTA 选择性段；主线 autotuner 类体未闭合）；[精度检查卡](torch_npu_inductor_accuracy_check.md)（INDUCTOR_ASCEND_CHECK_ACCURACY 文档契约与版本范围）；[实验数值 helper 卡](torch_npu_experimental_triton_numeric_helpers_and_nan_bool.md)（隔离树 helper）；[TileGenerator 裁剪卡](torch_npu_release_flat_inductor_tile_generator_descents.md)（配置来源）；[设备算子覆写卡](torch_npu_release_flat_inductor_device_op_overrides.md)（wrapper 侧设备面）。
