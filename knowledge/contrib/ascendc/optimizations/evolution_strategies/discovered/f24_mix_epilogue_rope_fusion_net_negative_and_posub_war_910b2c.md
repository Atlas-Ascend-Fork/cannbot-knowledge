---
type: Optimization
title: "F24: 把下游就地旋转（RoPE）融进 GEMM epilogue 的 MIX 融合——精度可修，但净负向"
description: "把下游就地旋转（RoPE）融进 GEMM epilogue 的 MIX 融合，精度可修但净负向；省下的往返不足以抵消融合与同步开销。"
tags:
  - task.debugging
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToUB.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/pipeline_scheduling/pipeline_scheduling.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f24_mix_epilogue_rope_fusion_net_negative_and_posub_war_910b2c.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 mix-epilogue-rope-fusion-net-negative-and-posub-war）。
>
> 原始元数据：
>
> ```yaml
> confidence: single_op
> phenomenon: perf_regression
> severity: medium
> occurrences: 3
> failed_combination: [X113, P17, P1]
> op_families: [matmul, attention, cv-mix, elementwise]
> operator_type: matmul
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/f24_mix_epilogue_rope_fusion_net_negative_and_posub_war_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f24_mix_epilogue_rope_fusion_net_negative_and_posub_war_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F24: 把下游就地旋转（RoPE）融进 GEMM epilogue 的 MIX 融合——精度可修，但净负向

## 现象

「GEMM 输出 → 下游对输出做就地 elementwise 旋转（RoPE/scale/gate）」这类两段结构，
很自然会想把旋转融进 GEMM 的 epilogue：省一次 launch、省一段 `out` 的 GM 往返。

在 本例算子（`out_q[T,128,192]`，对每 head 末 64 通道做 GPT-J RoPE）上
**三次独立尝试**（本轮变体、本轮变体、本轮变体，全部 `MIX_AIC_1_2`
+ `CrossCoreSetFlag/CrossCoreWaitFlag`，AIC 逐 tile fixpipe 后交 AIV 处理该 tile 内的 rope 窗）：

- 精度：前两次 T≤64 全 PASS、T≥128 全 FAIL（`matched_ratio≈0.83`，只错 `out_q` 的 rope 列，

## 根因（两部分，都必须记住）

### 1) 精度根因：「S 读 → MTE2 写」的反向依赖 `--cce-auto-sync` 不覆盖

AIV 侧用**标量** `posUb.GetValue(i)`（S 流水）读位置缓冲，下一个 row-chunk 的 `DataCopyPad`（MTE2）
覆写同一 UB buffer。`--cce-auto-sync` 不会为这条**反向**依赖补同步 ⇒ chunk k+1 读到 chunk k 的残留
⇒ cos/sin 用错行 ⇒ 只有 rope 列错、且从第二个 chunk 起才错。
**这解释了「T≤64 全过、T≥128 才挂」的阈值现象**：T≤64 时每 AIV 只有 1 个 chunk，永不触发。

修复：在每个 row-chunk 末尾加一条 `PipeBarrier<PIPE_ALL>()`（已验证有效）。
**不要**改成显式 `SetFlag/WaitFlag<HardEvent::S_MTE2>(6)` —— 会与 `--cce-auto-sync` 的 event id
冲突，实测直接 aicore timeout（hang）。

### 2) 性能根因：跨核握手成本 > 省下的 GM 往返

付出的是每个 tile 一次 `CrossCoreSetFlag/WaitFlag` 往返 + AIV 侧要按 head 枚举 rope 窗求交
（hd=192，rope 窗在每 192 列里占 64 列）。本例 per-tile 握手次数与 tile 数同阶，成本反超收益。

与 F13（epilogue 融合受 L2 roofline 约束）、F14（多 stream/求和口径）同族：
**融合不是免费的重叠**，它的收益必须大于跨单元同步的固定成本。

## Resolution

1. **先算账再动手**：`省下的字节数 / HBM 带宽` vs `tile 数 × (cross-core flag 往返延迟 + 额外标量枚举)`。
 前者 < 后者时不要做（本例 tile 数 ≫ 1 且跨核 flag 每 tile 一次）。
2. 若仍要做，**必须先把精度通路做对**：任何「标量读 UB buffer + 后续 DMA 覆写同一 buffer」都要在
 chunk 边界加 `PipeBarrier<PIPE_ALL>()`；禁止用显式 S_MTE2 event（与 auto-sync 冲突会 hang）。
3. 更划算的替代：让下游 kernel **按行块 + 2D strided DMA + issue-many/wait-once** 自己跑
 （见 X116 / X112）——本例把 vec2 从 953us 压到 570us 就是这条路的收益，无需融合。
4. 判断「rope 段只占每 384B 中 128B ⇒ 按 512B 行粒度取数 3x 流量放大」这类物理墙时，
 融合也无法绕过它（写侧放大仍在），只能改数据布局，而布局由算子接口固定。

## 证据

- 本轮变体：首版，T≤64 PASS / T≥128 FAIL，回滚。
- 本轮变体：在 `CFG_MDL` 基座上重做（`CubeCore<T,CFG>` 模板避免融合让 G2 退回 CFG_NORM），

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f24_mix_epilogue_rope_fusion_net_negative_and_posub_war_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

