---
type: Optimization
title: AscendC 自定义算子要能被 SuperKernel 融合，需加 --op_relocatable_kernel_binary=true 编译选项
description: AscendC 自定义算子要能被 SuperKernel 融合，需加 --op_relocatable_kernel_binary=true 编译选项。要让一个走 AscendC add_ops_compile_options 构建的自定义算子能被 SuperKernel 融合，在其 CMakeLists.txt 的 OPTIONS 里加 --op_relocatable_kernel_binary=true——编译时会额外产出 super kernel 专用的可重定位二进制 .o。 破一个直觉误区：不需要把算子改成在线（JIT）编译才能进 SuperKernel。本地离线编译只要带上这个可重定位二进制选项，就能产出该 .o、参与融合，无需切在线编译。
tags:
- task.optimization
- topic.attention
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/35
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- agnostic
---

# AscendC 自定义算子要能被 SuperKernel 融合，需加 --op_relocatable_kernel_binary=true 编译选项

## 条件 → 优先尝试什么

要让一个走 AscendC `add_ops_compile_options` 构建的自定义算子能被 [SuperKernel](../../concepts/techniques/superkernel.md) 融合，在其 `CMakeLists.txt` 的 `OPTIONS` 里加 `--op_relocatable_kernel_binary=true`——编译时会额外产出 super kernel 专用的**可重定位二进制** `.o`。

**破一个直觉误区**：不需要把算子改成在线（JIT）编译才能进 SuperKernel。本地离线编译只要带上这个可重定位二进制选项，就能产出该 `.o`、参与融合，无需切在线编译。

## 依据

SuperKernel 融合要求参与融合的算子提供 super kernel 专用的可重定位二进制。cann-recipes-infer 里这是 [AscendC](../../concepts/frameworks/ascendc.md) 算子的通用约定，`ops/ascendc/src/` 下约 16 个算子（`hc_post`、`moe_gating_top_k_hash`、`gather_selection_kv_cache`、`kv_compress_epilog`、`rms_norm_dynamic_quant`、`partial_rotary_mul_quant`、`scatter_nd_update_asc`、`dequant_swiglu_clamp_quant`、`hc_pre`、`hc_pre_inv_rms` 等）都在编译选项里带此项。示例（`hc_post/CMakeLists.txt`）：

```cmake
add_ops_compile_options(
        OP_NAME HcPost
        OPTIONS --cce-auto-sync=off
                -Wno-deprecated-declarations
                -Werror
                -mllvm -cce-aicore-hoist-movemask=false
                --op_relocatable_kernel_binary=true
)
```

维护者确认：[LightningIndexer](../../concepts/kernels/lightning_indexer.md) 算子当时虽未打开在线编译，但本地编译加了 `--op_relocatable_kernel_binary=true`，编译时即产出 super kernel 专用 `.o`，这种情况下无需改在线编译也应能使用 super kernel 功能。

## 反例 / 边界

- 编译选项的存在与写法为 diff/代码事实；"产出 super kernel 专用 `.o` / 因此无需在线编译即可用 SuperKernel"为维护者确认。源未给 before→after 性能数值。
- 适用面限于仍走 AscendC `add_ops_compile_options` 路径的算子。注意 **LightningIndexer 本身自该 issue 后已从 AscendC 构建迁到 [PyPTO](../../concepts/frameworks/pypto.md)/TileFwk 构建**（pypto 的 op_kernel CMake 走 `target_sources(tile_fwk_impl ...)`、未用该选项）——本规则适用于仍在 AscendC 构建的算子（锚点用仍在册的 `ops/ascendc/src/*`，不再指已迁走的 lightning_indexer 路径）。
- 不外推为整个昇腾栈通用律。

## Evidence

- **代码事实**（clone `@da545ca42b74`）：`grep -rn "op_relocatable_kernel_binary" ops/ascendc/` 命中 16 个算子的 `CMakeLists.txt`，均在 `add_ops_compile_options` 的 `OPTIONS` 内（如 `hc_post/CMakeLists.txt`、`moe_gating_top_k_hash/CMakeLists.txt`）。
- **维护者确认**：该选项编译时产出 super kernel 专用 `.o`、此情况无需在线编译即可用 super kernel。
- 溯源下探：[cann-recipes-infer-issue-35-bug-report-lightningindexer-superkernel](https://gitcode.com/cann/cann-recipes-infer/issues/35)