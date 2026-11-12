---
type: Optimization
title: "优化机制卡：流水优化（Double Buffer / 流水掩盖 / 同步降本）"
description: 单缓冲下 MTE 搬运与计算串行（pipe 求和≈100% 但各 pipe 均不满）判串行无重叠指纹，双缓冲把搬运与上tile计算重叠，理想收益上界 ≈ max(t_copy,t_compute)/(t_copy+t_compute)；分场景实施形态（TQue 标准流水 / 裸 MTE ping-pong / Cube-Vector 混合 workspace 份数 / AIC:AIV 配比 / 同步删减）；无 Bound 形态六机制与回滚条件。
tags: [task.optimization, topic.performance.analysis, topic.implementation.pipeline]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-mechanism/references/optimize/pipeline.md
    role: primary
created_at: "2026-11-05T03:50:00Z"
updated_at: "2026-11-05T03:50:00Z"
platforms: [a2, a3, "950"]
---

# 优化机制卡：流水优化（Double Buffer / 流水掩盖 / 同步降本）

对应判定规则：L1_SERIAL_NO_OVERLAP、L1_LATENCY_SYNC_SUSPECT、L1_FIXP_BOUND（气泡相关）、L0_STALL_DOMINANT。机制卡按 verdict findings 路由加载（证据先行：没有判定不加载机制卡）。

## 原理

单缓冲下 MTE 搬运与计算串行：pipe busy 求和 ≈100% 但各 pipe 均不满——「串行无重叠指纹」（判定规则 L1_SERIAL_NO_OVERLAP 命中即此形态）。双缓冲把 tile 搬运与上一 tile 计算重叠，理想收益上界 ≈ max(t_copy, t_compute) / (t_copy + t_compute)。

## 适用前提

- verdict 命中 L1_SERIAL_NO_OVERLAP 或 LATENCY/SYNC 可疑 + 反证「串行指纹」；
- UB/L1 容量预算：双缓冲 = 2×tile 缓存，须核对 TilingData 的 buffer 规划（DB 使能时实际可用 UB 减半）；
- 循环内无跨 tile 数据依赖（有依赖需先做依赖分析或改滚动窗口）。

## 实施形态（分场景）

| 场景 | 形态 | 关键点 |
| --- | --- | --- |
| TQue 标准流水 | `InitBuffer(queue, 2, size)` | bufNum=2；EnQue/DeQue 配对；循环内无多余 Sync |
| 非 TQue（裸 MTE + 事件） | ping-pong 两组 UB + event id | 须自行论证 prologue/drain 段（已知知识缺口，验证强度需提高） |
| Cube-Vector 混合 | workspace 份数 2→4 | 减少 Cube/Vector 互等 |
| AIC:AIV 配比 | 1:1 → 1:2 | Cube/Vector 耗时严重不匹配时收益最大 |
| 同步删减 | 删除经依赖证明冗余的 SetFlag/WaitFlag/barrier | 每删一处必须给出依赖论证（精度/正确性风险点） |

## 无 Bound 形态（NO_BOUND_FOUND / 全 pipe 低占用）

各单元利用率均不高、无明显单一瓶颈时，流水化优先于单点优化，六机制按序尝试：① PingPong 粒度调优（确保计算时间 ≥ 搬运时间，否则 DB 反而暴露搬运瓶颈）；② MMAD→Fixpipe UnitFlag 同步（硬依赖场景替代显式 Barrier）；③ 减少单次搬运量（边算边搬不积压）；④ Preload 窗口（当前计算未完成时启动下一批搬入；搬完算没完 = 白搬）；⑤ 指令提早发射（搬移指令不等当前计算完全结束）；⑥ Vec 融合减重复搬运（同一数据多次搬入场景寄存器内连续处理）。

trace 判读：MTE2 全在前、VECTOR 全在后 = DB 未生效；交替出现 = 流水健康。

## 验证与回滚

- 精度全量（工程现有测试，禁止自创容差）+ 同口径性能（与基线同 timing_method/warmup/repeat）；
- 机制生效证据：MTE 与计算重叠比例 >30%（部分 10-30%，未生效 <5%）；无 trace 设施时用 `__pipe_sum_mean` 下降或 L1_SERIAL_NO_OVERLAP 转 NOT_HIT（间接指纹，报告标注「重叠度为间接推断」）；
- 回滚条件：speedup < 1.05（噪声带内）→ 加采样轮次复测，仍带内 → revert；精度任一 case fail → revert（该轮性能数字不进报告）；容量联动被破坏（tile 改动后 device fault）→ revert + 缩小改动粒度 + msSanitizer 定位。

## 失效边界

- 同管道 V barrier 删除在饱和管道无收益（吞吐饱和非杠杆时先判延迟停滞 vs 吞吐饱和）；
- 模板资产（scalar/elementwise 族设计文档）留工具仓 ops-family，不随本卡迁移；相关族 guide 见算子族批次。
