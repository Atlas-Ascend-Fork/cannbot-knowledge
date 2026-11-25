---
type: Optimization
title: "X124: 轻权重 GEMM 的「每核搬运字节」core-fill 重切"
description: "轻权重 GEMM 常只点亮少量 cube 核；按「每核搬运字节」而不是 base tile 合法性来重切网格，可把网格铺满并降低单核墙钟。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.data_copy
  - topic.memory
  - topic.tiling
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_optimization_overview.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_multi_core_split_k.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x124.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X124）。
>
> 原始元数据：
>
> ```yaml
> id: X124
> origin: discovered
> confidence: single_op
> op_families: [matmul, cv-mix]
> bottlenecks: [tiling_imbalance, undersize_transfer]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x124.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x124.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X124: 轻权重 GEMM 的「每核搬运字节」core-fill 重切

## 核心思路
`MultiCoreMatmulTiling` 对本算子里的**方 GEMM / 轻权重 GEMM**（权重 < 约 4 MB，典型是 C×C 的
通道投影与输出投影）只点亮 **1~12 / 24** 个 cube 核：它按 base tile 保证切分合法，却不会为了
"把网格铺满"而继续往下切。而一个 cube 核的墙钟由它**独自**要搬的字节决定：

```
per_core_bytes ~ (singleCoreM + singleCoreN) * K * 4
```

它与聚合带宽无关 —— 空转的核不会帮正在搬的核分担。所以正确目标函数不是"窗口最宽"，而是
**最小化单核搬运字节**，判据就是：`ceil(M/sM) * ceil(N/sN) >= aicCoreNum` 是否成立。

两段式判据（与"窗口/深度"派互补，不冲突）：
- 权重 **< ~4 MB** → 按 per-core bytes 把网格铺满（本卡）；
- 权重 **≥ ~4 MB** → 交给窗口/深度派（加宽 baseK、显式 SetBufferSpace），因为这时瓶颈变成
 L1 在飞窗口而非核数。

## 适用场景
- matmul / cv-mix 系，**M 远小于 N、K**的瘦长或方形 GEMM（M=B·H·W 或 B·seg·W 只有个位数到几十）；
- 症状：`op_summary` 里 `Block Dim` 只有 1~12，而 `aic_mte2_ratio` 很高、`cube_utilization` 低；
 或 dump 出 tiling 发现 `nBlocks*mBlocks` 远小于 24；
 （本卡只在 <4MB 区间生效，与小 case 的固定开销优化正交）。

## 实现要点
1. 先 dump 真实 tiling（不要信请求值，API 会夹取），确认 `mBlocks*nBlocks` 与 `usedCoreNum`；
2. 若 `totalBlock < aicCoreNum`，按 `(sM+sN)·K·4` 最小化重新切；**必须保留基线的粗扩展**
 （`totalBlock < aicCores` 时按 base tile 缩小单核 tile）—— 撤掉它会让 `singleCoreN` 退化为整个 N，
3. 只在权重 <4MB 时接管，别把大权重 GEMM 也拉进来（会与窗口派互相打架）；
4. 顺带的代数恒等（同源发现）：`seg==1` 时 permute 后的 `aw ≡ x`、`wr ≡ we`，可删掉一次 M·C gather

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x124.json`；引用时请结合上文适用条件与失效边界判断适用范围。

