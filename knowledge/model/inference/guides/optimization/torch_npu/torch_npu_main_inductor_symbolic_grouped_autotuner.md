---
type: Guide
title: torch_npu 主线 NPUSymbolicGroupedAutotuner：逐组调优、运行期组解析与 cpp wrapper 落盘
description: 记录主线 runtime/triton_heuristics.py 的分组运行期消费类 NPUSymbolicGroupedAutotuner：候选计划来自 inductor_meta 注入、按 bucketize radix 解析运行期 group_id、代表形状物化 benchmark 参数（含规约 kernel 的整数区间采样）、逐组筛选与三路测量链、_record_grouped_cpp_wrapper_plan 的 variant load_meta 落盘；及其与 cpp_wrapper_npu.py 的 plan 消费锚。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/cpp_wrapper_npu.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/symbolic_grouping.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_switch.py
  role: evidence
created_at: '2026-11-12T13:18:38Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 `NPUSymbolicGroupedAutotuner`：逐组调优、运行期组解析与 cpp wrapper 落盘

## 固定版本与适用范围

主线 pin（ac0e1564）`runtime/triton_heuristics.py` 的分组运行期消费类 `NPUSymbolicGroupedAutotuner`（`:2430-3163`，733 行）：候选计划来自 inductor_meta 注入、按 bucketize radix 解析运行期 group_id、代表形状物化 benchmark 参数（含规约 kernel 的整数区间采样）、逐组筛选与三路测量链、`_record_grouped_cpp_wrapper_plan` 的 variant load_meta 落盘，及其与 cpp_wrapper_npu.py 的 plan 消费锚。决策树 row 3 选点见[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)；计划构造侧（`_triton_config_npu_index_grouped`/`build_grouped_launch_policy`/`resolve_grouped_runtime_block`）由[分组配置卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)持有；构造期代表/桶语义由[分组构造卡](torch_npu_main_inductor_grouped_meta_construction.md)持有；`_measure_prerun_ms`/`_select_prerun_top_candidates` 的候选路径调用族见[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)；`bucketize`/`find_primary_feature_index`/`is_open_bucket_group`（symbolic_grouping.py `:139-196`）本卡只引用不重写。发布 pin（f3ecfe4a）无此类与 `grouped_candidate_plan`（全树 rg 零命中，负证据，含 test/）；`test/_inductor/test_autotune_switch.py` 的类外契约见『验收契约』节，`test_inductor_dynamic_shapes.py` 由[动态形状分组测试卡](torch_npu_main_inductor_dynamic_shapes_grouping_tests.md)持有。纯静态阅读；draft、platforms 为空。

## 计划注入与状态（`__init__` `:2431-2475`）

不本地构造计划：`candidate_plan = inductor_meta["grouped_candidate_plan"]`（`:2462`），`_build_candidate_plan` 覆写直接返回它（`:2474-2475`，屏蔽基类重建）。`reachable_selection_keys` 取计划的 `reachable_group_ids`，缺失时回退 `range(group_id_count)`（`:2463-2468`）。逐组胜者状态 `best_candidate_map`/`best_launcher_map` 以 group_id 为键——与基类单胜者 `best_candidate_config`/`best_launcher` 并存但互不读写（`:3131-3133` 注释原义：分组复用同一套 keyed winner cache，按 group_id 索引）。

## cpp wrapper 落盘（`:2477-2560`）

- `_grouped_variant_load_meta`（静态，`:2477-2527`）：launcher 无 `bin`/`bin.asm` 直接 raise；`cubin_path` 缺失时把 `npubin` 二进制经 `write()` 落到 `split_aot_inductor_output_path(config.aot_inductor.output_path)[0]`（再缺 raise）。返回 13 键元数据：`mangled_name`/`shared_mem`（`bin.shared` 或 `metadata.shared` 两形态）、`mix_mode`/`parallel_mode`/`is_pure_simt`、`shared_mem_dynamic_size`/`has_auto_blockify_blacklist_op`/`lock_init_val`/`workspace_size`（`getattr` 缺省 0/False/0/0）、`lock_num`/`sync_block_lock_layout`（经 `_get_sync_block_lock_*` helper，见[Grid/launcher 卡](torch_npu_main_inductor_grid_and_launcher_generation.md)）、`auto_tile_and_bind_subblock`、`cubin_path`。
- `_record_grouped_cpp_wrapper_plan`（`:2529-2556`）：每个可达组必须有胜者（缺则 raise「missing winner for group」）；`best_by_group[str(group_id)] = {variant_id, policy_id}`；入选变体逐个从 `variant_launcher_map` 取 launcher（缺 raise）并写 `plan["variants"][variant_id]["load_meta"]`；最终写 `plan["best_by_group"]`。`save_npu_kernel` 覆写（`:2558-2560`）先记录再调基类——cpp 侧消费锚：`cpp_wrapper_npu.py:113/257/319/389/424` 读取 `grouped_candidate_plan` 并在生成代码里 emit C++ 版 `resolve_grouped_runtime_block`（定向 rg 锚，cpp_wrapper 文件主体未读）。

## 逐组选择与预编译（`:2562-2606`）

- `_pick_first_compiled_candidate_per_group`（`:2566-2590`）：每个可达组取**首个已编译且 runnable** 的 candidate（免测路径，确定性跳过时使用）；某组一个都没有 → raise。
- `_precompile_variants`（`:2592-2606`）：`_grouped_variant_launchers_initialized` 标志 + `self.lock` 双检锁；launchers 为空时 `_precompile_worker()` + `_make_launchers()`（耗时写 `precompile_time_taken_ns`），否则 `_refresh_variant_launchers()`；只执行一次。

## 运行期组解析（`:2608-2702`）

- `_runtime_feature_inputs`（`:2608-2633`）：按计划 `feature_arg_indices` 从运行参数取值；`outer_product`/`reduction_product` 源连乘，其余源要求恰好一值（否则 raise）。
- `_resolve_group_id`（`:2635-2652`）：`group_id = Σ bucketize(value, buckets) × stride`，`stride` 逐特征乘 `len(buckets)+1`（radix 混合编码，与构造期 `representative_for_group` 解码同基数；逻辑与 symbolic_grouping 的 `make_group_id`（`:146-161`）等价但**就地内联**、未调用该函数，另加 `group_id >= group_id_count` 越界 raise）。`bucketize` 本身接受 `value == upper` 落入闭桶（`:139-143` 字面 `value <= upper`），与构造期 `(lower, upper]` 正区间一致。运行参数解析到**不可达组**时 `run` 直接 raise「unreachable grouped autotune group」（`:3134-3137`）——运行期不静默回退。
- `_materialize_runtime_blocks`（`:2654-2699`）：**V1 只支持一条 runtime block 规则**且必须指向主轴 `{AXIS}BLOCK`（`inductor_meta["primary_group_axis"]` 存在时强校验，违反 raise）；规则 op 只接受 `ceildiv`；块值经 `resolve_grouped_runtime_block(axis_numel, expected_grid=grid_target, block_sub, representative_numel, max_grid)` 计算（数学见[分组配置卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)）；`runtime_block_append_order` 中缺值 → raise。`_diagnostic_runtime_blocks` 委托同函数（`:2701-2702`）。

## 代表形状 benchmark 参数物化（`:2704-2877`）

`_materialize_benchmark_args(group_id)`（`:2716-2877`）按计划 `benchmark_axis_values_by_group` 建 `axis_env`，逐 spec 物化：

| spec 形态 | 动作 | 边界 |
| --- | --- | --- |
| `runtime_arg` | 直接取 `_grouped_runtime_args_snapshot[index]`（越界 raise） | 快照只在 `_autotune_all_groups` 期间非空（`:3057` 赋值、`:3107` finally 清空） |
| `axis_expr` | `eval_expr` 小语言：const / **runtime_arg_index** / axis_name / mul / add / floordiv（二元） | 与 codegen 侧 `evaluate_grouped_benchmark_expr`（symbolic_grouping `:357-399`）不同，**此处在运行期允许 `runtime_arg_index`**（codegen 侧显式 raise「不可界」，见[分组构造卡](torch_npu_main_inductor_grouped_meta_construction.md)），同一表达式负载两个消费端语义不同 |
| tensor（buffer/constant） | `rand_strided(size, stride, dtype, device)`（可被 `_benchmark_tensor_factory` 属性覆写，`:2853-2855`） | dtype 经 `"torch.X"` 字符串 `getattr(torch, ...)` 解析（`:2774-2778`） |
| workspace | `workspace_factory`：`ZERO_ON_CALL` → `torch.zeros`，否则 `torch.empty`（`:2780-2785`，可被 `_benchmark_workspace_factory` 覆写） | count 经 `eval_expr` |

**整数区间采样**（`:2787-2835`，本类独有）：`integer_benchmark_range` 仅对 `REDUCTION`/`PERSISTENT_REDUCTION` 启用；取快照中真实参数（须为非空、非浮点、非 bool 的整数 Tensor）的 `(min, max)`。docstring 原义：`rand_strided` 对整数张量零填充，间接 load 全部落到同一元素、gather 零成本——按全零索引调优会把「能处理散射行」与「不能」的候选排成同档；采样真实参数张成的区间恢复区分度，且真实发射已用这些值索引故不会越界。`fill_integer_range`（`:2817-2835`）：夹到 dtype 极值；上界已达 `iinfo.max` 时（int64 哨兵值场景）放弃 +1 的排他上界、少抽这一个值（注释原义），区间空则 `fill_(low)`。整数 tensor 物化后立即回填（`:2857-2860`）。

## 逐组测量（`:2879-3054`）

- `_build_grouped_benchmark_entries`（`:2879-2908`）：每个有 candidate 的组**物化一次** benchmark args；组内每个 runnable launcher 的 candidate 生成 entry（runtime_blocks + launch_args 预先算好）。
- `_benchmark_grouped_entries`（`:2913-2984`）：spill 门（非 custom 且 `n_spills > inductor_meta["spill_threshold"]` 缺省 16）→ `inf`；其余进 `kernel_call` 闭包（pre_hook 合并参数字典 → `clone_args(launch_args)` → `reset_to_zero_args(kernel_args_prefix)` → 发射克隆；`kernel_args_prefix = launch_args[:len(fn.arg_names)]` `:2910-2911`——置零作用于 kernel 参数前缀而非全部发射参数）。测量链：`_benchmark_kernel_funcs_batch(kernel_funcs, "grouped")` 批量（mspti→profiler，见[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)）→ 批量为 None 时先 `_screen_grouped_entries` 再对幸存者逐个 `_bench_with_launch_args`。
- `_screen_grouped_entries`（`:2990-3054`）：**仅 REDUCTION/PERSISTENT_REDUCTION 且候选数 > `_GROUPED_SCREEN_MIN_CANDIDATES=200`（`:2988`）**才执行；每个候选单发计时 `_measure_prerun_ms`，异常按 `autotune_continue_on_failure` 分流（inf 或 raise）；**每组独立**取 `_select_prerun_top_candidates` 幸存者（min_k 10/max_k 200/50ms，与候选路径同一对文件尾 helper）；被筛掉的候选保留单发计时作为最终 timing（docstring 原义：反正不可能是组内胜者，单发排序够公平；胜者仍由完整测量决定）。注释原义：分组 reduction 按桶代表而非真实形状测量，候选池大一个数量级且含循环数在代表长度下爆炸的配置——把注定输的候选测到全精度只量化输得多惨。

## 顶层流程（`:3056-3162`）

| 门槛/阶段 | 动作 | 失败/边界 |
| --- | --- | --- |
| `_autotune_all_groups`（`:3056-3107`） | 快照 args → 建 entries → 可达组缺 entries → raise；测量；每组取最小 timing 胜者；可达组无胜者 → raise；finally 清快照 | timing 数与 entries 数不符 → raise |
| `ensure_grouped_autotune_ready`（`:3115-3123`） | `_precompile_variants`；锁内检查 `_all_reachable_groups_tuned`（`:3109-3113`，所有可达组都有 launcher）早退；确定性跳过 → `_pick_first_compiled_candidate_per_group("deterministic")`；否则 `_autotune_all_groups` | 确定性路径免测但仍逐组要求可编译 |
| `run`（`:3125-3162`） | ensure ready → 特征值 → group_id → 查 `best_*_map`（缺则 raise unreachable）→ `_materialize_runtime_blocks`（按**真实** args）→ log dispatch → `store_cubin` 且（非 benchmark_run 或未存过）时 `save_gpu_kernel` → `launcher(*launch_args, stream, **kwargs)` | 不走基类 `autotuner()`；`launchers` 单元素等基类捷径在此不存在 |

## 分组调度验收契约（test_autotune_switch.py）

`test/_inductor/test_autotune_switch.py` 的 `_grouped_autotuner` 系列（静态阅读，未运行；测试用 `object.__new__` 构造半实例并 mock `_autotune_all_groups`，钉的是**类外接口契约**）钉死 `ensure_grouped_autotune_ready`：

- max 全关仍 `_autotune_all_groups`——分组调优不受 max-autotune 旗标影响。
- 确定性 reduction **每组取第一个 runnable 候选**（跳过 `runnable=False` 的候选）、空组不进 `best_candidate_map`、`reachable_selection_keys` 之外的组不出现。
- 确定性 pointwise 仍逐组 benchmark。

## 失效边界与静态口径

- 本卡全部结论来自两 pin 静态阅读；未运行任何分组调优、代表物化或 profiler 路径。`_benchmark_tensor_factory`/`_benchmark_workspace_factory` 在主线全树仅有 `hasattr`/`getattr` 消费点（`:2781-2782`/`:2853`），无任何赋值处（含 test/）——按预留扩展点静态记录。
- `run` 的组解析依赖运行参数与 `{axis}_numel` 签名的一致性；真实参数落入构造期判定的不可达组时行为是 raise 而非回退，本卡未验证上层调用方的捕获策略。
- `cpp_wrapper_npu.py` 主体只按消费锚登记（`:113/:257/:319/:389/:424`）；`_triton_config_npu_index_legacy` 主体由[legacy 候选生成卡](torch_npu_main_inductor_legacy_config_and_decorator_entries.md)持有；`test_inductor_dynamic_shapes.py` 契约由[动态形状分组测试卡](torch_npu_main_inductor_dynamic_shapes_grouping_tests.md)持有。
- 与[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)的边界：其 row 3 行只持选点与门链概述，类体语义以本卡为准；`bucketize`/`find_primary_feature_index`/`is_open_bucket_group` 语义以 symbolic_grouping 实现窗口为准。

## Evidence

- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（primary；类体 `:2430-3163` 全读，`_GROUPED_SCREEN_MIN_CANDIDATES` `:2988`）
- [主线 codegen/cpp_wrapper_npu.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/cpp_wrapper_npu.py)（implementation；rg 消费锚 `:113`/`:257`/`:319`/`:389`/`:424`，文件主体未读）
- [主线 runtime/symbolic_grouping.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/symbolic_grouping.py)（implementation；`bucketize` `:139-143`、`make_group_id`/`decode_group_bucket_indices` `:146-174`、`find_primary_feature_index` `:176-184`、`is_open_bucket_group` `:186-196` 引用自 symbolic_grouping 实现窗口）
- [test_autotune_switch.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_switch.py)（evidence；全文 531 行静态阅读，分组契约断言见『验收契约』节）
