---
type: Optimization
title: "优化机制卡：MC² 通算融合（Local Matmul 首选 + 通信掩盖 + 膨胀控制）"
description: MC² 优化固定顺序：① Local Matmul 首选（本 rank 数据无需通信，独立计算与通信重叠，任何 R 档位先做）→ ② R 值与 TilingData 驱动的流水配平系统搜索（禁止 1-2 个经验值交付）→ ③ matmul 计算效率（仅计算 bound）；模式选型按执行顺序（Pattern A 通信后计算→前置独立；Pattern B 计算后通信→后置独立），Local 数据段 M 维切分必须连续。
tags: [task.optimization, topic.performance.analysis, topic.data_movement.communication.collective_communication, topic.tiling]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-mechanism/references/optimize/mc2.md
    role: primary
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-mechanism/references/optimize/mc2-balancing.md
    role: supporting
created_at: "2026-11-05T03:50:00Z"
updated_at: "2026-11-05T03:50:00Z"
platforms: ["950"]
---

# 优化机制卡：MC² 通算融合（Local Matmul 首选 + 通信掩盖 + 膨胀控制）

对应判定规则：L3_MC2_BALANCED / COMPUTE_BOUND / STRONG_COMPUTE / COMM_BOUND / STRONG_COMM / L3_MTE2_POLLUTED / L3_RANK_IMBALANCE。

## 策略优先级（与 R 值无关的固定顺序）

```
① Local Matmul（首选，不依赖 Bound 判定）
   本 rank 数据无需通信 → 独立计算与通信重叠。任何 R 档位都先做这一步。
② 流水配平（在 ① 基础上叠加）
   由 R 值与 TilingData 驱动的系统搜索，禁止 1-2 个经验值交付。
③ matmul 计算效率（仅计算 Bound，优先级最低，正交可叠加）
   转 matmul 族优化（pingpong/streamk/fullload）。
```

## ① 的模式选型（按执行顺序）

| 执行顺序 | 推荐模式 | 机制 |
| --- | --- | --- |
| 通信后计算（Pattern A，如 alltoall+matmul） | 前置独立 | LocalMatmul 先执行，与首次通信重叠隐藏通信延迟 |
| 通信后计算且通信量小 / Local 占比小 | 融合 | self rank 在通信块循环内一起算 |
| 计算后通信（Pattern B，如 matmul+alltoall） | 后置独立 | 通信块只算远程 rank，Local 后置不冲突 |
| 计算后通信且通信量小 | 融合 | 同上 |

**Local matmul 连续性约束**：前置/后置模式下 Local 数据段的 M 维切分必须连续（否则 WaitFlag 顺序与数据顺序错位）。

## ② 流水配平：长短块排布的系统搜索

MC² 算子 = AIC（matmul 计算）+ AIV（UDMA/SHMEM 通信）分离架构，同步方向由执行顺序决定（Pattern A：AIV CrossCoreSetFlag → AIC WaitFlag；Pattern B：AIC NotifyComputeComplete → AIV Wait）。配平改变的是**长短块排布**（长块 = 大 M 计算块，短块 = 小 M 计算块），使计算块耗时分布与通信块节奏互补。

搜索算法（配平比 ρ = max(R, 1/R)）：搜索空间为长块 M 候选集 × 短块 M = 长块 M/ρ（对齐修正）× 块数切分方案；**四条剪枝**：① 核利用率不下降；② L1/L0 容量不超预算；③ 计算膨胀+通信膨胀估算不超收益；④ M/N/K 对齐约束（512B/分形对齐）。输出 Top-N 候选 → 逐个实测（tileCnt 扫描）→ 按跨 rank max 口径择优。执行载体为工具仓 mc2_search.py 脚本。

## ③ 与膨胀控制

matmul 计算效率转族优化机制。**膨胀控制**：配平/融合带来的额外计算与通信开销（膨胀）须最小化瓶颈方膨胀——R 档位判定给出方向后，非瓶颈方可以接受膨胀换取掩盖。

## 验证与失效边界

- 掩盖率 = (融合前耗时−融合后耗时)/min(T_comm,T_compute)；跨 rank 一律取 max 口径（平均口径系统性高估收益）；
- R 值随 shape/量化/rank 数剧烈变化（实测跨 0.3~9.8），每 case 必须隔离测试实测；
- MTE2 污染（L3_MTE2_POLLUTED）命中时单核访存机制全部无效，本卡是唯一改道方向；
- 平台边界：本卡机制标定仅 950（MC²/SHMEM 路径）；a2/a3 未验证不入 platforms。
