---
type: Optimization
title: 大行宽 UB 溢出防护——H 维度列分块两 pass
description: 当单行工作集超出 UB 时，沿 H 维切列块，并改用 UB 列分块两遍处理
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-ub-column-tiled-two-pass.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：大行宽 UB 溢出防护——H 维度列分块两 pass

> 单一优化点：当单行（row）的完整 UB 工作集超过可用 UB 时，把行宽 H 切分为多个列块，
> 先 pass1 逐列块累计每行的归约量（如 abs-max），再 pass2 逐列块重新加载做变换输出。
> 快/正确的依据：消除了 InitBuffer 静默超 UB 导致的越界写崩溃（vector core 507035），
> 且仅在"整行放不下"的极端大 H 场景触发，不影响常规路径。

本策略适用于任何"按行独立计算 + 行宽可能很大 + 单行 UB 需求超上限"的 kernel，与具体算子无关。

---

## 1. 原理

AscendC 的 `pipe_.InitBuffer` 对超 UB 的分配**不报错**，vector 计算越界写 UB 会触发
`vector core exception`（ACL stream sync 507035）并级联拖垮设备。tiling 若不计算"单行完整
UB 工作集"，大 H 输入就会崩溃。列分块把单行切成 columnTiles 块，每块的 UB 需求降到可用 UB
内；归约量（scale）依赖整行，故需两 pass：pass1 累计各列块的 per-row 归约，pass2 重新加载
量化。扫描量 2×，但只作用于 columnTiles>1 的极端 shape，常规 shape 无损失。

## 2. 性能问题模式

1. tiling 只按 per-row 估算或 baseRowLen 硬编码，未检查"单行 buffer 总和 ≤ UB"。
2. 行宽 H 大（如 H 数千元素、dtype 4B）时单行 UB 需求 ≈ 常数×H 超 192KB。
3. profiling/运行时表现为 vector core 507035 崩溃 + 设备级联不可恢复。
4. 非对齐 H（H 非 32 倍数）时单行 padding 进一步推高需求。
5. **Broadcast 高阶 API tmp 不足 → kernel 卡死**：Broadcast (R,1)->(R,COL) 的 sharedTmpBuffer 需求随 dstShape 变化，tmp 分配不足时 UB 越界写破坏同步、设备不可恢复卡死——大行宽分块路径须同步核算 Broadcast tmp 需求并扩容。

不适用：单行 UB 需求恒小于可用 UB 的常规 shape（此时列分块会白付 2× 扫描）。

## 3. 正确性红线

- **列块宽度与行步长对齐**：列块内所有 buffer 行步长必须一致（统一元素对齐），否则连续 Cast 流错位。
- **末列块宽度**：`colCnt = min(colLen, H - cb*colLen)`，加载/输出只拷 colCnt 列，padding 区必须清零（否则垃圾/NaN 污染归约）。
- **两 pass 同步**：pass1 与 pass2 间、跨列块间需显式事件（MTE2_V / V_MTE3）或 barrier，防数据竞争。
- **归约累计**：pass1 的 per-row 归约要跨列块取 max（勿覆盖），独立 buffer 存累计值。
- **块归约槽 32B 对齐**：slot 偏移须为 8 元素（=32B），偏移 1 元素触发 "UB address not aligned" 507035；大行宽分块模式 DataCopyPad 覆盖 xBlk / 搬出 yBlk 前必须 PIPE_ALL 同步防数据 race；host tiling 与 kernel InitBuffer 的 buffer 预算必须一致。

## 4. 泛化条件

适用（任一）：
- 任意按行独立计算、行宽 H 可超 UB 的算子（dequant/elementwise/融合算子）。
- tiling 能拿到 dtype 与可选 tensor 信息来精确估算单行 UB。

不适用（任一）：
- 行宽恒小、单行 UB 恒够的算子（列分块是纯损失）。
- 归约量不可拆分为"逐列块累计"的算子。

## 5. 实施步骤

1. tiling 计算单行完整 UB 工作集（含 ws/qs 等 fixed buffer），阈值留 headroom 匹配实测崩溃边界。
2. 超限则解 columnTiles（线性扫描取最小满足），colLen 对齐到统一行步长。
3. kernel 增加 Regime B 两 pass 路径：pass1 逐列块 load+计算+abs-max 累计；pass2 重算 scale 后逐列块量化输出。
4. 同步用显式 HardEvent（V_MTE2 / MTE2_V / V_MTE3），勿用全 barrier（实测死锁）。
5. 全量编译，覆盖"崩溃边界±"shape 验证精度与不崩溃，再评估性能。

## 6. LLM 前置问题

- tiling 能否拿到 dtype + 可选 tensor 信息？拿不到就用最坏情况估算。
- 归约量（scale/max）能否拆分为逐列块累计？
- 各 buffer 行步长是否统一元素对齐（防连续 Cast 错位）？

## 7. 验收标准

- 精度：之前崩溃的极端大 H shape 全部通过且不崩溃；常规 shape 无回归。
- 性能：列分块 case 无崩溃即可（两 pass 2× 扫描是必要代价），常规 shape 不退化。

## 检索卡（短卡）

动作：当单行工作集超出 UB 时，沿 H 维切列块，并改用 UB 列分块两遍处理
适用：适用任一：按行独立计算且H可超UB；或tiling可按dtype及可选tensor精确估算单行UB。
限制：列块内所有buffer行步长须统一元素对齐；单行预算须含fixed buffer、保留余量并核验容量边界。
范围：大行宽的 dequant、elementwise 与融合算子按行路径
检索词：UB、H 维列分块、two-pass、InitBuffer、columnTiles、vector core exception
机会：tiling 未校验单行全部 buffer 总和是否不超过 UB
