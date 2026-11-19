---
type: Guide
title: torch_npu 主线 precompile 管线：串/并行调度、TTIR 检查门、全败 UB 反馈与 save_npu_kernel 落盘
description: 记录主线 runtime/triton_heuristics.py 的 :831-987 与 :1131-1415 段：_precompile_worker 的 template 串行门与 CompileThreadPool 并行、_make_ttir_module_from_cfg/_triton_make_ttir 的 TTIR-only 编译与调度器 make_ttir_for_check 每核检查门、_precompile_configs_with 全败 NoTritonConfigsError 与 ub_overflow_failures 反馈、UB 溢出一次性重试、_precompile_config 的 required_ub_bits 回填与 enable_auto_blockify、_make_launchers 变体刷新、save_npu_kernel 的 runtime_blocks 与 ttadapter IR 落盘；附发布版逐点差异锚。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/scheduling.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_ub_overflow_retry.py
  role: evidence
created_at: '2026-11-12T13:13:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 precompile 管线：串/并行调度、TTIR 检查门、全败 UB 反馈与 save_npu_kernel 落盘

## 固定版本与适用范围

主线 pin（ac0e1564）`runtime/triton_heuristics.py` 的 precompile 面：`:831-987`（调度、TTIR-only 编译族）与 `:1131-1415`（`parse_triton_ascend_options`、`_precompile_config`、`_make_launchers`、`save_npu_kernel`、并行编译），并定向读消费端 `codegen/scheduling.py:230-300`（`make_ttir_for_check`）与 `codegen/triton_utils.py:25-45`（`NPUKernelType.compile_mode`）。`cached_autotune` 决策树与补丁安装见[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)；costmodel 子类对 `_prepare_configs_for_precompile` 的覆写与子类不做 UB 重试的另一证据见[costmodel/debug 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)；`_precompile_variant_configs`/`_refresh_variant_launchers`/`_precompile_current_configs` 消费端与 UB 反馈的调用侧见[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)。发布 pin（f3ecfe4a）对应面（release `:412-520`/`:521-611`/`:613-652`）已由[发布版接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)与[发布版类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)闭合，本卡只给逐点差异锚。纯静态阅读：未导入/执行/编译任何上游代码；draft、platforms 为空。

## 调度：`_prepare_precompile`/`_precompile_worker`（`:833-852`）

`_prepare_precompile` 先 `_prepare_configs_for_precompile()` 再 `candidate_plan = _build_candidate_plan(self.configs)`（`:833-835`；costmodel 子类在覆写里插入预筛选，见[costmodel/debug 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)）。`_precompile_worker`：`skip_precompile` 置位直接返回（fasta tuner 用，见[Grid/launcher 卡](torch_npu_main_inductor_grid_and_launcher_generation.md)）；已有 `compile_results` → 直接走串行路径（幂等入口）；`is_template = heuristic_type == TEMPLATE 且 size_hints is None`——源码注释原义：`template()` 无 size hints，`foreach()` 也用 TEMPLATE 但保留 size hints、必须保住其 vector configs 的并行编译——`precompile_thread_num > 1 且非 is_template` → 并行，否则串行。

## TTIR-only 编译族（`:854-986`）与调度器检查门

- `_make_ttir_module_from_cfg`（`:854-925`）：deepcopy `triton_meta`；cfg kwargs 中**属于 constexpr 形参名**的项写入 `constants`（`:858-862`）；`num_warps`/`num_stages` 特例（`:864-869`）；`debug` 三重门槛与发布版相同（env `INDUCTOR_ASCEND_DEBUG` ∈ {true,1} 且 `assert_indirect_indexing` 缺省 True 且非 is_hip，`:872-876`）；`compile_mode` 缺省 `NPUKernelType.SIMT_TEMPLATE.compile_mode()` = `"simd_simt_template"`（`:878-880`；triton_utils.py `:35-38` 实字）；`GPUTarget(type, cc, warp=32)`；options 含 `multibuffer`/`enable_vf_fusion`（cfg kwargs 缺省 False，`:900-907`）——**`_precompile_config` 的 options 没有这两键**（见下节差异）；`parse_triton_ascend_options`（`:1131-1138`）把 `triton_meta["npu_compile_options"]` 与 cfg kwargs 中属于 `triton.backends.ascend.compiler.NPUOptions` dataclass 字段的键并入 options；随后 import triton 内部 `ast_to_ttir/make_backend/ir/ascend_ir`，`load_dialects` 后返回 `ast_to_ttir(fn, src, context, options, {}, {})`——**只到 TTIR，无后端降级/launch**（docstring 原义 "no backend lowering/launch"）。
- `_select_ttir_test_config`（`:927-946`）：选 `*SUB` 后缀 kwargs 整数乘积最小的 config（无 SUB 项则回退 `configs[0]`）。
- `_triton_make_ttir`（`:948-986`）：configs 空 → `NoTritonConfigsError`；只编译上述**一个**测试 config，失败 → `NoTritonConfigsError`（附 kernel/config/异常栈）；成功即 `self.compile_results = [ttir_module]`。
- **调度器检查门**（codegen/scheduling.py `make_ttir_for_check`，读窗 `:230-300`）：`codegen_node_schedule` 对每个生成 kernel 在 `codegen_kernel()` 后立即调 `make_ttir_for_check(src_code)`——把源码里 `Placeholder.KERNEL_NAME` 替换为 `triton_`、按行 eval 出 `inductor_meta`、置 `force_disable_caches=True`、`PyCodeCache.load` 加载后 `mod.triton_._triton_make_ttir()`，最后 `os.remove` 删掉临时缓存文件（FileNotFoundError 容忍）。即：**每个 codegen 出的 kernel 在编译期都要过一次 TTIR-only 编译检查**，这是 DSL 级失败在调度器处的显式失败面，不是运行期 autotune 失败面。

## 批量编译与全败 UB 反馈（`:988-1047`）

`_precompile_configs_once`（`:988-999`）串行逐 config，逐项捕获异常与栈。`_precompile_configs_with`（`:1001-1047`）：configs 空 → `NoTritonConfigsError`；`compile_once` 后无任何成功 → `NoTritonConfigsError`（附第一个异常与栈）；全败且 `type(self) is NPUCachingAutotuner` 且失败数 == 尝试数时，逐个用 `re.search(r"ub overflow.*?requires (\d+) bits while (\d+) bits available", re.IGNORECASE)` 解析失败文本，**每一项**都须满足 `required > available > 0`，任一项不匹配即不设属性；全匹配则 `error.ub_overflow_failures = tuple((cfg, required, available))`（`:1024-1041`；注释原义："Only an entirely UB-overflow batch supplies feedback to the outer, one-shot search stage"）。编译耗时仅 `log.debug`。

## UB 溢出一次性重试（`:1058-1126`）

- `_precompile_worker_with`：已有 `compile_results` → 对每个 result `TritonBundler.put(triton_hash_to_path_key(result.kernel.hash), triton_meta.get("device", 0))` 后返回（warm-cache 注册）；`launchers` 非空 → `AssertionError("Before _precompile_worker, launchers must bt empty")`（源码拼写 "bt" 原样）。**子类不做 UB 重试**：`type(self) is not NPUCachingAutotuner`（costmodel/grouped）直接 `_precompile_current_configs` 返回——注释原义 "Only the ordinary autotuner supports UB retry"（`:1069-1073`）。
- 基类路径 `try/except NoTritonConfigsError`：无 `ub_overflow_failures` → 原样重抛；有则尝试 `_retry_with_smaller_configs`，重试内部再抛 `NoTritonConfigsError` 被 `pass` 吞掉，**最终仍重抛最初的批次错误**（`:1084-1087`；注释原义 "A failed or unavailable retry must preserve the original batch error"）。
- `_retry_with_smaller_configs`（`:1089-1126`）门槛：`_ub_retry_attempted` 已置、`custom_kernel`、`group_enabled` 任一为真 → False（不扩张）。`ub_overflow_retry_configs`（tile_generator，[TileGenerator 下降卡](torch_npu_release_flat_inductor_tile_generator_descents.md)登记的生成器；persistent_reduction 对 `PERSISTENT_REDUCTION`/`TEMPLATE` 启用）产不出额外 config → False。随后置 `_ub_retry_attempted = True`（**每个 tuner 只试一次**）；`expanded_configs = [*original, *extra]` 重建 plan，只编译**新增变体**（注释原义 "without recursive expansion"），`log.warning` 报告追加数；成功后才发布扩张后的 `self.configs/candidate_plan/compile_results`（`:1122-1125`，注释原义 "Publish the expanded candidate space only after the new batch succeeds"）。重试语义的逐条验收契约见下节。

## UB 重试验收契约（test_ub_overflow_retry.py）

`test/_inductor/test_ub_overflow_retry.py`（217 行全文静态阅读，未运行；通过与否依赖 torch 版本与设备）钉死本节重试语义：

| 契约 | 测试钉死的断言 | 边界 |
| --- | --- | --- |
| 反馈有下界（`test_feedback_bounded_below_smallest_tile`） | 4 个 XBLOCK（32768→4096）全反馈 UB 溢出 → 额外候选恰为 `[2048,1024,512,256]`；**原 configs 列表不被改写**；极端反馈（requires 100000 bits、available 1）→ 额外候选 `[1]` | 重试候选按减半序列生成到 1 为止 |
| 固定轴/运行块保留（`test_fixed_and_runtime_axes_are_preserved`） | `X0BLOCK`/`split_blocks`/`R1BLOCK_SUB` 原样保留，只收缩 `X0BLOCK_SUB` 且结果 `< 32`；`no_loop_axis` 覆盖该轴或 constexpr 名单缺失 → 额外候选为空（不重试） | 失败配置传入的是**编译后** cfg（剥掉 X0BLOCK/split_blocks） |
| 批次后置发布（`test_retry_waits_for_batch_and_publishes_success`） | 重试只在**整批失败后**发生（编译期间 `tuner.configs/candidate_plan` 身份不变）；成功后 configs 身份更换、数量 2→6、plan 条目 6、`compile_results` 的 variant id 恰为 `{v2,v3,v4,v5}`——原两变体不进入结果；串行/并行两条编译路径同契约 | 与实现“只编译新增变体、成功后才发布”逐字对应 |
| 全败才触发（`test_only_all_ub_failure_retries`） | 任一成功（部分成功）、任一非 UB 错误（无论位置）、available ≥ requires（"requires 1024 bits while 2048 bits available"）→ 都不重试，`_retry_with_smaller_configs` 未被调、configs/plan 原对象保留 | 实现 `required > available > 0` 逐项校验的测试面 |
| 失败保留原错误且不重复（`test_failed_retry_preserves_error_and_is_not_repeated`） | 重试失败 → 最终异常**就是最初批次异常**（`caught.exception is errors[0]`、`__context__` 为 None——无异常链包裹）；`_ub_retry_attempted` 置位后第二次调用不再扩张（编译次数只多 1 次）；失败后 configs/plan/compile_results 全部保持失败前状态 | “A failed or unavailable retry must preserve the original batch error” 的断言面 |
| 不扩张面（`test_custom_and_grouped_kernels_do_not_expand`） | `custom_kernel` 或 `group_enabled` → 只 `NoTritonConfigsError`、`_precompile_config` 恰调一次、configs 不变、无 `_ub_retry_attempted` | |
| costmodel 兜底旁路（`test_costmodel_keeps_existing_fallback_without_ub_retry`） | `NPUCostModelAutotuner` 全败时走 `_costmodel_fallback_configs`（8192 失败 → 补编译 2048），`_retry_with_smaller_configs` 未调、无 `_ub_retry_attempted` | 子类不做 UB 重试的独立证据（与实现 `:1069-1073` 注释互证；costmodel 兜底见[costmodel/debug 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)） |

## 单配置编译 `_precompile_config`（`:1140-1260`）与并行（`:1380-1413`）

| 步骤 | 主线动作 | 发布版对照 |
| --- | --- | --- |
| constants 过滤（`:1144-1148`） | cfg kwargs 只写**属于 constexpr 形参名**的键 | release（`:521-525`）写"出现在 `fn.arg_names`"的**全部** cfg kwargs——过滤面不同（diff 锚） |
| debug 门/compile_mode/ASTSource/GPUTarget（`:1150-1198`） | 与 TTIR 变体相同：三重 debug 门、`compile_mode` 缺省 `"simd_simt_template"`、无 ASTSource → `RuntimeError("Installed triton version too old, please upgrade")`、warp 恒 32 | release 同构（对照 `:520-545` constants 过滤与 debug 门；ASTSource/GPUTarget 段结论归[发布版类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)） |
| options（`:1200-1211`） | `{num_warps, num_stages, debug, compile_mode}` + `parse_triton_ascend_options` 合并 `npu_compile_options` 与 cfg kwargs（NPUOptions 字段过滤） | release 无 NPUOptions 合并（全树 rg `parse_triton_ascend_options` 零命中，负证据） |
| auto_blockify（`:1212-1220`） | `inductor_meta["enable_auto_blockify"]` 或 `requires_no_linear_block_remap is True` → 并入 `enable_auto_blockify: True`；注释原义：旧版 Triton-Ascend 暴露该选项，新版内部管理 block mapping、选项会被过滤 | release 无此段 |
| 成功路径（`:1229-1233`） | `binary.metadata.required_ub_bits` 回填 `cfg.real_ub_size` | release 无 required_ub_bits/real_ub_size（rg 零命中） |
| AttributeError（`:1235-1242`） | binary 为 None → `raise Exception("Triton compilation failed") from e`；binary 存在但 metadata 缺 `required_ub_bits` → **仍返回编译结果**（注释原义 "mistake is metadata no required_ub_bits, but binary work"） | release 只有通用 `except Exception: log.debug + raise`（`:573-582`） |
| 其他异常（`:1244-1258`） | log.debug 后从 traceback 正则抓 `requires (\d+) bits` 回填 `cfg.real_ub_size` 再原样重抛 | release 无 ub 解析 |
| 并行（`:1380-1413`） | `_precompile_configs_parallel_once` 经模块级 `compile_thread_pool`（`CompileThreadPool`，见[Grid/launcher 卡](torch_npu_main_inductor_grid_and_launcher_generation.md)）逐 config 提交；同一 `_precompile_configs_with` 失败语义。`:1399-1401` 注释原义：warm-cache 编译也会跑在 fork 出的 worker 里，那里禁止初始化 NPU runtime，设备初始化属于编译完成后的 `_make_launchers` | release 无并行编译路径（`_precompile_worker` 串行 for 循环） |

## `_make_launchers` 与 `save_npu_kernel`（`:1262-1378`）

- `_make_launchers`（`:1262-1289`）：`len(launchers)==len(compile_results)` 幂等返回；`DeviceGuard` + `device_interface.synchronize()` 初始化上下文；逐 result `make_launcher()` 捕获异常（保留**最后一个**）；0 个 → `RuntimeError("No valid triton configs. ...")` 附最后异常栈。与发布版（release `:585-611`）两级失败面结论一致（发布版卡已记）；主线差异：成功后调 `_refresh_variant_launchers()`（variant map 回填，见[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)），且 precompile 后**不**清 `self.configs`（release `:516` 置 None；主线 configs 保留供候选计划与 UB 重试扩张）。
- `save_npu_kernel`（`:1294-1378`；`save_gpu_kernel` 别名 `:1291-1292`）：`kernel_name` 缺失 → `RuntimeError`。params 在发布版参数包之外新增：`runtime_blocks`（`best_runtime_blocks` 与 `runtime_block_arg_names` zip 成 dict；无则取第一个 compiled candidate 的 `runtime_blocks`；再无则 `{}`，`:1323-1333`）、`mix_mode`/`parallel_mode`/`is_pure_simt`/`has_auto_blockify_blacklist_op`（getattr 缺省 False）/`lock_num`（`_get_sync_block_lock_num`）/`sync_block_lock_layout`/`auto_tile_and_bind_subblock`/`lock_init_val`/`workspace_size`（`:1334-1358`）。`enable_simt = "simt" in parallel_mode or is_pure_simt`；`npu_config.is_ascend950 and enable_simt` → 另存 `shared_mem_dynamic_size`（`:1360-1362`）。落盘 `CudaKernelParamCache.set(key, params, bin.asm["npubin"], bin_type="cubin", asm=bin.asm.get("ttadapter"), asm_type="ttadapter")`——注释原义：AOTI 打包（package_cpp_only）路径下 `CudaKernelParamCache.set` 要求同时提供 kernel IR，Ascend backend 的 ttadapter stage 就是该 IR。发布版（release `:616-652`）只落 npubin + `bin_type='cubin'`，无 asm/asm_type 与上述 metadata 扩展（发布版卡已记）。

## 相邻卡边界

[Grid/launcher 卡](torch_npu_main_inductor_grid_and_launcher_generation.md)（`make_launcher` 拼装本体、`CompileThreadPool`、`_NPUSkipPrecompilePlugin`）；[主线基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)（`_precompile_variant_configs`/`_refresh_variant_launchers`/`_precompile_current_configs` 消费端与 UB 反馈的调用侧）；[主线 costmodel/debug 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)（`_prepare_configs_for_precompile` 覆写与子类不做 UB 重试的另一证据）；[分组 autotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)（grouped 侧 `_precompile_variants`/`save_npu_kernel` 覆写）；[发布版类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)与[发布版接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)（发布侧对应面）；[自动预编译缓存卡](torch_npu_automatic_precompile_cache.md)（TritonBundler warm-cache 的缓存面）。

## 失效边界与静态口径

- 本卡全部为两 pin 静态阅读；`required_ub_bits`/`ttadapter`/`NPUOptions` 字段集均以安装的 triton-ascend 为准，未在设备或编译环境验证；`enable_auto_blockify` 在新版被"过滤掉"的说法是源码注释原义，未实测过滤行为。
- `make_ttir_for_check` 的每核检查门结论限定读窗 scheduling.py `:230-300`（SIMD 调度路径）；其他调度器路径（template/DVM 等）是否同样调用未逐文件核对。
- UB 重试是每个 tuner 一次（`_ub_retry_attempted` 实例级）；重试成功后的候选空间扩张不保证后续 benchmark 全部可运行，该消费语义见[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)。
- 验收契约条目为测试文件静态阅读，未运行测试；断言与实现的“互证”仅指语义对应，不等于测试当前可跑或通过。

## Evidence

- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（primary；读窗 `:831-987`、`:1131-1415`）
- [主线 codegen/scheduling.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/scheduling.py)（primary；`make_ttir_for_check`/`codegen_node_schedule` 定向读 `:230-300`）
- [主线 codegen/triton_utils.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton_utils.py)（implementation；`NPUKernelType.compile_mode` 读 `:25-45`）
- [发布版 npu_triton_heuristics.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py)（implementation；对照读 `:490-583`；发布侧全量结论以[发布版类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)为准）
- [test_ub_overflow_retry.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_ub_overflow_retry.py)（evidence；全文 217 行静态阅读，断言见『UB 重试验收契约』节）

## 附录：codegen/triton_utils.py 四助手全表（:1-66 全文）

`:10-24` `byte_per_numel` 全表（float32:4/float64:8/float16:2/bfloat16:2/int32:4/int64:8/int16:2/int8:1/uint8:1/bool:1/complex32:4/complex64:8/complex128:16），表头注释原义："wrapper npu 32 bytes align, get and pass unalign info to triton meta / then autotune choose tiling param and send them to bishengIR"——该表是 wrapper 向 Triton meta 传递未对齐信息的 dtype→字节映射。`:41-44` `get_byte_per_numel(None→1)` 与 `:47-51` `get_aligned_numel`（`32//byte_per_numel` 得 32 字节对齐元素数，未知 dtype 回 1）。`:54-66` 两个节点名判别：`get_indirect_var` 以正则 `indirect|masked` 取节点名后缀（None 表示非间接节点），`get_indirect_mem_var` 以 `index_select|gather_template|indexput_template|scatter_template` 判别间接访存模板类节点。消费者：`ir.py`/`tile_generator.py`/`split_tiling.py`/`fasta_autotune.py`（rg 全树）；`NPUKernelType` 由 `lowering.py:81` 引用（与上文 `_make_ttir_module_from_cfg` 的缺省 compile_mode 锚一致）。对齐面与 cpp_wrapper 的 npu_block/NPU_ALIGN_BYTES、分组 tiling 卡交叉，不重复展开。
