---
type: Optimization
title: "优化机制卡：存储层次优化（L2/UB/L1/L0 复用与 Bank 冲突规避）"
description: 按存储层次选机制：L2 CacheMode 二分（有复用开 NORMAL、流式数据 DISABLE 防污染）、L1 小侧矩阵驻留（fullload）、L0C 累加不回写、UB 常驻复用（TBuf 替代重复 MTE2）、寄存器驻留；Bank 冲突规避按判定字段（bankgroup/bank/资源/MTE 四类冲突）对应修法。
tags: [task.optimization, topic.performance.analysis, topic.memory, topic.data_movement]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-mechanism/references/optimize/memory-hierarchy.md
    role: primary
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-family/references/common/ub_resident_design.md
    role: supporting
created_at: "2026-11-05T03:50:00Z"
updated_at: "2026-11-05T03:50:00Z"
platforms: [a2, a3, "950"]
---

# 优化机制卡：存储层次优化（L2/UB/L1/L0 复用）

对应判定规则：L1_MTE2_BOUND（真饱和档）、L0_L2_LOW_HIT、L1_VEC_BOUND（UB 往返类）。

## 机制清单（按层次）

| 层次 | 机制 | 适用证据 | 关键约束 |
| --- | --- | --- | --- |
| L2 | `SetL2CacheHint(CacheMode::CACHE_MODE_NORMAL)` | L2 hit <50% 且数据有复用 | — |
| L2 | 只读一次数据 `CACHE_MODE_DISABLE` | 流式数据污染 L2 | 与上一条二分：有复用开 NORMAL，无复用 DISABLE |
| L2 | 工作集切分（访问序改造） | 大工作集整体 miss | L2 参数随 SoC 变化，须重算容量 |
| L1 | B 矩阵/小侧矩阵驻留（fullload） | 小侧 ≤L1/2 + 对侧 T≥2 + 真 MTE2 bound | L1 预算 = 分形 + ping-pong 缓冲 |
| L0 | L0C 累加（多 matmul 累加不回写） | CUBE bound + Fixpipe 高 | 累加链精度（语义变更类） |
| UB | tile/loop 间常驻复用（TBuf 替代重复 MTE2） | 多 tile 重复搬同一数据 | UB 容量 + Bank 冲突规避（padding 32B 整数倍） |
| 寄存器 | 中间值留寄存器/areg | 短生命周期中间量 UB 往返 | 寄存器压力与 spill 反证 |

## UB 常驻复用与 Bank 冲突

常驻复用分两类：**常驻复用**（跨整个 Process 或多层循环的数据——weight、gamma、scale 等小参数，循环外搬入循环内只读）与**分时复用**（单次 Process 内多阶段串行，前一阶段结束下一阶段覆盖）。收益形态：参数搬运次数从每 tile 一次降为 Process 生命周期一次；临时 buffer 总量从 sum(各阶段) 降为 max(并发阶段)。

Bank 冲突规避（常驻复用的伴生问题）——Vector 计算单元在一个 Repeat 周期并行发出多个 DataBlock 读写，多个请求落到同一 bank/bank group 时被串行化，单 Repeat 从 1-2 拍退化到多拍：

| 冲突类型 | 判定字段 | 修法 |
| --- | --- | --- |
| bankgroup | vec_bankgroup_cflt_ratio >3% | 修改 repeatStride/blockStride |
| bank | vec_bank_cflt_ratio >3% | UB tensor 起始地址 + 32B 整数倍 padding |
| 资源 | vec_resc_cflt_ratio >5% | 错开 Vector/Cube 调度 |
| MTE | vec_mte_cflt_ratio >3% | 搬运与计算时序调整 |

不同芯片 UB bank 结构不同（如 DAV_2201 为 192KB / 48 bank / 16 组×3；dav-3510 为 256KB / 16 bank / 8 组×2），冲突条件随结构变化，必须查目标硬件手册。

## 验证与回滚

L2Cache.csv 复采（hit rate 变化）+ verdict 复跑；驻留类改造须核对 L1/L0/UB 三级预算（L1：分形 A + 分形 B + ping-pong 缓冲 ≤ L1 总容量；L0：mL0+nL0+kL0 分域；UB：tile 输入 × bufNum(2) + 输出 ≤ UB 容量）。

## 失效边界

- L2 CacheMode 二分的前提是能判定「有无复用」，访问序不明时先做访问分析；
- L0C 累加改变累加顺序属语义变更类，精度用例必附；
- UB bank 结构与冲突阈值随 SoC 变化，跨平台迁移须重查。
