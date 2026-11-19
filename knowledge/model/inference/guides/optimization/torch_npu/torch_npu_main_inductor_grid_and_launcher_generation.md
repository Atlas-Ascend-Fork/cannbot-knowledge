---
type: Guide
title: torch_npu 主线 runtime Grid 家族与 launcher 生成：profiler 计时工具、runtime block 网格与 exec 拼装
description: 记录主线 runtime/triton_heuristics.py 的 :106-730 与 :2017-2100 段：CompileThreadPool 与模块级 profiler 计时工具（read_device_time 均值口径、npu_profiler_session_active 探针）、GridNpu/GridExprNpu 的 runtime block 与分组网格路径、TritonCompileResultNpu.make_launcher 的 constexpr 字面量替换与 grouped 缺参校验、_NPUSkipPrecompilePlugin、NPUCachingAutotuner.__init__ 候选/变体状态、copy_args_to_cpu_if_needed 显存预算拷贝与 _interpret_args_grid 三分支；附发布版逐点差异锚。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py
  role: implementation
created_at: '2026-11-12T13:13:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 runtime Grid 家族与 launcher 生成：profiler 计时工具、runtime block 网格与 exec 拼装

## 固定版本与适用范围

主线 pin（ac0e1564）`runtime/triton_heuristics.py`（4160 行）的 Grid/launcher 生成面：`:106-730`（模块级工具、Grid 家族、`make_launcher`、`_NPUSkipPrecompilePlugin`、`NPUCachingAutotuner.__init__`/`copy_args_to_cpu_if_needed`）与 `:2017-2100`（`_interpret_args_grid`），另定向读 `:3666-3681`（`filter_launcher_def_args`）。`cached_autotune` 决策树与补丁安装见[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)；基准与候选计划见[主线基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)；precompile 主体见[主线 precompile 管线卡](torch_npu_main_inductor_precompile_pipeline.md)；调试/run 头（`:1817-2016`）的对照面见[发布版 autotuner 类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)。发布 pin（f3ecfe4a）对应面已由[发布版 autotuner 类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)闭合，本卡只给逐点差异锚。纯静态阅读：未导入/执行/编译任何上游代码；draft、platforms 为空。

## 模块级编译线程池与 profiler 计时工具（`:106-248`）

| 实际门槛/对象 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| `_metadata_value`/`_get_sync_block_lock_num`/`_get_sync_block_lock_layout`（`:106-134`） | dict/对象两种 metadata 形态统一读字段；锁标记取 `max(lock_num, sync_block_lock_layout, 0)`。注释原义：Triton-Ascend 3.6 用打包的 `sync_block_lock_layout` 取代旧 `lock_num`，该 helper 让只判断"是否有锁"的旧消费端（如实验 fast launcher）仍拿到非零标记 | 唯一消费端是 `save_npu_kernel`（`:1342-1345`，见[主线 precompile 管线卡](torch_npu_main_inductor_precompile_pipeline.md)） |
| `CompileThreadPool`/`compile_thread_pool`（`:137-158`） | 模块导入即建 `ThreadPoolExecutor(max_workers=npu_config.precompile_thread_num)`；`warmup()` 为每线程提交一个阻塞在 `thread.Event` 上的 worker 强制建线程 | 单例在 import 期冻结线程数；进程内后改 `precompile_thread_num` 不生效（静态口径） |
| `npu_profiler_session_active()`（`:161-174`） | 探测 `torch_npu.profiler._profiler_path_creator.ProfPathCreator().is_prof_inited`；任何异常 → `log.debug` + 返回 False。docstring 原义：NPU profiler 是进程级单例，嵌套会话会让外层丢数据，autotune 绝不能在调用方 profiling 时再开会话 | 探针 fail-open（异常按"无会话"处理），供 `_benchmark_kernel_funcs_batch` 让位批量测量（见[主线基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)） |
| `create_profiler`（`:177-191`） | 包 `torch_npu.profiler.profile`：NPU activity、无 shapes/memory/stack、`schedule(wait,warmup,active,repeat,skip_first)`、`on_trace_ready=simple_trace_handler(profile_path)`、ExperimentalConfig AiCoreNone/Level0 | **发布版差异**：release 同名函数（f3ecfe4a `:85-99`）用 `torch_npu.profiler.tensorboard_trace_handler` 直落 trace，无 msprof 导出转换（见[主线 npu_compare 与 profiler 工具卡](torch_npu_main_inductor_npu_compare_and_profiler_tools.md)） |
| `read_device_time`（`:197-213`） | `os.walk` 找 `kernel_details.csv` 读 `Duration(us)` 列；`return_list=False` 返回**均值** `sum/len`；找不到 → 先 `delete_file_base(torch_path)` 再 `RuntimeError` | 两个 pin 的函数体都**不使用** `triton_only` 形参。**发布版差异**：release（`:103-118`）`return_list=False` 返回 `sum`（总量非均值），且不删目录直接 raise |
| `_summarize_statistics`（`:215-223`） | quantiles 走 `torch.quantile`；`return_mode="all"` 返回列表；否则 `getattr(torch, mode)(times).item()` | 模式字符串直接映射 torch 聚合函数 |
| `do_bench_using_profiling_npu`（`:225-248`） | 校验 return_mode ∈ {min,max,mean,median,all}；stream 同步 + warmup（默认 2）；`create_profiler(torch_path, active=8)` 内跑 `rep+10`（默认 10 → 20）次 `fn()` + `prof.step()`；读 csv 后删目录，`_summarize_statistics` 汇总 | 目录 `os.getcwd()/profile_result/triton_{md5(uuid)}`。**发布版差异**：release（`:132-155`）`create_profiler(torch_path)` 不覆写 active（默认 1），其余 warmup=2/rep+10 相同 |

## Grid 家族（`:250-397`）

- `GridNpu`（dataclass，`:250-278`）：`generate` 从 meta 读 `split_axis`/`split_blocks`，缺任一即 `RuntimeError`（`:259-262`）；`grid_fn(i)` 超界返回 "1"、block 为 None/1 返回原始 numel（不做 ceil-div）、python 模式 `({numel}+{block}-1)//{block}`、cpp 模式整除表达式——与发布版 `GridNpu`（f3ecfe4a `:159-186`）语义一致（发布版卡已记），差异仅在类形态（主线为带 `numels`/`mode` 字段的 dataclass）。
- `GridExprNpu.from_meta_and_set_numel`（`:288-340`）三路分派：`globals()` 里查不到 `grid_type` → **回退上游 `GridExpr.from_meta`**（发布版 `:189-207` 是 `issubclass` 断言，查不到直接 AssertionError）；非 `GridNpu` 子类 → 直接构造并 `generate(cfg)`；`GridNpu` 子类且 `inductor_meta["runtime_block_arg_names"]` 非空 → **runtime block 网格路径**：按 `axis_names` 解析每个块参数名（`removesuffix("BLOCK").lower()`），轴名不在 `axis_names` → `RuntimeError`；`runtime_grid_fn` 用块参数名生成与 `GridNpu` 同形的 ceil-div 文本（`:309-335`）。
- `from_grouped_meta_and_numel`（`:342-381`）：分组专用，grid 类必须是 `GridNpu` 子类否则 `RuntimeError`（"grouped grid path expects GridNpu-compatible grid"）；轴解析与表达式同上，`grouped_grid_fn` 输出三轴。
- `_create_launcher_grid`（`:384-397`）：`group_enabled` → 分组路径；否则 `from_meta_and_set_numel`。
- **负证据**：主线 runtime 文件 rg `PrecomputedGridNpu|FixedGridNpu` 零命中——发布版的预计算/固定 grid 两类（release `:211-240`，含 `_grid_0/1/2` extra_launcher_args 机制）主线不存在；主线 `extra_launcher_args` 由 codegen 侧按需注入。

## `TritonCompileResultNpu.make_launcher`（`:400-631`）

`exec` 拼装 `def launcher(def_args, stream)`。与发布版（release `:243-409`，发布版卡已记）逐点差异：

| 拼装步骤 | 主线动作 | 发布版对照 |
| --- | --- | --- |
| attrs-dict 时代 triton（`:418-460`） | 为每个 constexpr 建**字面量替换表** `repl`：字符串常量 → `r'...'`，其余 `repr()`（注释原义：dtype 常量生成可解析限定名 `triton.language.float32` 而非裸名 `fp32`）；`def_args` 过滤 constexpr 但**保留 runtime block 参数**（`:445-449`）；`call_args` 按 signature 过滤、constexpr 用字面量代入（`:450-460`） | release 同分支只改写 `num_warps`/`num_stages` 两个特殊隐参（`str()` 非 `repr`），def/call_args 基本取全量 `fn.arg_names`（release `:253-277`） |
| 非 attrs-dict 时代（`:461-476`） | `filter_launcher_def_args`（`:3666-3681`）：保留"不在 cfg 键集**或是 runtime block 名**"且不在 `none_args` 的参数——runtime block 即使是 cfg 键也保留为位置形参 | release 直接 `[name not in cfg_dict and not in none_args]`（release `:285-290`），无 runtime block 概念 |
| grouped 校验（`:478-491`） | `group_enabled` 时按 `runtime_block_append_order` 检查每个 runtime block 名**同时**出现在 def_args 与 call_args，缺项 `RuntimeError("Grouped launcher is missing runtime block args: ...")` | 无此段 |
| exec 作用域（`:504-539`） | 注入 `math`/`torch`/`triton` 模块（注释原义：让 repr 生成的限定名在 exec 时可解析、避免 NameError）；hooks 经 torch `knobs.runtime` 或类属性双轨取（`:498-503`）；`packed_metadata` namedtuple 就地 `_asdict()` | release 同位置注入的是 `"log": log`（release `:323`），无 math/torch/triton 注入（rg 该文件 `"math"|"torch"|"triton"` scope 键零命中） |
| runner 参数序（`:541-574`） | 有 `launch_metadata` 属性时代：`launch_enter_hook` 存在才生成 `bin.launch_metadata(...)` 表达式，否则 `None`；旧时代参数序 `grid_0/1/2, num_warps, *cta_args, shared, stream, function, hooks, metadata, *call_args` | release 同构（release `:328-361`），发布版卡已记 |
| 网格与收尾（`:576-614`） | `extra_launcher_args` 追加进 def_args（`:576-577`）；numels 取名含 `_numel` 的形参（`:579-583`）；`_create_launcher_grid` 出三轴文本；拼装行主线**无** release 的 `log.debug('[Runtime] Launch KERNEL ...')` 行（release `:379-384` 有）；launcher 挂 `config/runnable/n_regs/n_spills/shared/store_cubin`，另挂 **`cache_hash = triton_hash_to_path_key(binary.hash)`**（`:609-612`，供缓存命中写 `triton_cache_hash`，见[主线基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)） | release 不设 `runnable` 标志（rg `runnable` 零命中）也不设 `cache_hash` |
| store_cubin 保存面（`:616-630`） | attrs-dict 时代再过滤一次：def_args 去掉 cfg 键、call_args 去 constexpr signature 与 `none_args`，存 `fn/bin/def_args/call_args` 供 AOTI | release（`:394-408`）**同款** attrs-dict 二次过滤（对照 `:362-411`），结构等价 |

## precompile 跳过插件与基类状态（`:634-729`）

- `_NPUSkipPrecompilePlugin`（`:634-638`）：`pre_compile` 在 `autotuner.skip_precompile` 为真时返回 None（跳过基类 precompile 钩子），否则 `DEFER`。`NPUCachingAutotuner.__init__` 把它 **insert(0)** 到 `_plugins` 最前（`:660`）。rg 全仓：`skip_precompile` 唯一写入方是 `NPUFastAutotuner`（fasta_autotune.py `:869` 置 True，`:920/:924/:993/:1001` 复位 False）——fasta tuner 用它把基类 precompile 推迟到桶构造后。
- `__init__`（`:640-674`）在基类状态之外新增：`exceptions`/`fn_name`/`runtime_block_arg_names`（读 `inductor_meta`，缺省 `()`）与候选/变体五元组 `candidate_plan=None`、`variant_launcher_map={}`、`compiled_candidate_entries=()`、`best_candidate_config=None`、`best_runtime_blocks=()`、`best_launcher=None`；注释原义："candidate_plan keeps the full runtime candidate space, while variant_launcher_map points to the deduplicated compiled variants"。该五元组的消费语义由[主线基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)持有。
- `copy_args_to_cpu_if_needed`（`:676-729`）：仅 `optimize_mem` 开启时工作；`torch.accelerator` 探测抛 `RuntimeError` → 返回空表（fail-open）。预算 = `max_memory_allocated - memory_allocated`；对 `mutated_arg_names` 内、device ∈ {cuda,xpu,npu} 的张量按 `compute_required_storage_length × element_size` 计字节：超预算 → `torch.empty_strided(..., pin_memory=True)` CPU 拷贝（`copy_` non_blocking，再失败退 `arg.to("cpu")`）；未超 → 预算扣减。返回 `{name: (原参, cpu 拷贝)}`。消费端在隔离实验树的 fast launcher（triton_experimental/npu_triton_heuristics.py `:1311`），本仓主线 run 不消费。

## `_interpret_args_grid`（`:2021-2098`）

- constexpr 名单 = triton 自身 `fn.constexprs` 索引名 ∪ `inductor_meta["declared_constexpr_names"]` **再减** `runtime_block_arg_names`（`:2037-2043`）。源码注释原义：constexpr 以 kwargs 传入不占位置槽，若留在名字表会把尾部 grid 附加参绑错值、`_grid_2` 未定义；留在 def_args 的 runtime block 参数必须保持位置参数。
- 三分支 `eval_slow`（`:2048-2095`）：`group_enabled` → `from_grouped_meta_and_numel`，名字表 `[位置参数…, extra_launcher_args…, runtime_block_names…]` zip `(*args, *runtime_blocks)`；非分组但有 runtime block → `from_meta_and_set_numel` 同形名字表；否则纯 `[位置参数…, extra_launcher_args…]` zip `args`。
- 返回前从 args 尾部剥掉 `extra_launcher_args`（`:2096-2097`）。消费点 `:1907`（interpret 执行）、`:1937`（data dump）、`:1955`（debug launcher），均在调试/run 头窗口（`:1817-2016`，对照面见[发布版 autotuner 类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)）。
- **发布版差异**：release `_interpret_args_grid`（`:982-1004`）只有单一名字表分支，无 runtime_blocks 形参、无 `declared_constexpr_names` 补集。

## 相邻卡边界

[主线 precompile 管线卡](torch_npu_main_inductor_precompile_pipeline.md)（`:831-987`/`:1131-1415` 编译与落盘——本卡 `__init__` 状态的消费端）；[主线基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)（bench/prerun/候选选择）；[发布版 autotuner 类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)（发布侧 Grid/launcher/run 全量对照基线）；[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)（补丁安装与 `cached_autotune` 决策树）；[实验树 grid/launcher 卡](torch_npu_experimental_triton_grid_and_launcher_codegen.md)（隔离树，非本文件）。

## 失效边界与静态口径

- 本卡全部为两 pin 静态阅读；`grid_type` 字符串驱动的 `globals()` 类查找、`exec` 拼装的正确性均未运行验证；`precompile_thread_num` 解析失败 `sys.exit(1)` 的行为由[配置解析卡](torch_npu_inductor_config_parsing.md)持有。
- `copy_args_to_cpu_if_needed` 的预算扣减顺序（遍历 `fn.arg_names` 序）与 pin_memory 可用性未在设备上验证；主线本仓 run 链不消费该 helper，不据此断言主线行为变化。
- triton attrs-dict 时代的判定 `triton_version_uses_attrs_dict()` 为上游接口，两分支随安装的 triton-ascend 版本取一；未验证任何具体版本。

## Evidence

- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（primary；读窗 `:106-730`、`:2017-2100`、`:3666-3681`）
- [发布版 npu_triton_heuristics.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py)（implementation；对照读 `:85-160`、`:186-290`、`:490-583`；Grid/make_launcher/run 全量结论以[发布版类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)为准）
