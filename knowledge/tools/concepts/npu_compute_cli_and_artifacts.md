---
type: Concept
title: npu-compute 算子级性能采集工具的命令契约与产物结构
description: 用 Set（basic/full）或 Section 选择 npu-compute 采集范围执行算子实现级 PMU 采集，生成 .npu-rep 报告；解包后按 HardwareInfo.jsonl、各 Section CSV、summary.jsonl、PipeTrace.json 识别结果，从带宽、流水线、存储访问、缓存和资源冲突数据定位性能问题。
tags: [task.debugging, topic.performance.analysis, topic.implementation.debugging]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-npu-compute/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-npu-compute/references/cli-usage.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-npu-compute/references/collection-workflow.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-npu-compute/references/summary.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-npu-compute/references/hardware-info.md
    role: supporting
created_at: "2026-11-05T01:20:00Z"
updated_at: "2026-11-05T01:20:00Z"
platforms: ["950"]
aliases: [npu-compute, npu-rep, PipeUtilization, msopprof]
---

# npu-compute 算子级性能采集工具的命令契约与产物结构

npu-compute 是 Ascend C 算子实现级精细采集工具（950 / dav-3510 路线）：计算/流水线利用率、L2Cache、Memory/L0/UB 访存、流水时间线与资源冲突等指标组，生成 `.npu-rep` 报告，适合算子调优。本卡说明命令契约与产物结构；指标字段的算子侧判读（PipeUtilization 判定阈值等）见[性能指标方法论](../../ops/ascendc/guides/performance/index.md)与 [OpsTune 调优知识](../../ops/ascendc/optimizations/index.md)。

## 命令契约

```text
npu-compute [options] [--] [program] [program-arguments]
```

| 选项 | 含义 |
|---|---|
| `--list-sets` / `--list-sections` | 查询当前安装版本支持的 Set / Section（独立查询，不启动目标程序） |
| `--set <name>` | 选择预定义 Set（`basic` / `full`），名称区分大小写 |
| `--section <name>` | 选择单个采集项，可重复指定，重复项按首次出现去重 |
| `-i`, `--import <report>` | 解包 `.npu-rep` 报告 |
| `-o`, `--export <path>` | 指定报告文件、报告父目录或解包父目录 |
| `--` | 结束工具选项解析，其后第一项是目标程序 |

典型命令：

```bash
npu-compute ./add_custom                        # 默认 basic
npu-compute --set full ./add_custom             # 全量（basic + ResourceConflictRatio）
npu-compute --set basic --section ResourceConflictRatio ./add_custom
npu-compute --import ./report.npu-rep           # 解包到当前目录唯一子目录
```

`Section` 是一类可单独采集的性能指标及其结果文件；`Set` 是按分析目标预组合的一组 Section：`basic` = Pipeline、PipeUtilization、Memory、MemoryL0、MemoryUB、L2Cache、ArithmeticUtilization；`full` = basic 全部成员 + ResourceConflictRatio。Set 与 Section 可重复、交错使用，按命令行出现顺序展开。

采集成功以退出状态为 0、终端发布 `report` 路径且报告文件存在为准；目标程序自身输出成功不能单独证明采集成功。目标程序为无执行权限脚本时使用对应解释器（如 `bash run.sh`）。

## 产物结构与识别

解包目录（含 `collection-p...` 子目录时，根级结果与各子结果集合分开记录，不合并同名文件）：

| 文件 | 内容 |
|---|---|
| `HardwareInfo.jsonl` | 主机与 NPU 环境快照（Host Info / Device Info / CPU Information / AI Core Information / Memory Information 五行 JSONL） |
| `<Section>.csv` | 各 PMU Section 数据行，行键为 `block_id` / `sub_block_id`（AIC=`cubeN`、AIV=`vectorN`） |
| `summary.jsonl` | 每个所选 Section 一条汇总记录 + 一条 `PerformanceHints` + 末尾一条 `OpInfoSummary` |
| `PipeTrace.json` | Pipeline 事件、轨道与时间范围 |

`OpInfoSummary` 关键字段：`Op Name` / `Op Type`（cube/vector/mix）/ `Task Duration(us)` / `Block Dim` / `Device Id` / `Pid` / `Current Freq`、`Rated Freq`（MHz）/ `aicore_parallel_utilization` / `aicore_parallel_balance` / `aicore_gm_read_bw`、`aicore_gm_write_bw`（GB/s）/ `aicore_gm_bw_usage_rate(%)`（按理论带宽 1600 GB/s 折算）。字段不可用时为 `null` 或 CSV 中为 `NA`，不以默认值冒充真实观测。

`PerformanceHints`（适用于 Ascend 950PR&950DT 系列）提供检查方向：PH01 Vector 占比、PH02 Scalar 占比、PH03 MTE2 占比、PH04 平均 GM→UB 搬运量、PH05 ICache 缺失率、PH06 核间耗时分布；提示只是检查方向，优化效果通过可比条件下的重新采集确认。

`HardwareInfo.jsonl` 用于核对两次采集的可比性：`Device Info` 的 `chip info` / `arch info` 是判断同类 SoC 的主要字段（`arch info` 值如 `3510` 是字符串）；个别底层查询失败时字段可能保留默认值 0 或空字符串，不能统一当作真实零值。

## 结论边界

- 指标口径与字段语义以来源技能文档蒸馏为准；ratio 类字段不乘 100，百分比字段乘 100；
- 比较多次采集时先读 `HardwareInfo.jsonl` 确认同 SoC 与频率条件；
- 未选择的 Section 对应指标不可用（`NA`/`null`），不得据此下「指标正常」结论；
- 报告解读与瓶颈判定的算子侧方法见[性能分析指南](../../ops/ascendc/guides/performance/index.md)。
