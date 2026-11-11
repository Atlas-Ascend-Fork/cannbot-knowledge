---
type: Optimization
title: "L2 核间层瓶颈判定规则语义（长尾/离散度/切核不足/头开销/host 下发）"
description: 核间层判定六条：L2_CORE_TAIL（max > mean×1.25 判长尾，带 NUMA 两簇反证）、L2_IMBALANCE_MILD/SEVERE（(max-min)/max 10~30% 警告 / >30% 严重）、L2_UNDERUTILIZATION（block 行数 < 物理核 33% 判切核不足，Task <25us 时增核反证）、L2_HEAD_OVERHEAD（TaskDuration−最慢核 >30%）、L2_HOST_DISPATCH_BLOCK（下发间隙 >50us 且占比 >30%，规划态）。
tags: [task.optimization, task.debugging, topic.performance.analysis, topic.tiling]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-verdict/rules/L2-inter-core.yaml
    role: primary
created_at: "2026-11-05T03:20:00Z"
updated_at: "2026-11-05T03:20:00Z"
platforms: [a2, a3, "950"]
---

# L2 核间层瓶颈判定规则语义

核间（多核负载分布）层判定六条规则。机器真源为来源固定的规则 YAML；本卡保存判定语义、反证与阈值溯源。输入为各核执行耗时（time_mean/max/min_us）、CSV 行数（row_count，即 block 数）、物理核数与 Task Duration。

## 判定条件

| 规则 | 判定条件 | 说明 |
| --- | --- | --- |
| L2_CORE_TAIL | time_max > time_mean × 1.25 | 核间长尾：最慢核拖住整体（木桶） |
| L2_IMBALANCE_MILD | 不均衡度 (max−min)/max 在 10%~30% | 离散度警告档 |
| L2_IMBALANCE_SEVERE | 不均衡度 >30% | 离散度严重档 |
| L2_UNDERUTILIZATION | row_count > 0 且 < physical_cores × 0.33 | 切核不足（occupancy 可疑） |
| L2_HEAD_OVERHEAD | 头开销占比 >30% | 头开销 = TaskDuration − 最慢核主体时间（木桶口径） |
| L2_HOST_DISPATCH_BLOCK | host_dispatch_us > 50 且占 task_duration >30% | host 下发阻塞（scene=cluster 专用档，规划态） |

## 反证与警示

- **L2_CORE_TAIL 的 NUMA 反证**：前后半段核均值差距 ≥2%（`__two_cluster_gap_pct > 2`）提示 NUMA/L2 slice 负载偏斜——block swat（蛇形行窗口）/ 尾轮均衡优先于普通长尾处置；
- **L2_UNDERUTILIZATION 的短任务反证**：Task < 25us 时增核可能放大头开销（A2 满核头开销约 20-21us），需权衡——数据量小时少核 = 少头开销；
- **L2_HEAD_OVERHEAD** 语义：占比 >30% 说明数据量太小或核数太多，先减核再谈其它优化；
- **L2_HOST_DISPATCH_BLOCK** 是集群视角的 host 侧证据：下发阻塞（launch → task start 的 host 间隙）主导时算子侧优化收益有限，先解 host 下发（流组织 / launch 合并 / host 占用）。该规则为规划态（缺真实集群数据标定）。

## 阈值溯源与收益预期

| 规则 | 阈值来源 | speedup 预期 |
| --- | --- | --- |
| L2_CORE_TAIL | [tuning-practice] max > mean×1.25；离散度三档 | 1.05~1.3x 🟡 |
| L2_IMBALANCE_MILD / SEVERE | [tuning-practice] (max-min)/max 10~30% / >30% | 1.0~1.1x / 1.1~1.5x 🟡 |
| L2_UNDERUTILIZATION | [tuning-practice] block 行数 ≪ 物理核数；Block Dim 不足是最常见低垂果实 | 1.2~3.0x（4→20 核案例 4.75x 区间下界保守化）🟡 |
| L2_HEAD_OVERHEAD | [tuning-practice] 头开销占比 >30% | 1.05~1.2x 🟡 |
| L2_HOST_DISPATCH_BLOCK | 🟡 初值占位（首个集群场景实战后标定） | 1.0~1.2x 🟡 待标定 |

## 机制路由与失效边界

- 命中后路由 Tiling 优化机制（尾块均衡 / swat / Block Dim 提升）；L2_HEAD_OVERHEAD 路由 API 使用优化（减核 / 缩 TilingData / TPipe 外置）；
- 切核不足是最常见「最低垂果实」，但必须过短任务反证——Task 极短时增核反而放大头开销；
- row_count 取自 CSV 数据行数：`aic_*` 整列 NA（未用 Cube 核）时行数口径按有效行计；
- 阈值变更只改规则 YAML + evals 回归，本卡随后同步。
