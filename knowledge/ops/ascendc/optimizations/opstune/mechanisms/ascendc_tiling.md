---
type: Optimization
title: "优化机制卡：Ascend C Tiling 优化（切分与多核负载）"
description: 切核不足时 Block Dim 提升是最低垂果实（4 核→20 核案例利用率 10%→50%）但 Task <25us 时增核放大头开销；核间长尾走尾块均衡（swat 蛇形行窗口+尾块合并+末轮再切分）；MN 欠并行走 streamk（切 K 到空闲核）；多机制候选冲突时先做三层联动 tiling 建模再选单变量。
tags: [task.optimization, topic.tiling, topic.performance.analysis, topic.programming_model]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-mechanism/references/optimize/ascendc-tiling.md
    role: primary
created_at: "2026-11-05T03:50:00Z"
updated_at: "2026-11-05T03:50:00Z"
platforms: [a2, a3, "950"]
---

# 优化机制卡：Ascend C Tiling 优化（切分与多核负载）

对应判定规则：L2_CORE_TAIL、L2_IMBALANCE_*、L2_UNDERUTILIZATION、L1_MTE2_BOUND（tile 尺寸侧）。

## 机制清单

| 场景 | 机制 | 说明 |
| --- | --- | --- |
| 切核不足 | Block Dim 提升 | 最低垂果实：4 核→20 核案例利用率 10%→50%；但 Task <25us 时增核放大头开销，须权衡 |
| 核间长尾 | 尾块均衡 | 数据总量不整除核数时尾块分散到更多核 |
| 长尾持续 | block swat / 尾轮均衡 | 蛇形行窗口 + 尾块合并 + 末轮二维再切分；两簇检测（前后半段核均值差 ≥2%）提示 NUMA/L2 slice 偏斜时优先 |
| 搬运次数多 | 增大 tile | mte2_instructions 过大时（与 UB 预算联动） |
| MN 欠并行 | streamk（SK/DP+SK） | totalBlockCnt < aicNum + K 长：切 K 到空闲核，AIV 归约（matmul 族） |
| 尾碎片不均 | swat | MN 够并行（>aicNum 数倍）但尾碎片负载不均 |

## Tiling 理论建模（多机制联动时的前置）

卡间切分 ↔ 核间切分 ↔ 单核 Buffer 规划**三层联动**（跨层耦合）：改一个 baseM 同时影响通信粒度、核利用率、L1/L0 容量。多机制候选冲突时先做 tiling 建模再选单变量：

```
建模输出：卡间切分 / 多核切分（Cube: L1+L0 split；Vec: UB split）
        / Buffer 规划（L1/L0/UB 分层）/ 分支场景覆盖（dtype/shape/对齐）
```

各族理论模型与 fallback 载体在工具仓 ops-family（matmul/mc2/reduce/elementwise/broadcast/conversion/sort/simt/scalar/fa），按族 guide 选型；族范式 guide 在算子族批次迁入知识库。

## 验证与回滚

- 切分改动后同口径 verdict 复跑：occupancy / imbalance 指标变化为机制生效证据；
- 容量预算破坏（L1/L0/UB 超限）会直接 device fault——tile 增大前先做三级预算核算；
- 候选参数不再经验拍：按 soc-spec 容量约束产出候选表 + 逐候选容量占用（工具仓 tiling_candidates.py 脚本承载）。

## 失效边界

- Block Dim 提升与头开销的权衡以 Task Duration 为判据（<25us 谨慎增核）；
- streamk/swat 等 matmul 族策略间构成互斥判定树（见算子族批次），不「全都加上」；
- tiling 建模是前置决策工具不是收益承诺，最终以单变量实测为准。
