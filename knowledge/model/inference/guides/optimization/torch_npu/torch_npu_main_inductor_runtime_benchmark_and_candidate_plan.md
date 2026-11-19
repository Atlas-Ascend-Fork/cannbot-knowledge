---
type: Guide
title: torch_npu 主线 NPUCachingAutotuner 基准与候选选择：候选计划、prerun 预筛与批量测量回退链
description: 记录主线 runtime/triton_heuristics.py 中 NPUCachingAutotuner 的测量与选择面：build_candidate_plan 候选/变体数据模型与编译去重、_benchmark_candidate_entries 的 prerun 单次计时预筛（min_k=10/max_k=200/50ms 预算）、mspti→profiler 批量→单 bench 三级回退链、bench 的双 spill 阈值与 with_profiler 三态门、确定性归约跳过测量与单候选免测路径的缓存写入差异。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_switch.py
  role: evidence
created_at: '2026-11-12T12:38:02Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 NPUCachingAutotuner 基准与候选选择：候选计划、prerun 预筛与批量测量回退链

## 固定版本与适用范围

主线 pin（ac0e1564）`torch_npu/_inductor/runtime/triton_heuristics.py`（4160 行）中 `NPUCachingAutotuner` 的测量与选择面：候选计划构造族 `:731-830`、precompile 编译账目上下文 `:988-1130`、基准类体 `:1416-1815`、`autotuner()` 调用点 `:1986-2019`、模块级计划构造器 `:3651-3727` 与文件尾 prerun 工具 `:4130-4160`。决策树与补丁安装见[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)；precompile 主体与 UB 溢出反馈实现见[主线 precompile 管线卡](torch_npu_main_inductor_precompile_pipeline.md)；调试族与 run 头（`:1817-2016`）的对照面见[发布版类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)。发布 pin（f3ecfe4a）无 `runtime/` 包，发布侧对应面已由[发布版 autotuner 类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)闭合（其 `bench`/`autotune_to_one_config` 是另一实现），本卡只在『发布版对照』给差异锚。纯静态阅读：未导入/执行/编译任何上游代码，未触发任何 autotune 或设备路径；draft、platforms 为空。

## 候选计划：`build_candidate_plan`（`:3683-3727`）与消费端（`:764-830`）

数据模型（逐字核对）：每个 config 生成一个 candidate `{candidate_id: "c{idx}", variant_id, full_config, runtime_blocks: ((name,int),...)}`；`variant_id` 按「剥离 runtime block 键后的 config repr」去重编号 `v{idx}`——多个 candidate 只在 **runtime block 取值**上不同时共享同一编译变体，`variant_order`/`runtime_block_append_order` 固定顺序。消费端：

| 门槛/动作 | 边界 |
| --- | --- |
| `_precompile_variant_configs`（`:764-785`）：只对 `variant_order` 里的**编译去重后**变体构造 `variant_cfg` 并挂 `_runtime_variant_id` | candidate 数 > variant 数时记一条 dedup 日志；BLOCK 选择推迟到 autotune |
| `_refresh_variant_launchers`（`:787-822`）：先按 `_runtime_variant_id` 归并已有 launcher，缺项再按 config repr 兜底；产出 `variant_launcher_map` 与 `compiled_candidate_entries`（只含变体有 launcher 的 candidate） | `autotuner()`（`:2001-2002`）与 `autotune_to_one_config`（`:1793-1794`）在 map 为空时才刷新；未编译变体只 log.debug |
| `_set_best_candidate`（`:731-748`）：写入 `best_candidate_config`/`best_runtime_blocks`/`best_launcher` | `bench`（`:1425-1426`）用 `best_runtime_blocks` 复现最佳口径 |

## prerun 预筛与三级批量测量回退（`_benchmark_candidate_entries` `:1569-1727`）

调用序（`autotune_to_one_config` `:1776-1815` → `_benchmark_candidate_entries`，由 `autotuner()` `:2017` 进入）：先建/刷新 plan，再按序执行：

1. **prerun 计时**（`:1607-1663`）：每个 compiled candidate 造一个冻结闭包（default-arg 绑定，`:1617-1618`）：`pre_hook` 有值先调用（`:1619-1625`）→ `clone_args` → `reset_to_zero_args(*args)` → launcher 执行；`_measure_prerun_ms`（`:4130-4137`）用一对 `torch.npu.Event` 计时。prerun 抛异常时按 `autotune_continue_on_failure`（config `:438`，`TORCHINDUCTOR_NPU_BACKEND == "default"` 才为真）分流：真→log.warning 后放弃该 candidate；假→`RuntimeError` 终止。注意 `config.triton.spill_threshold`（`:1614-1615`，torch 上游配置）在此挡候选，而 `bench`（`:1419-1421`）用的是 `inductor_meta["spill_threshold"]` 缺省 16——同类内两处阈值来源不同。
2. **预筛**（`:1665`）：`_select_prerun_top_candidates`（`:4139-4160`，文件末函数）：按 prerun 耗时升序，**前 `min_k=10` 个无条件入选**；此后循环仅当 `len(selected) < max_k=200` 且 `total_ms < max_total_ms=50.0` 时追加——即 10 个之后的候选才受 50ms 预算约束，且检查发生在追加之前。三个参数均为函数字面默认值；该函数与 `_measure_prerun_ms` 在本文件共两处调用族：候选路径 `:1635/:1665` 与 `NPUSymbolicGroupedAutotuner` 类体内 `:3023/:3042`（见[分组 autotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)）。
3. **批量测量回退链**（`_benchmark_kernel_funcs_batch` `:1525-1568`）：门槛 `npu_config.aggresive_autotune`（config `:373-376`，`INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE` ∈ {1,true}）为假或列表空 → 直接 `None`；调用方 profiler 会话活跃（`npu_profiler_session_active()`）→ `warning_once` + `None`（批量被让位给计时器）。否则 **mspti 批量**（`mspti_batch_benchmark(kernel_funcs, filter_list=["triton"])`，`:1538-1546`）→ 失败或计数不符（raise 的 RuntimeError 在同一 try 内，`:1542-1545`）被 `except Exception` 捕获记 warning（`:1547-1552`）→ **profiler 批量** `_profile_batch_benchmark`（`:1471-1524`）→ 同样捕获后返回 `None`（`:1554-1567`）。
4. 批量为 `None` 时逐候选走 `self.bench`（`:1695-1701`）；每个测得的 timing 回填 `coordesc_tuner.cache_benchmark_result`（`:1703-1709`；批量路径的 timing 由外层 `:1554-1560` 校验计数后**原样返回**，单位沿用各来源口径——mspti 路径量纲取决于 `mspti_batch_benchmark` 本体（未读），profiler 路径为微秒，与单 bench 的 benchmarker 结果之间未做统一换算）；全部 `inf` → `RuntimeError("All runtime block candidates ... are not runnable.")`（`:1711-1714`）。

`_profile_batch_benchmark`（`:1471-1524`）：`WAIT=1/WARMUP=1/ACTIVE=10/REPEAT=1/SKIP_FIRST=1` 加 `REDUNDANT_STEP=3` 共 16 步，每步循环全部 kernel 后 `torch.npu.synchronize()` + `prof.step()`；结果目录 `os.getcwd()/profile_result/triton_{md5(随机uuid)}`；逐个 `kernel_details.csv` 用 pandas 过滤 `Name` 以 `triton` 开头的行，行数必须恰为 `kernel_count × ACTIVE`，否则 `RuntimeError`；耗时按 kernel × ACTIVE 行的 `Duration(us)` 求和后除以 ACTIVE（微秒原口径，无单位换算）。**目录删除只发生在两条正常路径**：首个 csv 处理完（`:1519`）与无 csv 返回空表（`:1522`）；`pd.read_csv`/行数校验抛 `RuntimeError`（`:1506-1512`，报错文案指向 `{target_file}` 供检查）时目录保留现场，外层 `:1561-1566` 捕获后回退单 bench、也不清理。找不到 csv → 返回空表（`:1523`）。与发布版模块级 `do_bench_using_profiling_npu`（单 kernel、warmup 2、`rep+10`，见[发布版类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)）不是同一实现。

## 单点 `bench`（`:1416-1443`、`_bench_with_launch_args` `:1444-1470`）

门槛→动作：① 非 custom kernel 且 `launcher.n_spills > inductor_meta["spill_threshold"]`（缺省 16）→ `inf`。② `runtime_blocks` 缺省：`best_launcher` → `best_runtime_blocks`；否则从 `compiled_candidate_entries` 找该 launcher 的 candidate 用 `_diagnostic_runtime_blocks` 取值，找不到保持 `()`。③ `_bench_with_launch_args`：`with_profiler` 是**三态**（`None` → 取 `inductor_meta["profile_bandwidth_with_do_bench_using_profiling"]` 缺省 False；显式 False/True 直接生效，`:1462-1465`）；为真且当前无 profiler 会话（`:1466`）→ `do_bench_using_profiling_npu(kernel_call, rep=1)`；否则 `benchmarker.benchmark_gpu(kernel_call, rep=1, device_type='npu', is_vetted_benchmarking=True)`（`:1469`）。`kernel_call`（`:1450-1457`）**操作数区分**：`clone_args` 作用于 `launch_args`（runtime block 调整后的发射参数，`:1435`），发射克隆之前先 `reset_to_zero_args(*reset_args, **kwargs)` 作用于**原始 `args`**（`bench` `:1435-1440` 把原 `args` 作为 `reset_args` 传入）——被置零的不是克隆，本路径不提供「全部副作用隔离」的承诺。

发布版对照（`bench` f3ecfe4a `:655-677`）：签名无 `runtime_blocks` 参数、`with_profiler=False` 二态、meta 为真无条件走 profiler 路径（无会话活跃检查）、`benchmark_gpu(kernel_call, rep=1)` 不带 `device_type/is_vetted_benchmarking`、kernel_call 不做 `reset_to_zero_args`——四点均为逐字复核的差异锚，其余 spill 门语义相同。

## 选择与缓存写入：确定性跳过与免测路径（`:1728-1815`、`:1986-2019`）

| 门槛 | 动作 | 失效/版本边界 |
| --- | --- | --- |
| `_should_skip_autotune_for_determinism`（`:1728-1746`） | `inductor_meta["deterministic"]` 或 `["are_deterministic_algorithms_enabled"]` 为真 且 heuristic ∈ {REDUCTION, PERSISTENT_REDUCTION} | docstring 原义：跳过的是**测量**，全部 config 仍编译以免编译失败崩溃程序；pointwise 不受影响（tiling 不改变浮点数值） |
| 命中 → `_pick_first_compiled_candidate("deterministic")`（`:1748-1775`） | 取 `_first_compiled_candidate_entry()`（空则 `RuntimeError`，`:757-762`）置最佳；`launchers=[launcher]`；`save_cache_hook(best_config, 0, found_by_coordesc, triton_cache_hash=launcher.cache_hash)` | 时间记 0；`autotune_time_taken_ns` 不设置 |
| 未命中 → `autotune_to_one_config`（`:1776-1815`） | `_benchmark_candidate_entries` 计时 → `builtins.min`（`:1789`）选最优 candidate → `_set_best_candidate` + `launchers=[best_launcher]`；`autotune_time_taken_ns = precompile_time_taken_ns + benchmark`（`:1798-1800`）；`save_cache_hook(best_config, 总耗时, found_by_coordesc, triton_cache_hash)`（`:1801-1814`） | 全 inf 已在上游 `RuntimeError`；`best_candidate_config` 为 None 时回退 `launchers[0].config` |
| `autotuner()` 单候选捷径（`:2004-2011`） | `candidate_count==1` 时直接 `_set_best_candidate` 第一个 compiled entry 并 return | **不写 `save_cache_hook`、不设 `autotune_time_taken_ns`**——与确定性路径（写 0）和基准路径（写实测）都不同；只 log.info |
| `autotuner()` 前置（`:1986-2002`） | `best_launcher` 命中直接返回；plan 缺则构造；`len(launchers)==0` 时先 `_save_precompile_runtime_inputs`（`:1995`）再 `precompile()`（`:1997`） | precompile 失败面（`_precompile_configs_with` 全败 `NoTritonConfigsError`、UB 溢出反馈 `:1024-1041` 只对 `type(self) is NPUCachingAutotuner` 生效，`:1026`）见[precompile 管线卡](torch_npu_main_inductor_precompile_pipeline.md) |

## 选择与免测路径验收契约（test_autotune_switch.py）

`test/_inductor/test_autotune_switch.py`（531 行全文静态阅读，未运行）钉死本节选择行为：

- **max 开关不裁候选**（`test_max_off_still_benchmarks_existing_candidates` 等 3 项）：`NPUCachingAutotuner.autotuner` 在 max 旗标全关、显式 env `TORCHINDUCTOR_MAX_AUTOTUNE[_POINTWISE]=0` 时**仍对已有候选 benchmark**（`autotune_to_one_config` 被调）；pointwise 显式开也照测——开关只影响候选生成（见[legacy 候选生成卡](torch_npu_main_inductor_legacy_config_and_decorator_entries.md)验收契约），不改变“有候选就测”。
- **确定性只对 reduction 生效**（`test_determinism_overrides_max_flags_only_for_reductions`）：POINTWISE 四旗标组合下照测；REDUCTION/PERSISTENT_REDUCTION 在 `deterministic` 或 `are_deterministic_algorithms_enabled` 任一为真时免测、取首个 launcher，且 `save_cache_hook` 以 `(config, 0, found_by_coordesc=False, triton_cache_hash=None)` 记零耗时——`triton_cache_hash=None` 在无 cache_hash 时同样写入（`test_deterministic_selection_preserves_upstream_cache_metadata`：有 cache_hash 时透传、`found_by_coordesc` 跟随 `coordinate_descent_tuning`）。
- **免测路径**：单候选不 benchmark（`test_single_candidate_does_not_benchmark`）；`best_launcher` 已选不再测（`test_selected_candidate_does_not_benchmark_again`）。
- 决策树分派序与 import 无损的断言由[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)『测试验收契约』节持有；分组侧契约由[分组 autotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)持有。

## 相邻卡边界

[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)（决策树选到哪类 tuner、`_load_cached_autotuning` 缓存命中语义——本卡是 row-4 `NPUCachingAutotuner` 测量本体的闭合）；[主线 precompile 管线卡](torch_npu_main_inductor_precompile_pipeline.md)（precompile 主体与 UB 溢出重试）；[发布版 autotuner 类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)（发布侧 Grid/launcher/bench/run 类体与主线调试族对照）；[发布版接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)（`aggresive_autotune` 发布版 `benchmark_all_configs` 替换）。CostModel/Debug 两个子类体见[主线 costmodel/debug autotuner 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)；符号分组的代表/预算纯函数见[主线 grouped meta 构造卡](torch_npu_main_inductor_grouped_meta_construction.md)。

## 失效边界与静态口径

- 本卡全部为两 pin 静态代码事实；`mspti_batch_benchmark` 来自 `..profiler`（`:101` import），其本体与 mspti 路径可用性未读未验证；`benchmarker.benchmark_gpu` 的 `device_type='npu'`/`is_vetted_benchmarking=True` 语义为上游接口，未读上游实现。
- 运行级收益、批量测量精度不在本卡证据范围；验收契约条目为测试文件静态阅读，未运行测试，断言通过与否依赖 torch 版本与设备。

## Evidence

- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（primary；读窗 `:731-830`、`:988-1130`、`:1416-1815`、`:1986-2019`、`:3651-3727`、`:4130-4160`）
- [发布版 npu_triton_heuristics.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py)（implementation；`bench` 对照 `:655-677`、`NPUDebugAutotuner` 对照锚 `:1005-1040`）
- [主线 config.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（implementation；`aggresive_autotune` `:373-376`、`autotune_continue_on_failure` `:438`）
- [test_autotune_switch.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_switch.py)（evidence；全文 531 行静态阅读，选择断言见『验收契约』节）
