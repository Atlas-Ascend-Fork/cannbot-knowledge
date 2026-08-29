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
updated_at: '2026-08-25T06:41:27Z'
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
- 这条选型先验落地时可与后端专属经验配合：走 AscendC 后端时若要扩展 dtype 见 [ascendc-custom-op-out-of-band-dtype](ascendc_custom_op_out_of_band_dtype.md)；AscendC 自定义算子跨平台/跨 CANN 构建见 [ascendc-custom-op-cross-platform-cann-build](../../../runbooks/compilation/ascendc_custom_op_cross_platform_cann_build.md)；走 pyPTO 版 Lightning Indexer 时的兼容边界见 [c8-kvcache-disables-pypto-lightning-indexer](../anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)。

## 相关

- 概念页：[ascendc](../../../concepts/frameworks/ascendc.md) · [pypto](../../../concepts/frameworks/pypto.md) · [tilelang](../../../concepts/frameworks/tilelang.md)。
- 走 AscendC 后端的具体算子经验：[sfaa-nonpa-qkv-layout-constraint](sfaa_nonpa_qkv_layout_constraint.md)（SFAA 反量化 attention 的布局约束）。

## Evidence

- `维护者确认`（cann-recipes-infer，`@2c45117d781a`）：事件 Discussion 中维护者官方答复「当前阶段推荐 Ascend C 版本，性能最优；pyPTO & TileLang 版本会持续优化」，非提问者猜测。
- `仓库结构事实`（`@2c45117d781a`）：clone 核实 `ops/ascendc` / `ops/pypto`(`ops/pypto_python`) / `ops/tilelang` 三套后端目录确实并存且覆盖同类算子，佐证「三后端并行」。
- 无 benchmark 数据；时效限定「当前阶段」，需随仓库演进复核。
- 溯源下探：[cann-recipes-infer-issue-2-question](https://gitcode.com/cann/cann-recipes-infer/issues/2)。

<!-- cannbot:related:start -->
## 相关

- [AscendC](../../../concepts/frameworks/ascendc.md)（`related`）：默认采用 **Ascend C** 实现——维护者确认在当前阶段其性能最优，作为默认选型。；华为昇腾原生的 C++ 算子编程框架，提供对 NPU 硬件的精细控制能力，用于实现高性能融合算子。。前者给出 cann-recipes-infer 多后端并存时优先 Ascend C 的当前选型，后者说明 AscendC 以 C++ 模板和硬件精细控制实现高性能融合算子的能力基础，形成后端选择到框架能力的下钻链。
- [Lightning Indexer Kernel](../../../concepts/kernels/lightning_indexer.md)（`related`）：“本 kernel 在 cann-recipes-infer 中同时提供 **AscendC**（手写高性能）、**PyPTO**（自研 MegaKernel）、**TileLang**（社区编译）三路实现，彼此性能/易用性各有取舍；V4 在 AscendC 侧补充了 950PR/DT 直方图 Top-k 与 FP8 量化版 LI（INT8/FP8 共用 `npu_quant_lightning_indexer`，FP8 区别在上游 q 经 `npu_dynamic_block_quant` 量化，见下文 ［DeepSeek-V4 CSA 层增强］(#deepseek-v4-csa-层增强)）。”；“- **优先尝试**：默认采用 **Ascend C** 实现——维护者确认在当前阶段其性能最优，作为默认选型。”。焦点列出三种 LI 后端，目标规则给出当前默认首选和必须实测复核的选型顺序。
- [SparseAttnSharedKV (SAS) Kernel](../../../concepts/kernels/sparse_attn_sharedkv.md)（`related`）：“cann-recipes-infer 同步提供 **AscendC**（Atlas-A3 非量化 + 950PR/DT 伪量化）、**PyPTO**（拆为 SWA / CFA / SCFA 三个场景化算子）、**TileLang**（V4-Flash SFA 实现）三路实现。”；“- **优先尝试**：默认采用 **Ascend C** 实现——维护者确认在当前阶段其性能最优，作为默认选型。”。SAS 的三后端实现清单与目标规则的默认首选、实测复核边界形成具体选型链。
- [ascendc SparseFlashAttention 非 PA(无 block table)decode 路由到未优化模板、慢于 tilelang](../../../runbooks/runtime/ascendc_sparse_flash_attention_non_pa_slow.md)（`related`）：非 PA 路径当前是未优化模板，其耗时不代表算子上限——**不要据非 PA 实测判定 ascendc 弱于 tilelang**；真要在具体 workload 上定选型，仍应对目标算子实测三后端时延后再定。前者给出 SparseFlashAttention 非 PA 路径的反例边界，后者要求按目标 workload 实测；二者把默认后端先验收敛为可复核的具体选型流程。
<!-- cannbot:related:end -->
