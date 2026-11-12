---
type: Concept
title: 昇腾训练推理工具全景：问题域到工具的路由总览
description: 昇腾 NPU 上「不正常」（异常退出、AI Core Error、卡死、超时）与「不够快」（吞吐、时延、带宽）两类问题的工具路由：故障诊断用 asys/msaicerr/msnpureport，算子检测用 npu-check/msaicerr/asys，性能采集用 msprof/npu-compute，内存采集用 msprof，精度采集比对用 msaccucmp/msaicerr；附工具定位与部署位置速查。
tags: [task.debugging, topic.performance.analysis, topic.implementation.debugging]
status: stable
sources:
  - resource: https://gitcode.com/fujun19/doc/blob/390e82178231a6d198096586cc2d4f01c82e0afa/tools/tool_introduction.md
    role: primary
created_at: "2026-11-05T02:10:00Z"
updated_at: "2026-11-05T02:10:00Z"
platforms: [a2, a3, "950"]
aliases: [工具路由, tool landscape, asys, msaicerr, msnpureport, msprof, msaccucmp]
---

# 昇腾训练推理工具全景：问题域到工具的路由总览

训练与推理任务跑在昇腾 NPU 上遇到两类问题：一是「不正常」——任务异常退出、屏幕打印 AI Core Error、进程卡死、执行超时；二是「不够快」——训练吞吐不达标、推理时延偏高、内存带宽吃紧。按使用场景选工具：

| 使用场景 | 推荐工具 |
| --- | --- |
| 故障诊断（AI Core Error、超时、卡死等异常） | asys、msaicerr、msnpureport |
| 算子检测（越界、参数等） | npu-check、msaicerr、asys |
| 性能采集 | msprof、npu-compute |
| 内存采集 | msprof |
| 精度采集比对 | msaccucmp、msaicerr |

各工具定位与部署位置：

| 工具 | 一句话定位 | 来源与位置 |
| --- | --- | --- |
| asys | 一键式故障信息收集与诊断（collect/launch/info/health/diagnose/analyze 六类维测文件解析/config） | CANN 运维工具集 oam-tools，CANN 安装目录 `tools/` |
| msaicerr | AI Core Error 问题定位专家（`-p` 完整分析 / `-d` Dump 解析 / `-dtype` 类型转换 / `-e` 环境自检） | oam-tools，CANN 安装目录 `tools/` |
| msprof | 任务级/系统级性能数据采集与分析（ACL/Runtime API 耗时、算子执行耗时、AICore PMU、AI CPU、Host 系统数据） | oam-tools，CANN 安装目录 `tools/` |
| msaccucmp | Dump 数据解析与比对（convert 转 npy、file_compare 官方指标） | 随 oam-tools 发布（源自 msprobe） |
| msnpureport | Device 侧维测信息导出与配置（日志级别、坏核屏蔽、加速器复位等） | 昇腾驱动内置，驱动安装目录 `driver/tools/` |
| npu-check | NPU 运行时正确性检查（memcheck/synccheck/initcheck/racecheck） | Ascend C Tools（asc-tools） |
| npu-compute | 算子级性能数据采集（.npu-rep 报告） | asc-tools |

这些工具构建在 CANN 运行时（runtime）的日志、异常 Dump、Profiling 框架与驱动维测通道之上：业务运行时维测数据自动产生，工具负责一键采集、解析与分析。

## 故障诊断推荐路径（两条命令闭环）

```bash
# 1. 一键收集故障现场：Host 侧 CANN 软件栈日志 + Device 侧系统日志/黑匣子/coredump 调用栈
#    （底层自动调用驱动 msnpureport 导出，用户无感）+ dump 图、算子编译信息等
asys collect --tar="True" --output=$HOME/dfx_info

# 2. AI Core Error 根因分析：内部自动调用 msaicerr，输出分析结果（info.txt）辅助定位根因
asys analyze -r=aicore_error -d=0
```

`asys analyze -r=aicore_error` 不指定 `--path` 时会先自动收集故障信息再调用 msaicerr 分析；也可指定已有故障信息目录（如 asys collect 的输出）直接分析。超时类问题：asys collect 收集的 Host/Device 日志中包含超时报错及其上下文，配合 trace 文件解析定位超时发生点。其余常用能力：业务复跑 + 故障收集（`asys launch --task`）、进程卡死实时堆栈导出（`asys collect -r=stacktrace --remote=<pid> --all`）、健康检查（`asys health`）、综合硬件检测（`asys diagnose -r=stress_detect/hbm_detect/cpu_detect/aicore_stl_detect`）、调大 Device 日志级别（`msnpureport config --set --log`，问题偶发难复现时）。

## 精度问题三步流程

1. **采集**：通过 Dump 配置导出算子输入输出数据（模型 Dump、单算子 Dump、溢出算子 Dump；AI Core Error 场景由运行时自动生成异常算子 Dump）；
2. **解析转换**：msaccucmp 将原始 Dump 转 `.npy`；msaicerr 解析异常算子 Dump（输入/输出/workspace/tiling）并支持 dtype 转换；
3. **比对**：msaccucmp 将实际数据与 golden 数据比对，输出余弦相似度、最大绝对误差等官方指标。Runtime Dump 配置与 msaccucmp convert/file_compare 的完整流程见算子工具批次的 Runtime Dump 工具卡。

## 各域知识入口

- 故障诊断工具卡：[asys](asys_command_routing_and_constraints.md)、[msaicerr](msaicerr_aicore_error_analysis.md)、[msnpureport](msnpureport_export_and_device_config.md)、[AI Core Error 诊断工作流](aicore_error_diagnosis_workflow.md)、[AscendC 调试接口](ascendc_kernel_debug_api_selection.md)；npu-check/npu-compute/npu-objdump、Runtime Dump 与 msaccucmp、性能报告双源契约、整网采集等工具卡在 Issue #101 第一、二批 PR 迁入；
- asys/msaicerr/msnpureport 的输出语义与判读：见[Ascend C 诊断向导](../../ops/ascendc/guides/diagnostics/index.md)；
- 算子级调试（编译/运行时/AI Core/精度/通信）：见[Ascend C 调试指南](../../ops/ascendc/guides/index.md)。

## 失效边界

- 本卡为工具路由总览；各工具命令细节以对应工具卡与当前安装版本 `--help` 为准；
- CANN 工具仅支持 Ascend EP 形态（RC 形态不支持）；
- msaicerr 仅支持本地分析（部署环境与日志环境须同一环境），暂不支持分析通信与 Matmul 融合类算子（MatmulAllReduce 系、AllGatherMatmul 等）的 AI Core Error。
