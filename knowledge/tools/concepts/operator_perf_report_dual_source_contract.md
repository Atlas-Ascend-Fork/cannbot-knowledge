---
type: Concept
title: 算子性能报告解读的双源输入契约（npu-rep 与 msopprof PROF 目录）
description: 解读 NPU 算子性能报告先分源：950 用 npu-compute 采集的 .npu-rep（HardwareInfo.jsonl 自动识别芯片），非 950 用 msopprof 的 PROF_* 目录（必须显式指定 SoC）；两源都消费 PipeUtilization.csv 等 Section CSV 做瓶颈判定，NA 剔除、ratio 双口径归一、active_bw 与全程平均带宽区分等口径规则通用。
tags: [task.debugging, topic.performance.analysis, topic.data_movement]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-perf-analysis/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-perf-analysis/references/input-contract.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-perf-analysis/references/mechanism-routing.md
    role: supporting
created_at: "2026-11-05T01:20:00Z"
updated_at: "2026-11-05T01:20:00Z"
platforms: [a2, a3, "950"]
aliases: [npu-rep, msopprof, PipeUtilization, OpBasicInfo, active_bw]
---

# 算子性能报告解读的双源输入契约（npu-rep 与 msopprof PROF 目录）

拿到算子性能采集产物做解读前，先按输入形态分源路由，两源的产物清单与口径差异决定了哪些判定可做、哪些必须跳过：

| 判据 | 源 A | 源 B |
|---|---|---|
| 输入形态 | `*.npu-rep` 二进制容器（magic `npu-rep\0`，嵌套 type=1 子报告） | `PROF_*` 目录（含 OpBasicInfo.csv） |
| 采集工具 | npu-compute（950 / dav-3510 专用） | msopprof（非 950：A2/A3 等） |
| SoC 识别 | 从 HardwareInfo.jsonl 自动识别（3510→950） | 产物无硬件信息，必须显式指定 SoC |
| 基本信息来源 | summary.jsonl 末行 OpInfoSummary（算子名/Task Duration/Block Dim/频率/GM 带宽利用率） | OpBasicInfo.csv（等价字段） |
| L1/L2 判定输入 | PipeUtilization.csv 逐 block pipe 占比（aic_/aiv_ 双列） | 同名 CSV（列名同族；A2/A3 含更细 scalar stall 分解列） |
| L0 stall 档 | summary.db PcSampling 表（top_stall_pct）+ objdump/symbolizer 热点定位 | 无 PcSampling/PipeTrace，L0 档与 trace 汇总跳过（如实标注） |
| 反证标量 | ArithmeticUtilization（vec_fp32_ratio）、ResourceConflictRatio（vec_total_cflt_ratio）、L2Cache（l2_hit_rate） | 按采集时选择的指标，缺项如实标注 |

## 口径规则（两源通用）

- `NA` = 不适用/未采集，剔除不按 0 统计；`aic_*` 整列 NA 表示未使用 Cube 核；
- ratio 类字段存在 0~1 与 0~100 双口径，按边界值归一（≤1.5 视为比例）；
- 活跃带宽（active_bw）是**搬运活跃期间**的带宽，全程平均 ≈ active_bw × ratio；GM 带宽利用率优先用 OpInfoSummary 的 `aicore_gm_bw_usage_rate(%)`（Σ块口径）；
- 单次采集（single-shot）结论须标注非稳态——稳态结论需要 warmup ≥10 / repeat ≥5 / 取中位数；
- 降频（Current Freq < Rated Freq × 0.9）时标注「降频失真」；
- 多 kernel 产物（Op Name 多值）必须按 kernel 名过滤后判定，否则跨 kernel 平均无意义；
- 仅采 `Pipeline` Section 时无 CSV，逐 block 判定按数据绑定契约跳过，由 PC 采样与 summary 标量承担，报告须列出补采建议；
- msopprof 的 `aiv_scalar_ratio` 在 SIMT 内核上可与 vec/mte 并行超 100%——pipe_sum > 115% 是多 pipe 并行的证据而非数据可疑，与 npu-compute 串行求和口径区分解读。

## 解读纪律

- 只读用户给定产物，不启动采集、不上传报告、不修改用户数据；解包失败如实停止，不臆造；
- 数值一律引用脚本产物，不另行手算；缺数据/降级路径如实呈现缺口与补采建议；
- 瓶颈判定结论只出自规则引擎脚本（判定进脚本、解释进 LLM），判定后按 mechanism_refs 路由机制卡——机制知识见[OpsTune 调优知识](../../ops/ascendc/optimizations/index.md)。

## 失效边界

- 源 B 必须显式指定 SoC 才能做峰值换算（soc-spec 依赖）；产物无法证明自身芯片型号；
- PipeTrace.json 最多采样 6 个 Group，不代表全部核的流水时序；
- 本卡为采集产物输入契约的蒸馏；npu-compute 命令与产物字段见[npu-compute 工具卡](npu_compute_cli_and_artifacts.md)。
