---
type: Optimization
title: "F29: level-2 `Mul` 的 `src1RepStride=0` 跨 repeat 广播在特定调用组合下数值错误（level-0 形式可用）"
description: "level-2 Mul 的 repeat + src1RepStride=0 在特定调用组合下会出现形状对、数值全错；跨 repeat 广播应使用 level-0 + 位图 mask + BinaryRepeatParams 的形式。"
tags:
  - task.debugging
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.memory
  - topic.precision
  - topic.compute.quantization
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/aux_data_structures/BinaryRepeatParams.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/general_description_and_constraints.md
    role: constraint
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f29_vec_mul_repstride0_cross_repeat_broadcast_910b2c.json
    role: evidence
created_at: "2026-11-06T00:00:00Z"
updated_at: "2026-11-06T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 vec-mul-repstride0-cross-repeat-broadcast-910b2c）。
>
> 原始元数据：
>
> ```yaml
> confidence: single_op
> phenomenon: precision_failure
> severity: medium
> occurrences: 1
> failed_combination: [P94, P99]
> op_families: [matmul, quantization, elementwise]
> operator_type: [matmul, quantization]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/f29_vec_mul_repstride0_cross_repeat_broadcast_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f29_vec_mul_repstride0_cross_repeat_broadcast_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F29: level-2 `Mul` 的 `src1RepStride=0` 跨 repeat 广播在特定调用组合下数值错误
## 现象

在 本例算子 的 `DotAdd` 中，把「每个 64 元素 chunk 对 nCnt 行各发一条 `Mul`」合并为
「一条 `Mul` + `repeat=nCnt` + `src1RepStride=0` 让同一权重块广播到所有行」，共尝试 3 种实现

## 根因假设

**根因尚未定**。同 PR 内的两个成功案例说明「跨 repeat 广播」本身在该平台可用：
- `disc_x112.md`（S2Attention）：level-0 `Mul` / `MulAddDst` + 显式位图 mask +
 `BinaryRepeatParams(1,1,1,repS,repS,0)`，广播成功；
- `mla_preprocess_cfg_mdl_and_core_fill_910b2c.md`（MLA rope）：level-0 `Mul` +
 `BinaryRepeatParams(1,1,1,8,8,0)` + 位图 mask，广播成功。

因此差异更可能来自 **level-2 重载的参数组合、mask 形式（标量 vs 位图）、dtype、repeat 参数
或旧编译产物**，而不是 `Mul` 接口本身不支持 `repStride=0`。在拿到完整参数与最小复现前，
不应把本现象泛化为「`Mul` 不能广播」。

## Resolution

- **优先用已验证的 level-0 形式**：`Mul` / `MulAddDst` + 显式**位图** mask +
 `BinaryRepeatParams(..., src1RepStride=0)`（见 X112 与 MLA 卡）；不要用 level-2 `Mul` 的
 `repeat + src1RepStride=0` 组合，除非已在本机复现验证。
- 若必须用 level-2 `Mul`，需附**完整 repeat 参数、输入 dtype、mask 形式、编译命令与最小复现**，
 并解释与 level-0 成功案例的差异；不能把 `MulAddDst` 写成无条件替代方案。
- 判定纪律：此类合并必须先在单个 dtype 的小 case 上跑全量精度，再谈性能；本案 3 次尝试均只省指令数、不省总工作。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f29_vec_mul_repstride0_cross_repeat_broadcast_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

