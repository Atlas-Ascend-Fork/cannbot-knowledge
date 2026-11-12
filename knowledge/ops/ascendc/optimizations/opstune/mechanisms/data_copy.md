---
type: Optimization
title: "优化机制卡：数据搬运优化（MTE2/MTE3 真假 bound 二分 + 11 项机制清单）"
description: 先分真假 bound 再选机制：实际耗时≈理论（active_bw ≥峰值 80%）为真带宽饱和，走数据量削减（增大搬运量/L2 CacheMode/UB 常驻/增大 tile）；active_bw <40% 峰值为假 bound，走搬运组织（512B 对齐/合并小搬运/避免同地址多核访问）；11 项机制清单各带适用条件与检查方式；MC² 算子先过 L3_MTE2_POLLUTED。
tags: [task.optimization, topic.performance.analysis, topic.data_movement.data_copy, topic.alignment]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-mechanism/references/optimize/data-copy.md
    role: primary
created_at: "2026-11-05T03:50:00Z"
updated_at: "2026-11-05T03:50:00Z"
platforms: [a2, a3, "950"]
---

# 优化机制卡：数据搬运优化（MTE2/MTE3 真假 bound 二分）

对应判定规则：L1_MTE2_BOUND、L1_MTE3_BOUND、L1_FIXP_BOUND。核心方法：**先分真假 bound，再选机制**——判定引擎的反证条目给出方向，机制卡只做实施。

## 原理与二分

```
理论 MTE2 耗时 = GM_to_UB_datas(KB) × 1024 / GM 峰值带宽
实际 MTE2 耗时 = ai*_mte2_time(us)

实际 ≈ 理论（差 <20%，或 active_bw ≥ 峰值 80%）→ 真带宽饱和：
  机制方向 = 削减数据量（复用/驻留/更小 dtype）与减少搬运次数（增大 tile）
实际 >> 理论（active_bw < 40% 峰值）→ 假 bound（搬运组织问题）：
  机制方向 = 合并小搬运 / 对齐 / 缓解同步
```

## 机制清单

| # | 机制 | 适用条件 | 检查方式 |
| --- | --- | --- | --- |
| 1 | 增大单次搬运量 | 单次 <16KB | GM_to_UB_datas / mte2_instructions |
| 2 | 512B 地址对齐 | fixpipe_ratio >5~15% | PipeUtilization fixpipe_ratio |
| 3 | 合并小搬运 | 多次 <20KB 小块合并成一次大 MTE2 | scaleKL1 = SCALE_L1_BUFFER_NUM × kL1 |
| 4 | L2 CacheMode | L2 hit <50% | L2Cache.csv；只读一次的数据 CACHE_MODE_DISABLE 防污染 |
| 5 | UB/TBuf 常驻复用 | 多 tile 重复从 GM 搬同一数据 | Bank 冲突规避与常驻联动设计 |
| 6 | Double Buffer | MTE 与计算串行 | 转流水优化机制卡 |
| 7 | 增大 tile | 搬运次数过多 | mte2_instructions 过大 |
| 8 | 避免同地址多核访问 | 各核 mte2_time 差异大 | 跨核共享读改广播/分片 |
| 9 | L2 复用（带宽未打满时） | 实际带宽/峰值 <80% 且有复用 | tile 调大使数据驻留 L2；相邻核处理相邻数据共享缓存行 |
| 10 | 基本块选型（stride 消除） | 搬移指令序列含高 stride | 重构数据布局/选连续大粒度搬移指令 |
| 11 | 原地消费 | 搬入搬出成对出现且无中间消费方 | UB 内数据可直接消费的不搬出再搬入 |

## 适用前提与路由顺序

- verdict 命中 L1_MTE2_BOUND（severity 分档决定投入深度）；
- **反证条目必须先读**：true-bandwidth-saturation 命中 → 只走 1/4/5/7（数据量侧）；fake-mte2-small-packet 命中 → 优先 2/3/8（组织侧）；
- **MC² 算子先过 L3_MTE2_POLLUTED**：污染为 true 时本卡全部机制无效，转 MC² 通信掩盖机制。

## 验证与回滚

同口径性能 + 搬运指标复采：mte2_active_bw 上升（组织侧修复）或 mte2_instructions 下降（数据量侧修复）为机制生效证据；精度用例随语义变更（dtype 缩小）必附；噪声带内 revert。

## 失效边界

- 反证条目缺失（active_bw 标量未提供）时二分不可评估，按 severity 谨慎投入；
- L2 CacheMode 参数随 SoC 变化，容量与模式须按目标芯片核对；
- 跨 DSL 实施时以工具侧跨 DSL 原语对照表路由到对应 DSL 专项文档，不按本卡字面照搬。
