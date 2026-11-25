---
type: Optimization
title: "X123: 按模 aicCores 取整补齐 cube 核占用"
description: "当 totalBlock = mTotal*nTotal 小于 AIC 核数时，取最小正整数 k 使 (k*nTotal) % aicCores == 0（即 k*nTotal 成为 aicCores 的整数倍）来补 mTotal，并用最小 singleCoreM 门控挡住小 M；早期「收缩 nTotal 降 A 重读」的路径已被后续实验否定。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.memory
  - topic.tiling
  - topic.alignment
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/tiling_strategy/inter_core_load_balance.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x123.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X123）。
>
> 原始元数据：
>
> ```yaml
> id: X123
> origin: discovered
> confidence: single_op
> op_families: [matmul, cube, moe, attention]
> bottlenecks: [tiling_imbalance, mte2_stall]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x123.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x123.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X123: 按模 aicCores 取整补齐 cube 核占用（或反向收缩 nTotal 降 A 重读）

## 判据（先打印 tiling，别靠猜）

```
totalBlock = mTotal * nTotal, mTotal = ceil(M/singleCoreM), nTotal = ceil(N/singleCoreN)
```

若 `totalBlock < aicCores` 或 `totalBlock % aicCores != 0`，就有核在空转；空转比例 =
`(aicCores*ceil(totalBlock/aicCores) - totalBlock) / (aicCores*ceil(...))`。

实测（`M=8192, N=2112, K=5120`，Ascend910B2C，CANN 8.5.1）：
`base=128x256x64, singleCoreM=4096, singleCoreN=256, mTotal=2, nTotal=9` ⇒ **totalBlock=18，

⚠️ 前提：**先确认瓶颈是「每核字节数 makespan」而不是「聚合 L2 带宽」**。判据是
`(nTotal*M + mTotal*N)*K*2 / 实测耗时` 是否已接近有效 L2 带宽。本例拆分后 makespan 从 44.3MB/核
⇒ 确认是 makespan 受限，不是聚合带宽受限。

## 两种互补整形

### (a) 增加 mTotal 补齐核占用（本例 G1）

取 `nTot = ceil(N/sN)`，找最小 `k` 使 `k * nTot ≡ 0 (mod aicCores)`，
`candM = AlignUp(ceil(M/k), baseM)`，并加**最小 singleCoreM 门控**（本例 `candM >= 1024`）：
小 M 时 B 的重复读不划算，必须挡住。

### (b) 收缩 nTotal 减少 A 重读（**后续实验已否定，勿作为当前推荐**）

早期假设：`singleCoreN = k*baseN` 让 `nTotal` 变小、每核 1 块（`nTotal 9 → 3`，singleCoreN=768=3×baseN），
A 的重读次数从 9 次降到 3 次（A 流量 756MB → 252MB）。

后续同算子的续跑实验否决了该假设：A 面板的 MTE2 重读粒度是 **baseN 而不是 singleCoreN**
（MDL 调度对每个 (m-base, n-base) 对重跑整条 K 循环，L1 环形缓冲只有 `depthA1` 块，跨 n 留不住长 K），
因此 `nTotal` 减少并不降低 A 总搬运量；代价是每核 3 块压成 1 块、失去块间重叠。
⇒ 本路径标记为**已否定的早期假设**，只保留 (a) 的整除对齐作为当前方案。

## 实现要点

- 必须**显式指定几何**再 `GetTiling`（或走 `SetSingleShape` 让 API 重算 step/depth），
 不能 `GetTiling` 之后手工改 `singleCoreM/N`——那样 step*/depth* 与新形状不自洽。
 见 F17/本库 MatmulTransA 记录）；本策略只在既有「只缩不放」收敛之后做**整除对齐**。
- ⚠️ `MultiCoreMatmulTiling::GetTiling` 的 `singleCore*` 会被**同进程前一次调用**影响（同 shape 两次
 跑出 `sN=1024` 与 `24576`），大 case 必须钉死几何并打印复核。
- ⚠️ 不要删掉基线里「`tiles < aicCores` 时按 (nB,mB) 铺满」的分支：

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x123.json`；引用时请结合上文适用条件与失效边界判断适用范围。

