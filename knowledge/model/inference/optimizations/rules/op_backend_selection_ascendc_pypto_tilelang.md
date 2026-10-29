---
type: Optimization
title: 同一算子有 AscendC / pyPTO / TileLang 多后端实现时的选型 — 当前阶段优先 AscendC
description: 同一算子有 AscendC / pyPTO / TileLang 多后端实现时的选型 — 当前阶段优先 AscendC。在 cann-recipes-infer 里部署某个算子时，发现同一类算子在 ops/ 下并行提供了三套后端实现——ops/ascendc（Ascend C）、ops/pypto（+ ops/pypto_python，pyPTO）、ops/tilelang（TileLang），三者覆盖同一批算子（例如 DeepSeek 系 indexer / attention 在多个后端下都有对应目录）。此时选哪一套后端并不显然，需要一条默认选型先验。
tags:
- task.optimization
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/2
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- agnostic
---

# 同一算子有 AscendC / pyPTO / TileLang 多后端实现时的选型 — 当前阶段优先 AscendC

## 适用场景

在 cann-recipes-infer 里部署某个算子时，发现同一类算子在 `ops/` 下并行提供了三套后端实现——`ops/ascendc`（Ascend C）、`ops/pypto`（+ `ops/pypto_python`，pyPTO）、`ops/tilelang`（TileLang），三者覆盖同一批算子（例如 DeepSeek 系 indexer / attention 在多个后端下都有对应目录）。此时选哪一套后端并不显然，需要一条默认选型先验。

## 条件 → 优先尝试什么

- **条件**：本仓中某算子同时存在 AscendC / pyPTO / TileLang 实现。
- **优先尝试**：默认采用 **Ascend C** 实现——维护者确认在当前阶段其性能最优，作为默认选型。
- **备选**：pyPTO / TileLang 属演进中的路径，成熟度与性能仍在追赶，作为后续再评估的备选，不作为首选。

维护者只给了定性建议、**未给任何 benchmark 数字**，因此不要据此写「快 N 倍」这类量化陈述——它是「先默认走 AscendC」的选型先验，不是性能测量。

## 反例 / 时效边界

- 该建议明确限定「当前阶段」：pyPTO & TileLang 会持续优化，未来三者相对优劣可能变化——把它当**可复核的默认值**、不是永久结论。真要在具体 workload 上定选型，仍应对目标算子实测三后端时延后再定。
- 适用面仅限本仓三后端算子的选型，不外推为整个昇腾栈通用律；归因主语是「本仓维护者的推荐」，非上游模型/算子厂商。

## 参考实现及其约束

- 三后端目录并存于 cann-recipes-infer 的 `ops/ascendc` · `ops/pypto`(`ops/pypto_python`) · `ops/tilelang`，覆盖同类算子。
- 这条选型先验落地时可与后端专属经验配合：走 AscendC 后端时若要扩展 dtype 见 [ascendc-custom-op-out-of-band-dtype](ascendc_custom_op_out_of_band_dtype.md)；AscendC 自定义算子跨平台/跨 CANN 构建见 [ascendc-custom-op-cross-platform-cann-build](../../runbooks/compilation/ascendc_custom_op_cross_platform_cann_build.md)；走 pyPTO 版 Lightning Indexer 时的兼容边界见 [c8-kvcache-disables-pypto-lightning-indexer](../anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)。

## 相关

- 概念页：[ascendc](../../concepts/frameworks/ascendc.md) · [pypto](../../concepts/frameworks/pypto.md) · [tilelang](../../concepts/frameworks/tilelang.md)。
- 走 AscendC 后端的具体算子经验：[sfaa-nonpa-qkv-layout-constraint](../../runbooks/runtime/sfaa_nonpa_qkv_layout_constraint.md)（SFAA 反量化 attention 的布局约束）。

## Evidence

- `维护者确认`（cann-recipes-infer，`@2c45117d781a`）：事件 Discussion 中维护者官方答复「当前阶段推荐 Ascend C 版本，性能最优；pyPTO & TileLang 版本会持续优化」，非提问者猜测。
- `仓库结构事实`（`@2c45117d781a`）：clone 核实 `ops/ascendc` / `ops/pypto`(`ops/pypto_python`) / `ops/tilelang` 三套后端目录确实并存且覆盖同类算子，佐证「三后端并行」。
- 无 benchmark 数据；时效限定「当前阶段」，需随仓库演进复核。
- 溯源下探：[cann-recipes-infer-issue-2-question](https://gitcode.com/cann/cann-recipes-infer/issues/2)。