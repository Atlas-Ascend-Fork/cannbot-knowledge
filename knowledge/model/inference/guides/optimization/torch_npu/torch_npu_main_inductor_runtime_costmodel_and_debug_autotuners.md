---
type: Guide
title: torch_npu 主线 NPUCostModelAutotuner 与 NPUDebugAutotuner：costmodel 预筛选管线与带宽调试路径
description: 记录主线 runtime/triton_heuristics.py 的两个决策类本体：NPUCostModelAutotuner 的 costmodel 预筛选管线（size_hints 兜底入参、TTIR 参数绑定构造、costmodel_bench 排序保留比例与空 ranking 保留原集、NoTritonConfigsError 回退编译）与 NPUDebugAutotuner 的带宽路径（benchmark_run 透传父类 run 形参、regex 名过滤、首测缓存与 select_algorithm isinstance 接线）；发布版对照与 costmodel 整体缺席负证据。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/select_algorithm.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_costmodel_autotuner.py
  role: evidence
created_at: '2026-11-12T12:38:02Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 NPUCostModelAutotuner 与 NPUDebugAutotuner：costmodel 预筛选管线与带宽调试路径

## 固定版本与适用范围

主线 pin（ac0e1564）`runtime/triton_heuristics.py` 两个决策类本体：`NPUCostModelAutotuner` `:2101-2429`、`NPUDebugAutotuner` `:3164-3217`，另定向读 precompile 挂钩上下文 `:830-853`、`:1054-1130` 与 `select_algorithm.py:290-315` 接线。选点（决策树 row 1 `profile_bandwidth` → `NPUDebugAutotuner`；row 4 `enable_costmodel_prefilter` → `NPUCostModelAutotuner`）由[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)持有。环境变量的文档契约（默认值、取值范围、发布页差异）由[CostModel 与分组指南](torch_npu_inductor_costmodel_and_shape_groups.md)持有，本卡只钉源码实现并做实现-文档对照，不重写文档承诺。发布 pin（f3ecfe4a）**无 costmodel 实现与两个类名之一**：全 pin 树 rg `NPUCostModelAutotuner|costmodel_bench|enable_costmodel_prefilter|costmodel_ratio` 零命中（负证据，含 torchnpugen/ 与 test/）；`NPUDebugAutotuner` 存在但是另一基类实现（见『发布版对照』）。纯静态阅读，未导入/运行/编译；draft、platforms 为空。

## `NPUCostModelAutotuner`（`:2101-2429`）：预筛选管线

### 挂钩与运行入参

`__init__`（`:2102-2135`）仅加三个状态位 `_costmodel_runtime_args/kwargs/fallback_configs`。基类 `_precompile_worker`（`:837-853`）经 `_prepare_precompile`（`:833-836`）调 **`_prepare_configs_for_precompile()` 覆写（`:2137-2142`）**：`_ensure_kernel_loaded()`（TTIR 重建需要 Python 函数，AsyncCompile pickling 会清掉它，注释原义）→ 解析运行入参 → `_apply_costmodel_to_configs`；随后基类才用**筛选后的** `self.configs` 构造 `candidate_plan`——预筛选发生在候选计划之前。运行入参来源：`autotuner()` 在 `len(launchers)==0` 时先 `_save_precompile_runtime_inputs(args, kwargs)`（`:1995`）再 precompile（`:1997`；覆写 `:2144-2146` 存入）；precompile 先于 run 时走 `_resolve_costmodel_runtime_inputs`（`:2183-2192`）→ `_build_costmodel_runtime_args_from_size_hints`（`:2148-2181`）：dict 直接入表；list/tuple 需 `inductor_meta["axis_names"]` 长度一致，同时写 `{axis}` 与 `{axis}_numel` 两键；随后按 `triton_meta["signature"]` 顺序遍历——`*_numel` 结尾的名字取 hint（缺失回退去尾名，再缺回退 1），其余签名项填**新建 `object()` 占位**（非整数，天然进不了绑定）。`_try_parse_int_like`（`:2194-2202`）：bool/int 直接 `int()`，其余 `int(value)` 截断转换，异常回 None（浮点按截断接受，静态记录）。

### TTIR 参数绑定（`:2204-2327`）

- `_build_ttir_arg_value_map`（`:2204-2259`）：正则 `tt\.func\s+public\s+@\w+\((.*?)\)\s+attributes`（re.S）截参数段，参数名正则 `%([A-Za-z_.$][\w.$-]*|arg\d+)\s*:`。注释原义：新版 Triton-Ascend 保留前端参数名（如 `%x0_numel`），旧版是 `%argN`；costmodel 的 `--arg-bindings` 是**按位置**的，故 TTIR 名优先匹配、位置序兜底。值来源优先级：保留名 → 签名序名 → 位置 `runtime_args`；`runtime_kwargs` 覆盖已有值；`cfg.kwargs` 只对签名内、且当前值非整数的项补值。
- `_build_costmodel_arg_bindings`（`:2261-2291`）：只绑定整数可解析项（`arg{id}={int}`，非整跳过）；恒附 `pid_x=0`；TTIR 含 `tt.get_num_programs x` 时才附 `num_programs_x`（`runtime_kwargs["num_programs_x"]` 或 `grid[0]`，均非整按 1）；整函数 try→`except Exception: return ""`。
- `_build_costmodel_items`（`:2293-2327`）：按 `build_candidate_plan` 变体复用同一 TTIR 文本（`ttir_text_by_variant` 缓存）；candidate 的 `runtime_blocks` 并入 kwargs 后再构造绑定；单项异常 → 该项空 ttir/绑定占位（`:2325-2326`）。

### 门链、执行与兜底（`_apply_costmodel_to_configs` `:2329-2383`）

按序短路（先序即事实）：`heuristic_type == USER_AUTOTUNE` → return；`configs<=1` → return；`enable_costmodel_prefilter` 假 → return；`costmodel_ratio <= 0.0 or >= 1.0` → return（实现层为字面比较、无 isfinite 校验：对普通有限浮点等价于开区间 (0,1)；NaN 两个比较均为 False 会放行，随后 `:2375` 的 `math.ceil(len(self.configs) × ratio)` 对 NaN 抛 ValueError，该行在 try 块之外，上层调用方处理未读，不作全局崩溃断言。配置层 `_parse_float_env`（config `:404-416`）同样只做 `<=0`/`>1` 字面比较、无 isfinite，解析失败或比较不通过时告警回默认 0.25）。通过后在 try 内 `from triton.backends.ascend.runtime.costmodel_runtime import costmodel_bench`（`:2346`，triton-ascend 侧包，本仓不读）；`npu_config.precompile_thread_num > 1` 且 items>1 时经模块级 `compile_thread_pool`（`:137-158`）并行提交，否则串行。**异常 → log.warning("Skip costmodel prefilter because costmodel path is unavailable") 后 return（原候选集保留）**；返回非 dict → return。排序：按预测耗时升序、剔除 `inf` 项得 `ranked_cfgs`；`target_count = max(1, ceil(len(self.configs) × ratio))`；不足时告警 `Config count filtered by costmodel is less than target count`；**`self.configs` 替换与落选集写入都在 `if ranked_cfgs:`（`:2378`）之内**——`selected_count = min(target_count, len(ranked))`、`self.configs = ranked[:selected]`、落选（有限耗时）存 `_costmodel_fallback_configs`。两点边界：预测为 inf 的候选不进兜底集（兜底只含「排上了但没入选」者）；**ranking 为空（全 inf 或 bench 映射为空）时 `if ranked_cfgs:` 不成立，原 `self.configs` 原样保留**（兜底位已被 `:2331` 置 None），并非全量丢弃。

### 编译失败兜底（`_precompile_with_costmodel_fallback` `:2385-2423`）

对当前（入选）configs 编译变体；`NoTritonConfigsError` 且有落选集 → log.warning 后用落选 configs 重建 plan 再编译（落选集此时成为 `self.configs`）；两级都失败 → 抛合并两者错误消息的 `NoTritonConfigsError`（`:2419-2423`）。基类分发 `_precompile_worker_with`（`:1058-1087`）：`type(self) is not NPUCachingAutotuner` 的子类（含本类与 grouped）**不走 UB 溢出重试**，直连 `_precompile_current_configs`（`:1071-1073`，注释原义）；覆写（`:2425-2427`）在 helper **正常返回后**清空 `_costmodel_fallback_configs`（无 finally）——两级编译都抛 `NoTritonConfigsError` 时异常直接上抛、不清空；且 `_apply_costmodel_to_configs` 入口（`:2331`）每次调用都先置 None，后续调用可重建。「兜底只吃一次」仅指单次 precompile 调用的正常路径，不是全局一次性保证。UB 重试旁路的测试证据见[precompile 管线卡](torch_npu_main_inductor_precompile_pipeline.md)验收契约（`test_costmodel_keeps_existing_fallback_without_ub_retry`）。

## `NPUDebugAutotuner`（`:3164-3217`）

基类是 **`NPUCostModelAutotuner`**（`:3164`）。`__init__`（`:3165-3180`）：`regex_filter`/`with_profiler`/`with_bandwidth_info` 三参在此消费、**不转发**给基类（注释原义：基类不接受；`with_bandwidth_info` 默认 True）。`run`（`:3182-3217`）：

| 门槛 | 动作 | 边界 |
| --- | --- | --- |
| `with_bandwidth_info=False` | `kwargs.setdefault("benchmark_run", True)` → `super().run(*args, stream=stream, **kwargs)` → return | 本类跳过的是**自己附加的**带宽 bench/打印；`benchmark_run` 未被本方法消费/pop，而是经 kwargs 命中父类 `run` 的显式形参（`:1900-1901`），父类 `:1927` 仍将其传入 `autotuner()`——父类的 autotune 测量照常可能发生 |
| `with_bandwidth_info=True`：名字解析 | `_find_names(self)` 取最长名；空则 `inductor_meta["kernel_name"]` 或 `fn.__name__`（`:3190-3194`） | 发布版无两级回退（对照见下） |
| `re.match(regex_filter, kernel_name)` 不匹配 | **直接 return，不执行 kernel**（`:3195-3196`） | 调试过滤器兼具跳过执行的作用，静态记录 |
| 匹配 | `super().run(...)`（`:3197`）→ `(launcher,) = self.launchers`（`:3198`） | launchers 非恰好 1 个会解包失败；上层决策树 row 1 装点即此路径 |
| 首次 | `bench(launcher, *args, with_profiler=self.with_profiler)`（`:3200-3201`）；数 `in_out_ptr` 前缀参数得 `num_in_out_ptrs`（`:3202-3208`）；`num_gb = get_num_bytes(*args, num_in_out_args=...)/1e9`、`gb_per_s = num_gb/(ms/1e3)`；`cached = (ms, num_gb, gb_per_s, kernel_name)`（`:3209-3211`） | 其后复用 `cached`（`:3212-3213`），不重测 |
| 每次命中 | `collected_calls.append(...)` + `print(create_bandwidth_info_str(..., suffix=kernel_name))`（`:3214-3217`） | 上游 `collected_calls` 全局表（`:46` import） |

`select_algorithm.py:299-315` 接线（定向读）：上游 `DebugAutotuner` 的 isinstance 检查匹配不到本类（**因为它继承 NPUCostModelAutotuner**，注释原义），故上游检查列表里并列追加了本类；Debug 分支的 benchmark 闭包（`:312-317`）只是不加 `benchmark_run=True` 显式旗标（非 Debug 分支 `:318-324` 才加）；`:298-302` 注释把这表述为「本类自消费 benchmark_run、闭包转发会收到两次」——按注释意图记录，闭包分支本身不证明运行期重复关键字必然发生。

## costmodel 绑定验收契约（test_costmodel_autotuner.py）

`test/_inductor/test_costmodel_autotuner.py`（99 行全文静态阅读，未运行）四个单测钉死类外行为：

- `_prepare_configs_for_precompile` 在并行编译后**必须重载 jit 函数**（`self.fn` 换成 `_reload_kernel()` 的结果）并把 `_resolve_costmodel_runtime_inputs()` 解析值传给 `_apply_costmodel_to_configs`。
- TTIR **保名**参数（`%y0_numel` 等非 argN 形态）与**旧版位置**参数（`%argN`）两种形态都按位置产出 `arg{id}={int}` 绑定串（对象占位被跳过），cfg kwargs 补值、恒附 `pid_x=0`（三个绑定测试的期望串逐字钉死）。

## 发布版对照（f3ecfe4a `npu_triton_heuristics.py:1007-1039`）

发布版 `NPUDebugAutotuner(NPUCachingAutotuner)`：`__init__` 仅 `regex_filter`；`run(self, *args, input_grid, stream)` 带 `input_grid`，`re.match` 不匹配同样先 return；`super().run(*args, grid=input_grid, ...)`；`bench(launcher, *args, input_grid=input_grid)`；无 `with_profiler/with_bandwidth_info/benchmark_run` 消费、无 `kernel_name` 两级回退。其余 `collected_calls`/`get_num_bytes`/带宽串拼接语义相同（逐字对照）。主线版本不接收 `input_grid`（注释原义：NPU launcher 自取 grid）。

## 失效边界与静态口径

- `costmodel_bench` 本体在 `triton.backends.ascend.runtime.costmodel_runtime`（triton-ascend 侧），未读未执行；其预测精度、缓存键构成不在本卡证据范围，仅按[文档契约卡](torch_npu_inductor_costmodel_and_shape_groups.md)的口径为「预筛选不替代实测」。
- costmodel 预筛选发生在 precompile 准备期（`_prepare_configs_for_precompile` 覆写链）；`_costmodel_fallback_configs` 在 `_precompile_current_configs` 正常返回后被清空（`:2427`，异常路径不清），且 `_apply_costmodel_to_configs` 每次进入都先置 None（`:2331`）——后续调用可重建，非「清空后永不重建」。
- `NPUDebugAutotuner` 的带宽数值依赖 `get_num_bytes` 对参数签名的静态推断，仅调试路径，无任何性能承诺。
- `NPUSymbolicGroupedAutotuner`（`:2430-3163`）由[分组 autotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)持有；验收契约条目为测试文件静态阅读，未运行测试。
- 本卡全部结论来自两 pin 静态阅读；未运行任何 costmodel、profiler 或带宽测量。

## Evidence

- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（primary；读窗 `:830-853`、`:1054-1130`、`:2101-2429`、`:3164-3217`）
- [主线 select_algorithm.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/select_algorithm.py)（implementation；`:290-315` isinstance/benchmark_run 接线）
- [主线 config.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（implementation；`_parse_float_env` `:404-416`、`enable_costmodel_prefilter`/`costmodel_ratio` `:427-428`）
- [发布版 npu_triton_heuristics.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py)（implementation；`NPUDebugAutotuner` 对照 `:1005-1040`）
- [test_costmodel_autotuner.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_costmodel_autotuner.py)（evidence；全文 99 行静态阅读，断言见『验收契约』节）
