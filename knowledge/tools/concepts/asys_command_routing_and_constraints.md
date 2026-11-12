---
type: Concept
title: asys 一键式故障信息收集工具的命令路由与使用约束
description: asys 覆盖 collect（故障收集）/launch（复跑+收集）/stacktrace（卡死实时堆栈）/info/health/diagnose（硬件检测）/analyze（trace/coredump/stackcore/coretrace/UB/AI Core Error 六类解析）/config/profiling；六条使用约束（仅 EP 形态、不建议多进程并行、root 权限分层等）与按症状路由表。
tags: [task.debugging, topic.implementation.debugging, topic.architecture]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/asys-toolkit/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/asys-toolkit/references/constraints.md
    role: constraint
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/asys-toolkit/references/collect-and-launch.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/asys-toolkit/references/analyze-files.md
    role: supporting
created_at: "2026-11-05T02:40:00Z"
updated_at: "2026-11-10T02:00:00Z"
platforms: [a2, a3, "950"]
aliases: [asys collect, asys launch, asys analyze, stacktrace, 堆栈导出]
---

# asys 一键式故障信息收集工具的命令路由与使用约束

asys 是 CANN 提供的一键式故障维测工具（随 CANN 安装，位于安装目录 `tools/`；`source <INSTALL_DIR>/set_env.sh` 后可直接使用）。本卡保存命令路由与使用约束；各解析模式的输出语义与判读见[Ascend C 诊断向导](../../ops/ascendc/guides/diagnostics/index.md)。

## 按症状路由

| 现场症状 | 命令 |
| --- | --- |
| 需要打包一份完整维测信息交付分析 | `asys collect --task_dir=<编译产物/dump目录> --tar="True" --output=<目录>` |
| 问题可稳定复现，想连带复跑一起收集 | `asys launch --task="sh app_run.sh" --tar="True" --output=<目录>` |
| 训练/推理进程卡住不退出 | `asys collect -r=stacktrace --remote=<pid> --all --output=./` |
| 日志出现 `there is an aivec/aicore error exception` | `asys analyze -r=aicore_error`（内部调用 msaicerr） |
| 进程 `Segmentation fault` | `asys analyze -r=coredump` |
| 拿到 `stackcore_*.txt` / `coretrace.*` / trace `*.bin` / UB `*.bin` | `asys analyze -r=stackcore|coretrace|trace|ub` |
| 怀疑 Device 不健康、要看故障码 | `asys health` |
| 看芯片型号、温度、功耗、HBM、AI Core 利用率 | `asys info -r=status`（software/hardware 查版本与规格） |
| 怀疑硬件故障（AI Core/HBM/CPU/STL/AI Vector） | `asys diagnose -r=stress_detect|hbm_detect|cpu_detect|aicore_stl_detect|component` |
| 压测异常退出后电压未恢复 | `asys config --restore --stress_detect`（**恢复命令须逐卡显式指定设备**：diagnose 压测默认覆盖全部设备，而 config 不指定 `-d` 时默认只作用于 Device 0——多卡压测后照抄单条命令会漏恢复其他卡的电压。应记录实际压测的设备清单，逐卡 `-d <id>` 执行恢复并读回确认） |

参数风格：`-r=` 指定模式、`--output=` 指定输出目录前缀（最终目录为 `{output}/asys_output_<timestamp>`，不带时输出到当前目录；取值为空/无效/无写权限时 asys 退出并报错）。

## 六类文件解析（analyze）前置依赖

| `-r` 取值 | 输入 | 前置依赖 | 产品支持 |
| --- | --- | --- | --- |
| `trace` | trace 日志 `*.bin` | asys 环境版本需与产生 trace 的环境**版本一致** | 全系列 |
| `coredump` | core 文件 + 可执行文件 | **gdb** | 全系列 |
| `stackcore` | `stackcore_*.txt` | **readelf**、**addr2line** | 全系列 |
| `coretrace` | `coretrace.*` | **addr2line** | 仅 Ascend 950PR / 950DT |
| `ub` | UB 维测信息 `*.bin` | — | 全系列 |
| `aicore_error` | 日志 / dump 目录 | — | 全系列 |

## 使用约束（六条 + 并行限制）

1. **仅支持 Ascend EP 形态**，RC 形态不支持；
2. 相同用户、相同时间段内同机器同时作业时，收集到的数据会有交叉；
3. 非 root 用户获取到的数据范围受限（Device 侧固件/系统日志、黑匣子、stackcore、coretrace、diagnose 全部模式与 config 需要物理机 + root）；
4. 集群、容器、虚拟机、云场景不支持一键式收集；
5. 涉及大量维测信息收集与内存占用，**不建议多进程并行执行**；
6. trace 日志文件过多时执行时间长（默认存放 `$HOME/ascend/atrace/`）。

并行限制：组件检测（`diagnose -r=component`）不支持并行；不支持对同一个卡住进程并行导出堆栈。run 包安装日志的收集要求安装用户与应用执行用户一致。

## 采集一致性

自动收集受环境变量影响：执行收集时环境变量值需与业务运行时保持一致，否则收集到的信息可能不准确（涉及 `ASCEND_PROCESS_LOG_PATH`、`NPU_COLLECT_PATH`、`DUMP_GRAPH_PATH`、`ASCEND_WORK_PATH`、`ASCEND_CACHE_PATH`、`ASCEND_CUSTOM_OPP_PATH`）。`--task_dir` 指定算子编译文件（`.o`、`.json`）与 dump 文件的目录；未指定或没收集到时 asys 从环境自动收集。

## 失效边界

- 本卡为命令路由与约束的蒸馏；参数细节以当前安装版本 `asys --help` 为准；
- `asys analyze` 解析结果的判读边界（首错、版本一致、符号搜索）见诊断向导既有卡（asys 文件解析、采集上下文与健康检测系列）。
