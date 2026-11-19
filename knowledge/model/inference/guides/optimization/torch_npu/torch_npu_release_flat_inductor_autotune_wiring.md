---
type: Guide
title: torch_npu 发布版扁平 Inductor autotune 接线（npu_triton_heuristics 关键决策链）
description: 记录发布 pin _inductor 扁平布局下 autotune 的安装点（_load_cached_autotuning/should_use_persistent_reduction/aggresive benchmark 替换）、cached_autotune 决策、生成代码 @npu_triton_heuristics 装饰器入口、triton_config_npu_index 与 codegen 版 TileGenerator，及与主线重构树的文件对照与覆盖边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/runtime.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_choices.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/tile_generator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: implementation
created_at: '2026-11-12T06:50:18Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 发布版扁平 Inductor autotune 接线（npu_triton_heuristics 关键决策链）

## 固定版本与适用范围

发布 pin（f3ecfe4a，v26.0.0 实际交付布局）的 `torch_npu/_inductor/` 是扁平结构：autotune 相关为 `npu_triton_heuristics.py`（1396 行）、`runtime.py`（70 行）、`npu_choices.py`（33 行）、`npu_triton_helpers.py`（28 行）与 `codegen/tile_generator.py`（253 行）。主线 pin（ac0e1564）把这些拆进 `runtime/` 补丁包与 `triton_experimental/` 隔离树并改为 monkey-patch 接线（见[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)）。本卡覆盖发布版 autotune 的接线链；同目录其余扁平文件中，`npu_device.py`、`npu_fusion_attention_graph.py`、`lowering_op_list.py`、`npu_decomp.py` 与 `codegen/cpp_wrapper.py` 的行为面分别见[设备算子覆写卡](torch_npu_release_flat_inductor_device_op_overrides.md)、[fusion attention 图模式卡](torch_npu_release_flat_inductor_fusion_attention_pattern.md)、[lowering 白名单卡](torch_npu_release_flat_inductor_lowering_whitelist_fallback.md)、[分解表面卡](torch_npu_release_flat_inductor_decomposition_surfaces.md)与[发布版 cpp wrapper 旧一代实现卡](torch_npu_release_inductor_cpp_wrapper_legacy_codegen.md)；`cpp_utils.py` 与 `aoti_runtime/interface.cpp` 仅有存在性与结构验证，未建行为结论——不得把本卡结论外推到未建行为结论的文件。本卡为纯静态阅读，未运行任何编译或测量。draft、platforms 为空。

## 安装点（release `_inductor/__init__.py`，160 行全文读）

`TORCHINDUCTOR_NPU_BACKEND` 为 mlir/dvm 时走各自插件分支（不安装下表）；default 分支按序：

| 安装点 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| `set_compile_threads()` / `disable_comprehensive_padding()`（config 侧函数） | 编译线程与 padding 默认收敛 | 细节属 config 面，见[配置解析卡](torch_npu_inductor_config_parsing.md) |
| `_inductor_register_backend_for_device` | 注册 `NPUTritonScheduling` + `NPUWrapperCodeGen` + `CppWrapperNpu` 三件套 | 与主线 `NPUCombinedScheduling`/`NPUPythonWrapperCodeGen` 是不同类名的发布版实现 |
| `inductor_lowering.make_reduction = make_reduction`、`make_fallback = npu_make_fallback` | 覆写 torch 全局 lowering 钩子 | `make_fallback` 被整表替换是发布版独有做法 |
| `patch_torch_for_aoti()`（`DISABLE_AOTI_PATCH != "1"` 时，默认安装） | cpp_wrapper/device_to_aten/constant fold/ir_fx 等 8 件 patch；`PRE_GRAPH_OPTIMIZER`/`POST_GRAD_GRAPH_OPTIMIZER` 精确等于"1"才挂 pre/post grad 自定义 pass | fx pass 本体不在本卡 |
| `_register_npu_inductor_fallbacks()` + `_register_npu_inductor_decompositons()` | 降级/分解注册（注意发布版函数名拼写 `..._decompositons`） | 发布版**没有** mm/addmm/bmm/grouped/multi_slice 的 per-op 注册（rg 零命中；对照主线见矩阵乘卡） |
| `aggresive_autotune`（`INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE`，拼写少一个 s）为真时 | `_replace_benchmark_all_configs()`：`CachingAutotuner.benchmark_all_configs = npu_triton_heuristics.benchmark_all_configs`（类方法级替换），并设 `TRITON_BENCH_METHOD=npu` | 关闭时不替换，基准走 torch 上游实现 |
| `InductorChoices.should_use_persistent_reduction = should_use_persistent_reduction`（npu_choices.py） | 覆写上游降级判定 | 见下节阈值 |
| `autotune_cache._load_cached_autotuning = _load_cached_autotuning`（`:126`） | 安装扁平 runtime.py 内的缓存覆盖 | 语义见主线卡的发布版差异节：只 pop `time_taken_ms/num_warps/num_stages`，`Config(best_config,...)` 直建，`found_by_coordesc=True` |
| `register_fa_pass()` + 末尾七个 patch（`patch_cache_base_get_system/patch_is_gpu/patch_has_triton/disable_foreach/patch_get_first_incompatible_cudagraph_node/patch_get_optimization_cflags/patch_device_override_func`） | FA fx pass 与杂项兼容 patch | 各 patch 本体未逐行读 |

关键结构性差异：发布版**不替换** `torch._inductor.runtime.triton_heuristics.cached_autotune`——本仓 autotuner 不靠 monkey-patch 生效，而是生成代码直接引用仓内模块（下节）。

## 生成代码入口：`@npu_triton_heuristics` 装饰器

`codegen/triton.py:755-780`（读到 790）：生成 kernel 前拼接 `heuristics_line`，`inside_reduction` 时为 `@npu_triton_heuristics.{heuristics}(size_hints=..., reduction_hint=..., filename=__file__, triton_meta=..., inductor_meta=...)`，否则 `pointwise` 变体（带 `tile_hint`），随后 `@triton.jit`；行内注释原义“Note: override original triton_heuristics”。生成代码的 import 由 `gen_triton_ext_imports`（`:471-479`）注入：`from torch_npu._inductor import npu_triton_heuristics`、`from torch_npu._inductor.runtime import NPUDeviceProperties`、`from torch_npu._inductor import npu_triton_helpers` 等。grid 类型取 `npu_triton_heuristics.GridNpu`（`:467-468`）。自定义 kernel 走 `npu_triton_heuristics.user_autotune_npu`（wrapper 代码生成引用，rg 命中）。因此：发布版每个被 inductor 生成的 Triton kernel 的 autotune 都进本仓 `cached_autotune`，与 torch 上游 `triton_heuristics.cached_autotune` 的存续无关。

## `cached_autotune` 决策与 NPUCachingAutotuner（release 版）

`npu_triton_heuristics.py:1041-1116`（cached_autotune 全函数）：盘上缓存命中逻辑与主线同构（`force_disable_caches`/`TRITON_INTERPRET`/多候选或 coordesc 才建 `AutotuneCache`，命中则候选收缩为单 best_config）。decorator 内只有两个分支：`profile_bandwidth` → `NPUDebugAutotuner`；否则一律 `NPUCachingAutotuner`（`:1114`）。**没有** FASTAUTOTUNE、符号分组、costmodel 预筛分支（发布 pin 全源 rg 零命中）。

`NPUCachingAutotuner`（`:412-520`）：相对 torch 上游是薄子类——`__init__` 只加 `exceptions`/`fn_name`；`precompile` 串行 for 循环逐配置 `_precompile_config`（`:487-518`），任一配置可编译即可用，全失败抛 `NoTritonConfigsError`；静态方法 `api_accuracy_checker` 挂 msprobe 精度比对（消费 `INDUCTOR_ASCEND_CHECK_ACCURACY` 面，config 卡已覆盖）。

`benchmark_all_configs`（`:1262-1375`，aggresive_autotune 安装）：用 `torch_npu.profiler`（`AiCMetrics.PipeUtilization`、Level1、tensorboard_trace_handler 落 `profile_path`+md5 目录）批量计时，`rep=1`、每步循环 `rep+3` 次，`schedule(wait=0, warmup=1, active=1)`；结果从 `kernel_details.csv` 里筛 `Name` 以 `triton` 开头的行取 `Duration(us)`（pandas），异常时回退逐个 `self.bench` 单基准并打印。任何 launcher 的 `n_spills > config.triton.spill_threshold` 时**整批**直接返回 `inf`（`:1284-1285`，与逐候选判罚不同，静态记录该差异）。测量结果同样 `coordesc_tuner.cache_benchmark_result` 回写。

## tile 生成（release 版）

`triton_config_npu_index`（`:1132-1174`）：从 `inductor_meta` 取 `split_axis/tiling_axis/low_dims/split_axis_dtype/axis_names/dual_reduction` 构造 `TileGenerator`（`from .codegen.tile_generator import TileGenerator`，`:72`），`descend_split_tiling()` 产配置；零配置时回退为“split 轴整段 BLOCK”单配置（`num_warps=1, num_stages=1`，必要时 `dummy=1` 占位）；随后给每个配置注入 `split_axis`/`split_blocks` 元组 kwargs。release 版 `codegen/tile_generator.py`（253 行）：`stop_numel = 1024 // dtype_bytes` 是**字面常量**预算，与主线 runtime 版按 `config.ub_size`/`num_vector_core`/`input_ptr_num` 推导的预算（见主线卡）不是同一套停止条件；该文件与主线 `runtime/tile_generator.py`（574 行）经 `diff -q` 确认非同一文件，两版下降算法对照见[发布版 TileGenerator 裁剪卡](torch_npu_release_flat_inductor_tile_generator_descents.md)，不与主线版本或 triton-ascend 副本互推。入口装饰器 `pointwise_npu_index/reduction_npu_index/persistent_reduction_npu_index/foreach/user_autotune_npu`（`:1177-1396`）都是 `cached_autotune` 的薄包装。

`should_use_persistent_reduction`（npu_choices.py，33 行全文）：`config.triton.persistent_reductions` 关则直接 False；阈值表 `INNER:1024, DEFAULT:1024`、其余 hint 64；cooperative reduction 时按 `32//min(size_hint(numel),32)` 放大（unbacked symint 捕获 ValueError 放过）；`multi_kernel` 开启时再 ×16。该文件顶层有一个模块级 `@staticmethod` 装饰的自由函数（Python 3.10+ 可调用的写法，静态记录不判优劣）。

## 发布/主线文件对照（结构性映射，按目录与函数名对应）

| 发布版扁平文件 | 主线对应 | 状态 |
| --- | --- | --- |
| `runtime.py`（70 行：`_load_cached_autotuning` + `NPUDeviceProperties`） | `runtime/autotune_cache.py` + `runtime/runtime_utils.py`；`patch_create_device_properties` 挪入 `_compat/inductor.py` | 语义差异见主线卡『发布版差异』 |
| `npu_triton_heuristics.py`（1396 行，单 autotuner） | `runtime/triton_heuristics.py`（4160 行，五类 autotuner 决策树）+ `triton_experimental/npu_triton_heuristics.py`（3293 行，隔离树） | 接线方式从生成代码引用改为 monkey-patch |
| `npu_choices.py`（33 行） | `choices.py`（patch_inductor_choices） | 函数级对应 |
| `codegen/tile_generator.py`（253 行） | `runtime/tile_generator.py`（574 行） | 原始字节不同（diff -q differ）；仅证明两份内容字节不一致，不据此断言历史谱系无关，行为/谱系等价性未确立 |
| `npu_device.py`（NewNPUDeviceOpOverrides，214 行） | `codegen/common.py register_device_op_overrides_npu` | 行为面见[设备算子覆写卡](torch_npu_release_flat_inductor_device_op_overrides.md) |
| `npu_fusion_attention_graph.py`（npu_fa/NpuGraphAttentionFunction/register_fa_pass，257 行） | `fx_passes` FA/fav3 家族 | 注册链见[fusion attention 图模式卡](torch_npu_release_flat_inductor_fusion_attention_pattern.md) |
| `lowering_op_list.py`（111 行） | `lowering_fallback_list.py` + `lowering_override_list.py` | 三表与运行时重注册见[lowering 白名单卡](torch_npu_release_flat_inductor_lowering_whitelist_fallback.md) |
| `ascend_npu_ir/ascend_npu_ir/npu/npu_decomp.py`（203 行） | `decomposition.py` | 分解表面见[分解表面卡](torch_npu_release_flat_inductor_decomposition_surfaces.md) |
| `codegen/{cpp_wrapper.py, cpp_utils.py, aoti_runtime/interface.cpp}` | `codegen/{cpp_wrapper_npu, ...}` + AOTI 面重构 | cpp_wrapper 行为面见[发布版 cpp wrapper 旧一代实现卡](torch_npu_release_inductor_cpp_wrapper_legacy_codegen.md)；cpp_utils.py 与 interface.cpp 仅有结构验证 |

## 失效边界与静态口径

- 本卡结论只覆盖发布 pin 的 default（Triton）后端；mlir/dvm 分支只读了 import 与插件注册行。
- `aggresive_autotune` 的基准替换只在开启时生效；`benchmark_all_configs` 的整批 inf 行为是该安装路径的独有语义。
- 与主线的一切对照都是静态结构对应，不构成行为等价承诺：同一 torch 上游版本下两 pin 的实际 kernel 产物需另行核对。
- 未运行任何编译、profiler 或测量；`Duration(us)`/UB 等数值门槛以源码常量为准。
