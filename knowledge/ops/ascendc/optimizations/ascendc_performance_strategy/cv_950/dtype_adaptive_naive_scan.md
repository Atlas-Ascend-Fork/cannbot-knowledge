---
type: Optimization
title: 按输出 dtype 自适应选择 scan 数值链（低精度输出用朴素累加替换补偿链）
description: 按输出 dtype 编译期分支选择 scan 数值链：低精度输出用 fp32 域朴素累加替换补偿求和链（Kahan），高精度输出保留补偿链逐指令不变。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/30-dtype-adaptive-naive-scan.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：按输出 dtype 自适应选择 scan 数值链（低精度输出用朴素累加替换补偿链）

> **来源：A5 自由探索实测（sequential_linear_cumsum，2026-09-12，device 7）**
> direction_key: `aiv_vec::dtype-adaptive-naive-scan::vector-scan-loop`
> 证据：<AOA_ROOT>/AOA/AOA_skill_run/aoa_out/sequential_linear_cumsum/loop_<run-id>/explore/direction_002/evidence_run/final/bench_paired.log
>       （A=tests/base/_C_base.so（算子**冻结基线** .so，md5 b71d2d3b…），B=本方向改造后 .so，2 对平衡交替，23 case，B_over_A_geomean=0.443389）
> 实测：2.2554 x（**相对算子冻结基线**；注意本方向改造前该算子已含策略轮 4 的 champion 改动，相对该 champion 状态的增量 ≈1.9163 x（B_over_A≈0.521841）系**比值分解推算**（0.443389 ÷ 0.849663），非直接配对复测——两条证据链分别测于不同卡（本方向 dev7；轮 4 见 loop_<run-id>/round_004/apply/bench_paired.log），无法头对头；2026-09-15 审计核实：原稿「经另一次平衡交替配对复测」无归档日志，已更正为推算值），精度 PASS（23/23，含 1 轮功能修复：初版漏跨行累计，改为逐行读上一行累计 + tile 尾 run 延续后全过），改动前 bad_ratio 情况如证据所述（基线 Kahan 链 23/23 PASS；朴素链仅 fp32 case 会超标，见红线）

## 原理

向量核上的串行 scan（前缀和/累积）链，若为满足最高精度 dtype（如 fp32 输出、tol 2^-13）的相消误差而引入补偿求和（Kahan 五式：补偿项 y/t/c 的维护占 5 条向量指令中的 3 条，且每式后一次全流水屏障），则对所有 dtype 统一付出「每行 5 指令 + 5 屏障」的成本。当输出 dtype 是低精度（fp16 tol 2^-10 / bf16 tol 2^-7）且最终输出经一次量化舍入时，fp32 域朴素累加的每步舍入（~2^-24 相对）比输出量化步长低 2~3 个数量级，**数值上不可观测**——补偿链的额外精度在该 dtype 下是纯浪费。

机制：按输出 dtype 编译期分支（`if constexpr`）选择 scan 实现——高精度输出（fp32）保留补偿链逐指令不变；低精度输出（fp16/bf16）改朴素 fp32 累加（每行 1 条 Add，屏障从每行 5 次降到 1 次），累加种子（run）在 tile 尾一次承接。收益来源：AIV 向量指令数与全流水屏障次数同比下降，scan 主导的向量核关键路径缩短。

实测背景指纹：fp16/bf16 case（占 16/23）aiv_vec_ratio≈0.61~0.64、aiv_scalar_ratio≈0.18、aic_mac_ratio≤0.016——关键路径在 AIV scan；fp32 case aic_mac_ratio≈0.60——关键路径在 cube，朴素化对它无益也无害（路径保留原链）。

## 性能问题模式（哪些 profiling 信号说明该用）

- msOpProf PipeUtilization：低精度输出 case 的 aiv_vec 占比高（>0.6）、aiv_scalar 次之（~0.2）、矩阵计算 pipe 占比极低（<0.02）——向量核是关键路径。
- 代码审查：scan/累积段每行 N 条指令、每指令后跟全流水屏障（PIPE_ALL），行数 × 指令数 × 屏障次数即同步开销主体；其中多数指令只服务于补偿项维护。
- 精度判据按 dtype 分档（不同 dtype 的 tol 相差 2^3~2^6），且历史证据显示低精度 dtype 在朴素链时代精度即通过（补偿链是为个别高精度 case 引入的全局成本）。
- tiling 类策略收益已饱和（只改块大小不改每行成本），scan 开销未被触及。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **高精度输出 dtype 禁用朴素链**：fp32 输出（tol 2^-13 量级）下朴素累加的相消误差实测超标（bad_ratio 286/530 vs 参考 33/64 量级，全部是 fp32 case）——高精度路径必须保留补偿链，逐指令不变。
2. **量化步长论证前置**：切换前必须给出「累加域每步舍入 << 输出量化步长」的数值论证（本例 2^-24 vs 2^-10/2^-7，且输出侧量化舍入是唯一输出舍入点）；论证不成立不得切换。
3. **串行依赖必须逐行表达**：scan 的跨行累计（每行读上一行累计结果）不能因屏障塌缩而丢失——初版把屏障塌缩到 tile 尾一次，漏跨行累计出功能 bug；正确形态是每行读「上一行已累加完」的结果（首行读种子）、每行一次显式屏障（auto-sync 关闭时 V→V 读写依赖须显式排序），tile 尾一次承接种子。屏障塌缩必须以依赖完整为前提。
4. **分支必须编译期隔离**：dtype 分支用 `if constexpr` 类机制，保证高精度路径指令序列逐位不变（零扰动），运行时不得改变 fp32 case 行为。
5. **种子/尾块延续语义不变**：跨 tile 的 run 延续、尾行有效列数（nEff）处理与原链一致，只换数值链不换边界语义。

## 泛化条件（dtype / shape / 流水线 / 算子类型）

- 流水线：aiv_vec（向量核计算+屏障主导）；同步开销显著时 aiv_scalar 同受益。
- dtype：输出 dtype 精度显著低于累加域 dtype（量化步长差 ≥ 2^3 量级）时适用；输出与累加域同精度时禁用（红线 1）。
- 算子类型：任何「向量化 scan/递推/累积 + 按 dtype 分档精度判据」的向量核路径（前缀和、累积量、递推滤波形态），不限具体算子。
- shape：行数多（逐行链长）的 case 收益最大；行数少的 case 中性。
- 与其它策略正交：不改 tiling、不改 AIC/AIV 结构、不改同步框架，可与块大小/搬运类策略叠加。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 量化 scan 段成本：每行指令数、每行屏障次数 × 行数/tile，对照 profiling 确认向量核关键路径。
2. 列出精度判据分档：各输出 dtype 的 tol 与输出量化舍入点；论证「累加域舍入 << 量化步长」，不成立则终止。
3. 编译期按输出 dtype 分支：高精度 dtype 走原补偿链（逐指令不变）；低精度 dtype 走朴素链。
4. 朴素链实现串行依赖：每行读上一行累计结果（首行读种子），每行一次显式屏障；tile 尾一次种子承接（Adds 类恒等拷贝）。
5. 全量精度用例过门（重点：低精度全部 case + 高精度 case 零扰动）；若有功能修复，修复后重跑全量。
6. 平衡交替配对复测，确认低精度 case 显著改善、高精度 case 波动在噪声底内。

## LLM 前置问题（应用前必须自问）

1. scan 段每行多少条指令、多少次什么强度的屏障？其中多少条只服务于补偿精度？
2. 各输出 dtype 的精度 tol 分别是多少？累加域每步舍入与输出量化步长差几个数量级？输出侧唯一舍入点在哪？
3. 高精度 dtype 路径能否做到逐指令不变（编译期隔离）？用什么机制保证？
4. 朴素链的跨行累计依赖如何逐行表达？首行种子、tile 尾承接、尾块有效列分别怎么处理？
5. 历史证据是否支持「低精度 dtype 朴素链精度即通过」？有无反例 case？
6. 收益上界：scan 段占向量核时间比例 × 低精度 case 占比，是否超过噪声底？

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过，dtype 分支编译期隔离（无运行时分派开销）。
- **精度**：全量用例 PASS（本例 23/23）；高精度 dtype case 与基线逐位一致（零扰动）；低精度 dtype case bad_ratio 与基线同量级。
- **性能**：平衡交替配对（A/B .so 身份写明，A 侧为基线冻结重建），低精度 case 显著加速（本例 fp16/bf16 case 1.8x~5.1x）、geomean 2.2554x；高精度 case 波动在噪声底（0.5%）内。
- **零劣化判据**：全部 case 无一回退超阈值（本例最差 case +0.07%，噪声底内）。
- **归因**：收益归因于指令数与屏障次数下降（5+5/行 → 1+1/行），不改访存量与算法语义。
- **回退**：任一低精度 case 精度超标 → 该 dtype 回退补偿链；高精度 case 出现扰动 → 检查分支隔离是否泄漏。

## 检索卡（短卡）

动作：按输出 dtype 编译期分支选择 scan 数值链：低精度输出用 fp32 域朴素累加替换补偿求和链（Kahan），高精度输出保留补偿链逐指令不变。
适用：输出 dtype 精度显著低于累加域（量化步长差 ≥2^3 量级）且精度判据按 dtype 分档的向量核 scan/递推路径。
限制：高精度输出（fp32）禁用朴素链；切换前须论证累加舍入<<输出量化步长；跨行累计须逐行表达、屏障塌缩不得丢依赖；分支编译期隔离零扰动。
范围：向量核串行 scan/累积/递推链的数值实现选择环节。
检索词：Kahan、补偿求和、朴素累加、if constexpr、PIPE_ALL、量化步长、aiv_vec、前缀和。
机会：低精度 case aiv_vec 占比>0.6、矩阵 pipe 极低；补偿项维护占每行多数指令且每式后屏障；tiling 已饱和。
