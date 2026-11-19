---
type: Guide
title: torch_npu 主线生成代码的装饰器发射与模块绑定：别名遮蔽、_get_heuristic、combo foreach 强制与 template 发射
description: 记录主线 codegen 侧如何把五个 heuristics 入口写进生成代码并绑定到 torch_npu runtime 模块：NPUTritonKernel/NPUIndexTritonKernel 的 gen_common_triton_imports 模块别名遮蔽、_get_heuristic 三名选择与单 kernel 发射（tile_hint/reduction_hint/min_elem_per_thread 实参）、NPUComboKernel 的 foreach 强制与 jit_line 三分支、select_algorithm 的 template 发射（use_jit 门、无 filename、FixedGrid 与 aggresive_autotune 注入）、triton_experimental template 转发器与 fast_launch 补丁的边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton_combo_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/select_algorithm.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/patch.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: implementation
created_at: '2026-11-12T13:41:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线生成代码的装饰器发射与模块绑定

## 固定版本与适用范围

主线 pin（ac0e1564）。本卡回答「五个 heuristics 入口（[入口卡](torch_npu_main_inductor_legacy_config_and_decorator_entries.md)）如何被生成代码触达」：模块别名绑定（`codegen/triton.py:902-918/:997-1012/:911/:1006`）、单 kernel 发射（`:2426-2434/:2444/:2516-2542`）、combo kernel（`triton_combo_kernel.py:55-69/:94-163/:279-287`）、template 选择路径（`select_algorithm.py:132-133/:1142-1212`）、隔离树转发器（`triton_experimental/npu_triton_heuristics.py:3283-3293`）与 fast_launch 补丁边界（`experimental/python_wrapper_fast_launch/patch.py:14-20/:287-320/:378-394`）。对上游 torch 的 monkey-patch 只有 `cached_autotune` 一处（`runtime/triton_heuristics.py:3375-3376`，[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)）——入口靠别名而非补丁生效。发布版发射对照（`@npu_triton_heuristics.{...}` 与 `gen_triton_ext_imports`）归[发布版接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)。`npu_triton_heuristics.GridNpu` 的 Grid 语义归[Grid/launcher 卡](torch_npu_main_inductor_grid_and_launcher_generation.md)。纯静态阅读；draft、platforms 为空。

## 模块别名遮蔽（非补丁）

生成的 wrapper 代码头部 import 由 `NPUTritonKernel.gen_common_triton_imports`（`:902-918`）与 `NPUIndexTritonKernel.gen_common_triton_imports`（`:997-1012`，两段文本相同）拼接：`import torch_npu` + bad-fork 预置（未初始化且 `_is_in_bad_fork()` 时 `torch_npu.npu._initialized = True`，`:907-910`）后接 `from torch_npu._inductor.runtime import triton_heuristics as triton_heuristics`（`:911/:1006`）与 triton_helpers 星号导入——生成代码里的 `triton_heuristics.X` 全部解析到 npu runtime 模块，与上游 `torch._inductor.runtime.triton_heuristics` 的存续无关。codegen 自身 `:57` import 上游模块、`:80` import npu 版为 `npu_triton_heuristics`（如 `:1188-1189` `_get_grid_type` 返回 `npu_triton_heuristics.GridNpu`）。

## 单 kernel 发射（`_get_heuristic` 与 `:2516-2542`）

`_get_heuristic`（`:2426-2434`，注释原义 "not support fixed config and cooperative_reduction yet"）：`persistent_reduction` 需 `inside_reduction`（否则 `RuntimeError("assert self.inside_reduction to be true")`）返回 `"persistent_reduction"`；`inside_reduction` 返回 `"reduction"`；否则 `"pointwise"`。`codegen_kernel` 在 `:2444` 取该名后拼 decorator（行内注释原义 "Note: override original triton_heuristics"，`:2516`）：

- 规约：`@triton_heuristics.{heuristics}(size_hints=…, reduction_hint=…, filename=__file__, triton_meta=…, inductor_meta=…)`（`:2517-2524`；`size_hints` 原样内插不取 repr）。
- 非规约（pointwise）：`len(size_hints)==2` 时 `len(signature)==4` 取 `TileHint.SQUARE`、否则 `TileHint.DEFAULT`（`:2528-2533`），并附 `min_elem_per_thread`（`:2541`）——两个实参在入口处收下即弃（入口卡）。`@triton.jit` 紧随两形态（`:2525/:2543`）。

## combo kernel（`triton_combo_kernel.py`）

`select_combo_heuristics`（`:64-69`）：`enable_autotune` 为假时**强制 `"foreach"`**（`:67-68`，非 autotune 组合路径）；为真时取第一个 sub-kernel 的 `_get_heuristic()` 结果（`:56-58`）。`jit_line`（`:94-163`，`assert selected_kernel is not NPUIndexTritonKernel` `:122`）三支：foreach 传 `num_warps`、无 tile_hint（`:126-137`）；inside_reduction 传 `reduction_hint`（`:139-150`）；else 的 tile_hint **无条件**按 `len(size_hints)==2` 给 SQUARE/DEFAULT——无单 kernel 路径的 `len(signature)==4` 门（`:151-162`，与 `:2529-2533` 的差异）。调用点 `:279-287`。

## template 选择路径（`select_algorithm.py`）

`_gen_npu_template_triton_imports`（`:132-133`）= `NPUTritonKernel.gen_common_triton_imports()`——模板选择代码同样绑定 npu 模块别名（`:1113` splice 进 `<DEF_KERNEL>` hook）。`jit_lines`（`:1142-1212`）：`use_jit` 真 → 裸 `@triton.jit`（`:1152-1153`，无任何 autotune）；否则发射 `@triton_heuristics.template(num_stages=…, num_warps=…, triton_meta=…, inductor_meta=…)`（`:1203-1211`）——**不传 filename**，template 入口的 filename 形参保持默认 None（入口卡）。配套注入：`triton_meta["configs"]=[config_of(signature)]`（`:1166`）、`npu_compile_options`（`:145-152` 经 `:1182`）、`inductor_meta` 含 `FixedGrid.setup_grid_as_args()`（`:1192`）、`ENABLE_COMPILE_HINT/BLOCK_M/BLOCK_N`（`:136-141` 经 `:1198`）、`npu_config.aggresive_autotune` 真时 `profile_bandwidth_with_do_bench_using_profiling=True`（`:1200-1201`）。

## 隔离树与 fast_launch 边界

- `triton_experimental/npu_triton_heuristics.py` 自有 `pointwise`（`:2178`，独立实现，归 experimental_triton_* 卡），但其 `template`（`:3283-3293`）是**转发器**：`from torch_npu._inductor.runtime.triton_heuristics import template as npu_template` 后原样转发（含 `filename` 与 `**_kwargs` 吞掉 `num_consumer_groups` 等）——隔离树五个入口中只有 template 直接复用 runtime 版。
- `python_wrapper_fast_launch/patch.py`：`patch_fast_launch`（`:378-394`）经 `_resolve_triton_heuristics_module`（`:19-20`，`import_module("torch_npu._inductor.runtime.triton_heuristics")` 模块身份解析）取 npu runtime 模块；`_build_triton_patch_operations`（`:287-320`）只包 `TritonCompileResultNpu.make_launcher`（`:305-306` `group_enabled` 真即跳过），**不触碰五个入口**。
- 因此入口的可达面是：普通/combo/template 生成的 wrapper 代码 + 隔离树 template 转发；没有其他进程内直接调用方（本仓内 rg 全查）。

## 失效边界与静态口径

- 发射文本是 f-string 产物：`{size_hints}` 原样内插要求其 `str()` 是合法 Python 字面量（get_size_hints 多轴返回 dict 满足）；生成代码可执行性未动态验证。
- `use_jit`、`benchmark_kernel`、`enable_autotune` 等开关只按发射分支登记为事实，各开关的启用条件不在本卡范围。
- 发布版（f3ecfe4a）发射面走 `@npu_triton_heuristics.*` 命名（发布版接线卡 `:755-790/:471-479`），与本卡模块别名遮蔽是两套接线，不互推。
- 纯静态阅读：未运行 codegen、未生成/导入任何 wrapper 代码。
