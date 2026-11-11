---
type: Optimization
title: "L1 单核层瓶颈判定规则语义（MTE2/Cube/Vec/MTE3/FixP/Scalar/低占用/串行指纹）"
description: 单核 pipe 级 Bound 判定：MTE2 均值 >80%（或 >70% 且主导）判搬入瓶颈并带真带宽饱和/假 bound/对齐三条反证；Cube/Vec >80% 或 70%+主导判计算瓶颈（Vec 带 bank conflict 与 fp32 Cast 反证）；Scalar >80% 判标量瓶颈；全 pipe <50% 判 LATENCY/SYNC 可疑；max<70% 且 pipe 求和 85~115% 判串行无重叠指纹。阈值四级溯源，🟡 未标定项以 draft 交付。
tags: [task.optimization, task.debugging, topic.performance.analysis, topic.tiling]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-verdict/rules/L1-single-core.yaml
    role: primary
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-mechanism/references/optimize/index.md
    role: supporting
created_at: "2026-11-05T03:20:00Z"
updated_at: "2026-11-10T03:05:00Z"
platforms: [a2, a3, "950"]
---

# L1 单核层瓶颈判定规则语义

单核 pipe 级 Bound 判定的八条规则（L1_MTE2_BOUND / L1_CUBE_BOUND / L1_VEC_BOUND / L1_MTE3_BOUND / L1_FIXP_BOUND / L1_SCALAR_BOUND / L1_LATENCY_SYNC_SUSPECT / L1_SERIAL_NO_OVERLAP）。机器真源为来源固定的规则 YAML（判定引擎按其求值）；本卡保存判定条件语义、反证与阈值溯源，阈值以 YAML 为准，本卡变更不自动生效。

## 判定条件与聚合语义

指标来自 PipeUtilization.csv 逐 block 数据（列名兼容 aic_/aiv_ 双前缀与旧版百分数格式；ratio 类 0~1.5 视为比例 ×100 归一）。聚合口径：`mean` 用于判定（均值代表整体水位）、`rank=1` 表示主导 pipe（按 pipe 排序聚合）、`max` 用于长尾观察。派生指标 `__max_pipe_mean` = 各 pipe 均值最大值；`__pipe_sum_mean` = 各 pipe 均值求和（串行指纹用）。

| 规则 | 判定条件 | watch 档 |
| --- | --- | --- |
| L1_MTE2_BOUND | mte2_ratio 均值 >80%，或 >70% 且为主导 pipe | >50% 关注 |
| L1_CUBE_BOUND | cube_ratio 均值 >80%，或 >70% 且主导 | >40%（MatMul 类正常水位） |
| L1_VEC_BOUND | vec_ratio 均值 >80%，或 >70% 且主导 | 50~70% 已有收益空间 |
| L1_MTE3_BOUND | mte3_ratio 均值 >80%，或 >70% 且主导 | — |
| L1_FIXP_BOUND | fixpipe_ratio 均值 >80% | >15% 即 512B 对齐预警 |
| L1_SCALAR_BOUND | scalar_ratio 均值 >80%，或 >70% 且主导 | >30% 查 TilingData 体积与核数 |
| L1_LATENCY_SYNC_SUSPECT | 全部 pipe 均值 <50%（`__max_pipe_mean < 50`） | <30% 重度等待 |
| L1_SERIAL_NO_OVERLAP | max pipe <70% 且 pipe 求和在 85~115% 之间 | 串行指纹 |

## 反证条目（BOUND 类规则卡无反证不允许合入）

**L1_MTE2_BOUND 三条反证**（先分真假 bound 再选机制）：

| 反证 id | 条件 | 含义与改道 |
| --- | --- | --- |
| true-bandwidth-saturation | mte2_active_bw 占峰值 >80% | 真带宽饱和：优化在数据量削减/复用，不在搬运组织 |
| fake-mte2-small-packet | mte2_active_bw <峰值 40% | busy 高但带宽低：疑似小包/非对齐/频繁同步（假 bound），优先对齐/合并小搬运 |
| fixpipe-misalignment | fixpipe_ratio 均值 >15% | GM 地址未 512B 对齐问题叠加 |

**L1_CUBE_BOUND**：cube_ratio >85% 时须用 aic_cube_fops 折算理论利用率排除空转指令。**L1_VEC_BOUND**：vec_total_cflt_ratio >5% 时先解 Bank conflict 再谈向量化；vec_fp32_ratio >60% 时减 Cast 优先（存在大量 fp16→fp32 转换）。**L1_SCALAR_BOUND**：scalar >90% 且 vec/mte 低 → 标量访问/地址计算主导，查指针运算与分支。**L1_LATENCY_SYNC_SUSPECT**：pipe 求和在 85~115% = 串行无重叠指纹，Double Buffer / 流水掩盖是首选机制。

## 阈值溯源（四级标注）

阈值来源列记录 Bound 命中条件与 watch 条件的实际语义（以规则 YAML 的 condition 为准；来源 YAML 注释里的文案如有歧义，以本表区分后的口径为准）。

| 规则 | 阈值来源 | 备注 |
| --- | --- | --- |
| L1_MTE2_BOUND | [msprof-doc] >80% 直接判 / 最大且 >70%；watch 50% 档 [tuning-practice] | 反证 40%/80% 为工程折算 🟡 |
| L1_CUBE_BOUND | [msprof-doc] | — |
| L1_VEC_BOUND | [msprof-doc] 主判定表；50-65/65-80/>80 三档 [tuning-practice] | UB 融合 20-50% / 减 Cast 10-30% 收益 🟡 待校准 |
| L1_MTE3_BOUND / L1_FIXP_BOUND | [msprof-doc] >80% 判 bound；>15% 对齐预警 [tuning-practice] | 🟡 |
| L1_SCALAR_BOUND | [tuning-practice] Bound 命中条件为 scalar_ratio 均值 >80%，或 >70% 且排名第一；>30% 仅是 watch 档（查 TilingData 体积与核数） | 来源 YAML 的 threshold_source 注释文案写作「>30% 判定」，与执行 condition 不一致——注释不能当作有效判定阈值；>90% 地址计算方向 🟡 |
| L1_LATENCY_SYNC_SUSPECT | [tuning-practice] 全 pipe busy 均值 <50% 不是「无 bound」 | Double Buffer 类收益 1.2~2.5x 🟡 |
| L1_SERIAL_NO_OVERLAP | [tuning-practice] cube 0.44+mte2 0.42+mte1 0.18≈1 案例 | 单缓冲→双缓冲典型收益 1.3~2.0x 🟡 |

标注口径：`[msprof-doc]` = msprof 官方文档与 CSV 字段说明；`[tuning-practice]` = 一线调优实践沉淀（A2/A5 真机案例标定）；🟡 = 首期标定值（未独立复测）。

## 跨芯片差异

a2/a3 同为 DAV_2201 微架构（阈值共享）；950（dav-3510）列名走 aic_/aiv_ 双前缀，AIV 上 SIMT 场景 scalar_ratio 可与 vec/mte 并行超 100%——pipe 求和口径按串行假设解释时须先确认无 SIMT 并行重叠。950DT/950PR SKU 差异见平台知识（[Ascend 950DT 与 950PR 差异](../../../../../common/platforms/concepts/ascend950dt_vs_pr_overrides.md)）。

## 机制路由与失效边界

- 命中后按 mechanism_refs 路由机制卡：MTE2/MTE3/FIXP → 数据搬运优化（真假 bound 二分）；CUBE → Tiling/多核切分；VEC → API 使用/流水/RegBase VF（A5 深度档）；SCALAR → 标量削减六法；低占用/串行指纹 → 流水优化（Double Buffer 全形态）；
- 被 L3_MTE2_POLLUTED 命中时 L1_MTE2_BOUND 禁用（MTE2 含通信等待空转，单核访存优化无效，改道通信掩盖）；
- 指标缺失（CSV 无该列）时规则按绑定契约 SKIPPED，不能视作未命中；
- 阈值变更只改规则 YAML + evals 回归，本卡随后同步。
