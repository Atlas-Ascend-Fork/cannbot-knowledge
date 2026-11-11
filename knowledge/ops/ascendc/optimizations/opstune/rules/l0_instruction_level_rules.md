---
type: Optimization
title: "L0 指令级判定规则语义（ICache 缺失 / L2 命中率 / PC 采样 stall 枚举）"
description: 指令/源码层三条规则：L0_ICACHE_MISS（icache_miss_rate >15%，msprof 官方口径）、L0_L2_LOW_HIT（l2_hit_rate <50%，转 CacheMode 二分与工作集切分）、L0_STALL_DOMINANT（PC 采样 top stall 枚举占比 >40%，M2 启用占位）；无 Roofline 产物时不得推断 Roofline Bound。
tags: [task.optimization, task.debugging, topic.performance.analysis, topic.memory]
status: draft
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-verdict/rules/L0-instruction.yaml
    role: primary
created_at: "2026-11-05T03:20:00Z"
updated_at: "2026-11-05T03:20:00Z"
platforms: [a2, a3, "950"]
---

# L0 指令级判定规则语义

指令/源码层判定（PC 采样 / 仿真路径）三条规则，依赖 PipeUtilization 的 icache_miss_rate、L2Cache.csv 的 ai*_total_hit_rate 与 PC 采样（PcSampling，如 scoreboard_not_ready 等 stall 枚举）。

## 判定条件与阈值溯源

| 规则 | 判定条件 | 阈值来源 | 机制路由 |
| --- | --- | --- | --- |
| L0_ICACHE_MISS | icache_miss_rate >15% | [msprof-doc] 官方口径「>15% 需关注」 | API 使用优化（代码布局/分支整理） |
| L0_L2_LOW_HIT | 0 ≤ l2_hit_rate < 50% | [tuning-practice] <50% | 存储层次优化（CacheMode 二分 + 工作集切分） |
| L0_STALL_DOMINANT | top_stall_pct >40% | 🟡 PcSampling 字段口径 M1 末期标定（占位，M2 启用） | 流水优化（stall 枚举 → 对应流水机制） |

L0_STALL_DOMINANT 当前为占位规则（confidence: low，speedup 1.0~1.2x 🟡 待标定）：PC 采样 stall 枚举包括 M2 扩展的 SIMT/VF 档（divergence_stack_spill / register_bank_conflict / warp_level_sync 等）。

## 收益预期与失效边界

- L0_ICACHE_MISS：1.0~1.1x 🟡 首期标定值；L0_L2_LOW_HIT：1.1~1.4x [tuning-practice] L2 CacheMode 方法 🟡 待校准；
- **无 Roofline 产物时不得推断 Roofline Bound**（L0 层纪律）；
- PcSampling 数据来自 npu-compute `.npu-rep` 解包的 summary.db（msopprof 产物无此表，L0 档跳过并如实标注）；
- 本卡为 draft：L0_STALL_DOMINANT 阈值未标定，待 PC 采样字段口径在 M1 末期标定后升 stable；
- 阈值变更只改规则 YAML + evals 回归，本卡随后同步。
