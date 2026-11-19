---
type: Guide
title: torch_npu Inductor runtime 缓存 autotune 补丁链与 FASTAUTOTUNE 调优
description: 记录主线 _inductor/runtime/ 运行时补丁包的安装链、cached_autotune 决策树、FASTAUTOTUNE（Expert/SampleStack）调优算法本体、tile 生成与符号分组门链，及与发布版扁平实现的接线差异。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/autotune_cache.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/runtime_utils.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/fasta_autotune.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/symbolic_grouping.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/tile_generator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_helpers.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/split_tiling.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/runtime.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_switch.py
  role: evidence
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_symbolic_grouping.py
  role: evidence
created_at: '2026-11-12T06:50:18Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu Inductor runtime 缓存 autotune 补丁链与 FASTAUTOTUNE 调优

## 固定版本与适用范围

`torch_npu/_inductor/runtime/` 是主线 pin（ac0e1564）独有的运行时补丁包，8 个文件共 7179 行（wc -l 实测：`__init__.py` 8、`autotune_cache.py` 35、`fasta_autotune.py` 1666、`runtime_utils.py` 27、`symbolic_grouping.py` 590、`tile_generator.py` 574、`triton_helpers.py` 119、`triton_heuristics.py` 4160）。发布 pin（f3ecfe4a）`torch_npu/_inductor/` 下无 `runtime/` 目录，全 pin `find` 仅命中扁平 `runtime.py`（70 行）与 `codegen/tile_generator.py`（253 行，非本包文件），`fasta_autotune`/`symbolic_grouping`/`autotune_cache`/`triton_heuristics` 同名文件零命中——发布版接线见『发布版差异』与[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)。本链被 Triton 后端（`_load_triton_backend`）与 DVM 后端（`_load_dvm_backend`，仅 `has_triton` 时）共用；`triton_experimental` 物理隔离树不走本链（其 loader 无本函数调用）。本卡为两 pin 源码静态阅读：未执行任何编译、autotune 或设备路径；draft、platforms 为空。

## 安装链：`_apply_common_npu_triton_patches`

入口在 `torch_npu/_inductor/__init__.py:99-114`，两个调用点：`_load_triton_backend`（`:277`）与 `_load_dvm_backend`（`:176`）。函数体安装的补丁：

| 实际门槛 | 动作（替换了什么） | 失败/版本边界 |
| --- | --- | --- |
| 后端加载即调用，无独立开关 | `patch_triton_config_to_hashable()`：把 `torch._inductor.runtime.{runtime_utils, coordinate_descent_tuner, triton_heuristics}` 三个模块的 `triton_config_to_hashable` 绑定整体替换为递归冻结版本（嵌套 list/tuple 先转为 tuple 再入哈希键），`runtime_utils.py:1-27` 全文 | 只重绑这三个模块的模块级名字；其他直接 `from ... import triton_config_to_hashable` 的调用方不受影响（静态口径） |
| 同上 | `patch_triton_heuristics_cached_autotune()`：`torch._inductor.runtime.triton_heuristics.cached_autotune = 本仓 cached_autotune`（`triton_heuristics.py:3375-3376`） | 替换的是 torch 模块属性；已经持有旧函数引用的调用方不会被改（Python 属性替换的一般限制，静态记录） |
| 同上 | `patch_load_cached_autotuning()`：`torch._inductor.runtime.autotune_cache._load_cached_autotuning = 本仓实现`（`autotune_cache.py:32-35`） | 见下节缓存语义 |
| 同上 | 另附 `patch_create_device_properties()`（来自 `_compat/inductor.py`）、`patch_algorithm_selector()`（`select_algorithm.py`）、`patch_tuning_process()`（`autotune_process.py`） | 这三件不在本卡逐行范围；`patch_tuning_process` 的 extern/Catlass 测量面见[Catlass binary cache 卡](torch_npu_catlass_binary_cache_and_loading.md) |

`runtime/__init__.py`（8 行全文）只 re-export `patch_load_cached_autotuning`、`patch_triton_config_to_hashable`、`patch_triton_heuristics_cached_autotune` 与 `triton_helpers` 星号导入；`triton_helpers.py`（119 行）是 `@triton.jit` 数学辅助库（frexp、带索引极值、welford 等），供生成代码引用，无补丁语义。

## `cached_autotune` 决策树

本仓 `cached_autotune`（`triton_heuristics.py:3236-3373`）是 triton.autotune 的替代实现，先走 `AutotuneCache.create(...).read_best(...)` 的盘上缓存命中（命中则候选收缩为单个 best_config），再在 decorator 里按序选 autotuner 类：

| 顺序 | 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- | --- |
| 1 | `inductor_meta["profile_bandwidth"]` | 返回 `NPUDebugAutotuner` | 调试路径，类体见[costmodel/debug autotuner 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md) |
| 2 | `_use_fasta_autotune`：`npu_config.fasta_autotune` 且 `group_enabled` 为假 且 非（reduction 且 deterministic 标志为真） | 返回 `NPUFastAutotuner`（fasta_autotune.py） | FASTAUTOTUNE 与上游 max-autotune 开关互相独立（函数注释原义）；分组 kernel 与确定性 reduction 被显式排除，选点收缩回标准 tuner |
| 3 | `group_enabled` | 返回 `NPUSymbolicGroupedAutotuner` | 类体见[分组 autotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md) |
| 4 | 否则 | `enable_costmodel_prefilter`（`INDUCTOR_ASCEND_ENABLE_COSTMODEL`，默认 False）为真选 `NPUCostModelAutotuner`，否则 `NPUCachingAutotuner` | 类体分别见[costmodel/debug autotuner 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)与[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md) |

装饰器入口 `pointwise/reduction/persistent_reduction/template/foreach`（`triton_heuristics.py:3999/4019/4050/4078/4107`，入口参数与门槛见[legacy 候选生成卡](torch_npu_main_inductor_legacy_config_and_decorator_entries.md)）与 `_triton_config_npu_index_legacy` 都会落到这棵决策树：后者的 fasta 连接行 `:3915-3916`（`_use_fasta_autotune(...)` 为真时 `from .fasta_autotune import FastATileGenerator`），主体见[legacy 候选生成卡](torch_npu_main_inductor_legacy_config_and_decorator_entries.md)。

## 缓存命中路径 `_load_cached_autotuning`

`autotune_cache.py`（35 行全文）：`best_config` 为 `None`、或 `best_config.pop("configs_hash", None)` 与当前候选哈希不一致时返回 `None`（继续正常 autotune）——`configs_hash` 键在比较前即被 pop，失配时该键也已被从入参字典消费掉，不暗示失配路径原样保留输入；一致时按上游缓存写入方的约定继续原位消费 `time_taken_ms`/`triton_cache_hash`/`found_by_coordesc`/`extra_options` 键，用 `torch._inductor.runtime.autotune_cache._reconstruct_triton_config` 重建 Config，并强制 `triton_config.found_by_coordesc = True`——源码注释原义是“命中缓存的赢家跳过后续 coordinate descent”。即：缓存命中不只省测量，还改变了后续 coordesc 搜索是否发生的语义。

## FASTAUTOTUNE 算法本体（`fasta_autotune.py`）

`FastASetting` 是模块导入期构造的单例（`FASTA_SETTING = FastASetting()`，`fasta_autotune.py:132`）：env 值在 import 时被冻结；非法方法名分支的日志文本写“use SampleStack method instead”但代码实际赋值 `self.autotune_method = "Expert"`（`:94-97`，日志与动作不一致的源码事实）；默认超参：bucket 容量 10、SampleStack 轮数上限 `autotuner_max_find_times=3`、bucket 内最大查找 2、容差 `tolerance_rate=0.05`、Expert 最小 bucket 数 5、`expert_find_ub_right_index=3`、`kernel_no_fastA` 黑名单默认空、`re_profiling` 默认关。模块级 `get_ub_size()` 按 `npu_config.is_ascend950` 返回 256，否则 192（`:135-141`；其返回值进入 `FastAConfig` 的 UB 口径，与 config 侧 `ub_size`（192/256*1024 字节）同为 SoC 分档，两者标度对应关系未在源码中核对）。

`NPUFastAutotuner.__init__`（`:841-927`）的退出门（满足任一则 `use_origin_autotuner=True`，回退父类 `NPUCachingAutotuner.autotuner` 并把候选置为 expert 部分）：候选总数为 1；分离后 origin 候选 ≤1 或最终 configs 为 1；kernel 名命中黑名单（默认空表，等价不触发）；`NPUKernelType(inductor_meta.get("npu_kernel_type","simd")) != SIMD`——fasta 只服务 SIMD kernel，SIMT/SIMT 混合不参与。

| 方法 | 实际门槛 | 动作/分配 | 失败/版本边界 |
| --- | --- | --- | --- |
| Expert（`AUTOTUNE_METHOD` 默认） | init 期即构造（`_precompile_for_expert`） | `_make_bucket_and_filter_with_binary`：按 `vector_core_num` 从 `num_vector_core` 降到 1 分桶，桶内按 `ub_usage` 升序；每桶先试编译最大 UB 候选，失败时从异常文本解析 `requires (\d+) bits while (\d+) bits` 计算 `ub_times=max(max_req/(ub_size*元素字节*8),1)`、阈值 `1/ub_times` 后 bisect 收缩右界；Expert 再把参与桶收缩到 `_expert_method_get_choose_core_num_list`（优先取“无 UB 过滤可用”的核数段，不足 5 个补最大核数前 5），每桶再向下探 3 个候选确认；随后二分循环收敛每桶最大可用 UB（轮数上限 `find_bucket_max_ub_max_times`，默认 `inf`）。每桶产出 `NPUFastABucket(config_list[:find_ub_index+1])` | 解析不出位宽需求时保守取桶尾；任何一步没有可用候选的桶被丢弃并记 warning。多轮编译试错本身就是该算法的成本模型，静态口径下不比较总耗时 |
| Expert 候选组装 | 桶构造完成 | `_expert_configs_precompile`：expert 候选 + 每个入选桶 `get_configs_in_bucket_expert(get_circle_num=tiling_axis数)`（按 circle_num 升序取前若干档）+ `add_mutibuffer_config` 把每个候选复制出 `multibuffer=True/False` 两份（候选数翻倍）后统一 precompile | `precompile_thread_num` 决定并行度（`TORCHNPU_PRECOMPILE_THREADS`，config 侧解析失败直接 `sys.exit(1)`） |
| Expert 测量 | 首次 `autotuner()` 调用 | `auto_tune_by_fasta_parallel` → `benchmark_all_configs_with_std`（批量 profiler 测量，含 sem/std 三元组；批量路径异常时逐个 `bench_event` 兜底，单事件计时 warmup 1 次/重复 2 次取均值）→ `find_best_launcher` 取 `profiler_time` 最小者，并把 `bucket_score` 按“核数距最优核数”重排 | spill 超阈值的 launcher 计为 inf；`make_profile_values` 无有效值时抛 `ValueError("no valid profile data")`；此后 `best_launcher` 被缓存，后续调用直接复用并把调优总耗时（ns）写 `save_cache_hook` |
| SampleStack | `AUTOTUNE_METHOD=SampleStack`；`__init__.py:394-404` 在 `compile_threads != 1` 时强制降为 1 | 桶构造延迟到首次调用；循环（≤3 轮）内 `dynamic_generate_config_parallel` 以当前最优 `ub_usage` 为参照从各桶动态取候选（容量受 `precompile_thread_num` 限制），同样 multibuffer 翻倍、precompile、批量测量、`dispatch_profile_value` 回填桶 | 桶内部：目标 UB 采样点 `[0.5,0.6,0.8,0.9,1.0]×ub_max`；单轮有效样本 <3 即止桶；方向窗口中已测比例 >0.5 即止桶；`_is_all_bucket_end` 还要求最优核数的相邻 2 个核都更差才结束；全失败返回 None 时回退父类 autotuner |

`__init__.py:385-392`：`FASTAUTOTUNE=1` 时若 `ENABLE_PRINT_UB_BITS` 非"1"会打日志并设为"1"（源码注释原义：fasta 需要真实 UB 用量）。注意该分支首行调用的 `log.warnings(...)` 方法名不属于标准库 `logging.Logger` 接口——与[配置解析卡](torch_npu_inductor_config_parsing.md)已记录的“log.warnings 拼写”一致；静态上不能断言该分支一定能完成 env 设置，默认 `FASTAUTOTUNE=0` 时不进入该分支。

## tile 生成（`runtime/tile_generator.py`）

`TileGenerator.__init__`（`:109-163`）的预算常量：`local_mem_size = 128KB`（仅 `SIMT_ONLY`）否则 `config.ub_size`（SoC 判定 192/256KB）；`max_numel_threshold = local_mem_size // min(input_ptr_num,3) // dtype_bytes`；`stop_numel = min(max_numel_threshold, max_total_numel//num_vector_core)//8`；`tiny_kernel = max_total_numel < 128*1024`（元素口径）；`program_threshold` 取 `num_vector_core//8`（tiny 且非 SIMT_ONLY）或 `//2`，再被 `max_total_numel//128-1` 夹紧、下限 0。候选块沿 tiling/split 轴递减生成（`descend_tiling_axis`/`descend_split_axis_inner`/`descend_all_low_dims`），下降算法与预算常量见[TileGenerator 下降卡](torch_npu_release_flat_inductor_tile_generator_descents.md)，`ub_overflow_retry_configs` 提供溢出重试。`triton_heuristics` 顶层导入 `TileGenerator, ub_overflow_retry_configs`（`:92-93`），`fasta_autotune` 以 `FastATileGenerator(TileGenerator)` 继承并覆写 `descend_split_tiling`；候选的 `from_expert` 标志被 `_config_separation` 用于分流 expert/origin 两侧（赋值点：`:153` 构造缺省 False、`:419` expert 复制时 True、`:496` 非 expert 桶 False，见『FASTA 数据模型』节）。`npu_config.num_vector_core` 经 config 的惰性 `__getattr__` 从设备属性（或 `NPU_DEVICE_LIMIT`）解析。

## 符号分组 autotune 门链（`symbolic_grouping.py`）

| 实际门槛 | 动作/分配 | 失败/版本边界 |
| --- | --- | --- |
| `INDUCTOR_ASCEND_SYMBOLIC_GROUP_AUTOTUNE`（默认 0）为真 且 模板名在 `INDUCTOR_ASCEND_SYMBOLIC_GROUP_TEMPLATES`（默认 `pointwise,reduction,persistent_reduction`；config 注释自述“临时 rollout 开关”） | `split_tiling.apply_group_rewrite_if_needed`（`split_tiling.py:325-339`）把 `_build_grouped_meta()` 构造的 `GroupedKernelMeta` 挂到 `kernel.grouped_autotune_meta`（构造体见[分组构造卡](torch_npu_main_inductor_grouped_meta_construction.md)） | 任一门不满足即置 None，走普通 autotune |
| codegen 侧 | `codegen/triton.py:1992-2011` 把 `grouped_meta` 展开 进 `inductor_meta`（`group_enabled` 等 8 个键）；`:2476` `_disable_grouped_autotune_if_unsupported` 用 `build_group_representatives` 试构造代表形状，抛 `UnsupportedGroupedPlan`（如同一轴出现在多个 group feature、空 buckets）即整体禁用分组 | 动态形状轴（sympy 非 Integer）参与时由 `split_tiling` 侧原则与 `_disable_grouped_autotune_if_unsupported` 收缩 |
| 基准显存预算 | `:2486-2496` `_disable_grouped_autotune_if_benchmark_too_large`：`estimate_grouped_benchmark_footprint`（synthetic 张量字节 + 被修改参数克隆字节，按组评估、取最大克隆）与 `total_memory × INDUCTOR_ASCEND_SYMBOLIC_GROUP_MAX_BENCHMARK_MEMORY_RATIO`（默认 0.25）比较，超预算即禁用分组并记录 dominant 参数 | `total_memory<=0` 或属性缺失按“footprint 不可界定”禁用；被禁用后若开启符号分组则记录 `enable_auto_blockify=True` 的 legacy 回退请求（`:2196-2210`） |
| runtime 侧 | `group_enabled` 时 `cached_autotune` 决策树选 `NPUSymbolicGroupedAutotuner`：按运行期特征值 `bucketize`（`symbolic_grouping.py:139-176`，radix 混合编码为 group_id）解析组、逐组挑选 launcher、`_screen_grouped_entries` 筛选（类体见[分组 autotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)） | 与 fasta 互斥（决策树顺序）；`GroupedKernelMeta`/`GroupFeatureSpec` 为 frozen dataclass，`from_payload`（`:85-111`）按 `payload.get` 读取已知字段并用 `_require_*` 辅助校验值与类型——该函数不拒绝未知键，键集合不受严格白名单约束 |

`codegen/split_tiling.py:15` 与 `codegen/triton.py:81-84` 是这两个包对 `runtime/symbolic_grouping` 的导入点。

## 测试验收契约（分派序、安装面与分组预算守门）

以下契约来自 `test/_inductor/test_autotune_switch.py`（531 行）与 `test/_inductor/test_symbolic_grouping.py`（306 行）的静态阅读（未运行；通过与否依赖 torch 版本、设备与 `runIfVersion` 门）：

- **import 无损**（`test_backend_import_preserves_upstream_max_flags`）：子进程 4 组旗标组合下，import `torch_npu._inductor` 后上游 `config.max_autotune/max_autotune_pointwise` 值不被覆盖——安装链的补丁不吞掉上游 max-autotune 配置。
- **分派序**（最后两测）：`cached_autotune(caching_autotuner_cls=...)` 显式类**优先于** fasta 与分组（三类 tuner mock 全不被调）；无显式类时 `group_enabled` → 分组，否则 fasta（除非确定性 reduction 退 basic）——即决策树 row 2/3/4 顺序的测试面；`_use_fasta_autotune` 独立于 max 旗标、分组恒排除、确定性只对 reduction 排除。
- **预算守门**（`test_symbolic_grouping.py:188-241`）：超预算 → `group_enabled=False` 且 `group_template=None`；**边界含等号**：`total_memory = footprint.total_bytes × 4`（ratio 0.25）时仍放行；被拒且开分组开关时记录 legacy 回退 `enable_auto_blockify=True`。
- **footprint 口径**（`:64-111`）：`group_bytes` 按组分列、`synthetic_bytes` 求和、**只按一个被修改参数的克隆峰值**计 `mutated_clone_bytes`、`dominant_arg` 指最大张量（数值为 fp16 具体期望）——与门链『基准显存预算』行的“按组评估、取最大克隆”互证。
- **端到端**（`:244-300`）：200×69876 fp16 宽后备存储 + 单动态轴：`torch.compile` 产物源码里必须含 `'group_enabled': False` 与 `'enable_auto_blockify': True`，且数值与 eager 一致（唯一设备级用例，静态记录其断言内容，未运行）。

## 发布版差异（release pin f3ecfe4a）

- 发布版无 `runtime/` 包（`find torch_npu -name runtime -type d` 零命中；`ls _inductor/runtime` 报不存在）。对应行为在扁平文件：`_inductor/runtime.py`（70 行）内的 `_load_cached_autotuning` 是旧版覆盖——只 pop `time_taken_ms/num_warps/num_stages`，直接 `Config(best_config, ...)` 重建并置 `found_by_coordesc=True`，无 `_reconstruct_triton_config` 与 `triton_cache_hash`/`extra_options` 消费；由发布版 `_inductor/__init__.py:126` 在默认后端分支无条件安装到 `torch._inductor.runtime.autotune_cache`。
- 发布版不替换 `torch._inductor.runtime.triton_heuristics.cached_autotune`（全 pin rg `cached_autotune` 只命中其自仓 `npu_triton_heuristics.py:1041` 定义与 5 个内部调用）；本仓 autotuner 经生成代码里的 `@npu_triton_heuristics.{heuristics}` 装饰器直接引用（见[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)）。
- FASTAUTOTUNE/`AUTOTUNE_METHOD`、symbolic grouping、runtime 版 `tile_generator`、`config_to_hashable` 补丁在发布 pin 全源 rg 零命中；发布版仅 `aggresive_autotune`（`INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE`）时替换 `CachingAutotuner.benchmark_all_configs` 并设 `TRITON_BENCH_METHOD=npu`。
- 因此：FASTAUTOTUNE 是主线独有路径；按版本核对时，发布版环境变量文档若提及 FASTAUTOTUNE，不能反推该算法存在（配置解析卡的默认值行仅对主线成立，其适用范围以本卡边界为准）。

## 失效边界与静态口径

- `FastASetting` 在 import 期冻结 env 与超参：进程内后改 env 不影响已创建的 tuner；同进程切换后端（`_load_backend` 每次 `restore_inductor_baseline`）不会重建该单例。
- 单候选 kernel、非 SIMD kernel、分组 kernel、确定性 reduction 均不进 fasta；这些场景的调优行为回到 `NPUCachingAutotuner`/`NPUCostModelAutotuner`/`NPUSymbolicGroupedAutotuner`，类体分别见[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)、[costmodel/debug 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)、[分组 autotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)。
- 本卡全部结论来自两 pin 静态阅读；未执行编译、未触发 autotune、未在设备上验证 UB 假设或 Expert/SampleStack 的实际收益。任何“更快/更省”的量化结论都不在本卡证据范围内。配置项默认值与解析细节见[配置解析卡](torch_npu_inductor_config_parsing.md)；Catlass 后端选择见[Catlass autotune 卡](torch_npu_inductor_catlass_autotune.md)。

## FASTA 数据模型、桶构造中段与批量测量细节（fasta_autotune.py :1-30、:143-505、:795-840、:1466-1524）

头部 imports（`:1-30`，含 `from ..profiler import simple_trace_handler`，见[主线 npu_compare 与 profiler 工具卡](torch_npu_main_inductor_npu_compare_and_profiler_tools.md)）、`FastAConfig`/`TileConfig` 数据模型（`:143-209`）、`FastATileGenerator` 桶构造中段（`:212-505`）、`BinaryBucket`/`ProfileValue`（`:795-839`）与批量测量中段（`:1466-1524`）：

| 对象 | 实际门槛/动作 | 边界 |
| --- | --- | --- |
| `FastAConfig(Config)`（`:143-166`） | 在 torch `Config` 上扩展 `num_vector_core/ub_size/ub_usage/vector_core_num/core_usage/from_expert/real_ub_size/circle_num`（后两者缺省 -1）；`add_core_ub_info` 算 `core_usage = vector_core_num / num_vector_core` | `from_expert` 全部赋值点：`:153` 构造缺省 False（baseline）、`:419` expert 复制时 True、`:496` 非 expert 桶 False |
| `TileConfig`（`:169-209`） | 纯数据对象：`cal_vector_core_num` = 各 split 轴 `ceil_divide(numel, block)` 之积（空集为 1）；`cal_ub_size` = 各 tiling 轴 sub_blocks 之积；`cal_circle_num` = 各轴 `ceil_divide(block, sub_block)` 之积；`generate_base_config` 把 block/sub_block 按轴名映射成 cfg 键（可带 deal_function） | 桶内升序/`ub_usage` 口径的底层计算即出自这两组乘积 |
| `FastATileGenerator.add_multibuffer`（`:224-230`） | 空操作：docstring 原义 "This function does not work within tilegen; its purpose is to reduce the number of configs and the compilation time of subsequent steps" | 与 `NPUFastAutotuner.add_mutibuffer_config`（`:942`，候选翻倍）是两个不同函数：前者在 tilegen 内禁用，后者在 tuner 组装期生效 |
| `get_block_and_sub_list`（`:245-304`） | 逐轴产 `[block, sub_block]` 候选表：非 tiling/split 轴 → `[1,1]`；persistent r 轴 → block==sub；split 轴按核数从 `start_core_num` 降步进枚举 `ceil(numel/core)` 去重降序；tiling 且非 no_loop 轴：`b>32` 时 sub 从 `min(aligned(b), start_ub)` 降到 `stop_ub`（步长 `sub_block_step`，persistent 再补逐 1 尾段），`b≤32` 降到 1 步 1 | `strict_aligned_numel`（`:306-311`）：对齐粒度 `32 // dtype_bytes`，小 numel 回 `next_power_of_2` |
| `cal_sub_blocks_with_circle_num`（`:313-326`） | 按 circle 数扫描候选 sub：保留与上一个入选值间距 ≥ `aligned_numel_num` 或 `< 32` 的取值，降序去重 | 供 `get_block_and_sub_list_ceil_divide` 的对齐轴使用 |
| `get_block_and_sub_list_ceil_divide`（`:328-390`） | 选一个对齐轴：r 轴 numel 可整除 `aligned_numel_num` 或无非 r 轴 → `r_axis[0]`，否则取最大非 r 轴；对齐轴的 stop_ub 与 sub 候选都过 strict 对齐 | Expert 桶构造走此变体（`descend_split_tiling` `:433-436`） |
| `descend_split_tiling`（`:395-503`） | `max_ub_size_byte = get_ub_size()*1024`（注释原义 A2:192kb A5:256kb）、`aligned_numel_num = 32 // dtype_bytes`。`FASTA_SETTING.use_tile_exp` 恒 True（`:53` 字面量），故 `:82` 的 `elif kernel_no_fastA` 分支在本模块内不可达（静态口径）。use_tile_exp 路径：SIMD_SIMT_MIX → 以 `set_kernel_type` 分 SIMT_ONLY/SIMT_TEMPLATE/SIMD 三遍 `old_descend_split_tiling`（= `super().descend_split_tiling`，`:242-243`）；每条 expert config 转 `FastAConfig(num_warps=1, num_stages=1)`、`from_expert=True`、`ub_usage = calculate_config_numel / max_ub_size_numel`、`core_num = calc_total_programs_by_config`。非 SIMD kernel 在 `:426-428` 早退（注释原义 "fasta do not support simt/simt_mix/simt_template"）；`axis_name` 空早退。Expert 方法 → ceil_divide 变体（core 从 num_vector_core 到 1 步 1、stop_ub=1）；非 tiny kernel 先窄窗（stop_ub=aligned(max×`aligned_numel_num/max_ub_size_numel`)、步长 aligned_numel_num），候选总数 ≤ `(num_vector_core - 1) × 3`（`min_avg_core_config_num`）再换全窗；tiny kernel 直接全窗。`itertools.product` 逐轴组合成 TileConfig，过滤 `vector_core_num ≤ num_vector_core 且 ub ≤ max_ub_size_numel`（`:478`），落选即丢弃；非 expert `FastAConfig` 记 `circle_num` | 桶容量 10、SampleStack 采样点等超参口径见上文『FASTAUTOTUNE 算法本体』，不重复 |
| `BinaryBucket`（`:795-829`） | 二分状态对象（left/right/mid）；`get_mid_config` 注释原义 "we want to find the last 1 in '11111100000'"——编译成功=1：成功 `left=mid+1` 且记 `result_index`，失败 `right=mid-1`；收敛后无结果 → `max(0, mid_index-1)` | Expert bisect 收缩右界的底层状态机 |
| `ProfileValue`（`:832-839`） | `@dataclasses.dataclass(order=True)`：`launcher`/`config` compare=False，`profiler_time/sem/std` 参与排序 | `find_best_launcher` 取 `profiler_time` 最小的排序载体 |
| 批量测量中段（`:1466-1524`） | `profiler_active_num=10`；`_ExperimentalConfig(l2_cache=False, data_simplification=False)`；`do_batch_benchmark_kernel_isolate`：`TOTAL_STEP = WAIT1+WARMUP1+ACTIVE+SKIP_FIRST1`，每个 kernel 的每步后 `torch.npu.synchronize()`；每个 kernel 的步循环前 `buffer.zero_()`（`l2_cache_size = 192*(1<<20)`，注释原义 "此处加入清L2的内容"——192MB int 缓冲）；profiler 会话不带 schedule；结果用 pandas 过滤 `Name` 以 `triton` 开头的行 | 前后文（`:841-1465`/`:1525-1666`）见上文各节；本段钉「逐 kernel 清 L2 + 逐步同步」的测量口径 |

发布版对照不变：发布 pin 全树 rg `FastAConfig|BinaryBucket|descend_split_tiling` 零命中，FASTAUTOTUNE 整链仍是主线独有（『发布版差异』节仍然有效）。
