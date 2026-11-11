---
type: Optimization
title: "X52: Host 数据通路消除（reshape-materialization 消除 + 条件 at::empty + 单 pass strided-gather transpose）"
description: "融合 GQA/FA 管线的 host 侧常为 host-overhead-bound：permute().reshape() 强制物化转置、at::zeros 在无 padding 区时浪费 launch、每 forward 重建 mask 常量缓冲。用单 pass strided-gather copy_ 替代 permute+reshape+copy_，按 Dm%64==0 或 hd==Dp 条件使用 at::empty，并以 shape-keyed cache 复用 mask，可减少 host launch 与 GM 往返。"
tags:
  - task.optimization
  - topic.data_movement.layout_transform
  - topic.memory
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X52: Host 数据通路消除（reshape-materialization 消除 + 条件 at::empty + 单 pass strided-gather transpose）

## 核心思路
融合 GQA/FA 管线 host 侧是 host-overhead-bound 的（torch ops + launch 开销可与 kernel 时间同量级甚至更高）。host 侧每 forward 有大量中间张量物化：
1. `permute().reshape()` 非连续视图强制先物化转置再 copy_——同一转置 GM 往返 2 次。
2. `at::zeros` 零填充在无 padding 区时是纯浪费 launch。
3. 每 forward 重建 shape 无关的常量（mask）缓冲。

三管齐下消除：单 pass strided-gather copy_ 替代 permute+reshape+copy_；条件 at::empty（Dm%64==0 或 hd==Dp 时安全）；shape-keyed mask cache。净效果是减少 host launch 与 GM 往返，不新增 kernel。

## 适用场景
- 融合管线 host 侧有 permute/reshape/transpose 中间物化、每调用 at::zeros、重复重建 mask
- host-overhead-bound（小 shape / launch 密集）算子
- 与 X39（workspace at::empty）、X35（MatmulImpl host 开销消除）互补

## 实现要点
1. 单 pass strided-gather `view({...}).copy_(permutedView)` 替代 permute+reshape+copy_，删除前置物化。
2. 条件 at::empty 守卫：`Dm%64==0` 或 `hd==Dp` 时安全（无 pad 列）；M-row 尾块死行论证（下游不读、row-isolated）。
3. shape-keyed mask cache：mask 是 (S,kvPad) 纯函数，跨调用复用。
4. dead workspace（如 `(void)ws3`）替换为缓存 dummy。
5. 收益是删除 kernel（不新增），理论上不回归设备时间；精度必须全量通过。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
