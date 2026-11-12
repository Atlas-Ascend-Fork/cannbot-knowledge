---
type: Runbook
title: Profiling 解析失败：只有 trace_view、CSV 缺失与输出盘重解析
description: KernelViewParser 等 run failed 时保留原始数据，通过换文件系统 analyse 做受控诊断；区分缺列、空目录与缺通信文件。
tags:
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/references/troubleshooting.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/SKILL.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/scripts/function.sh
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py
  role: supporting
created_at: '2026-11-09T09:23:49Z'
updated_at: '2026-11-10T01:26:11Z'
platforms:
- a2
- a3
---

# Profiling 解析失败：只有 trace_view、CSV 缺失与输出盘重解析

## 症状与探针

enable_profiler 已开启，日志中 KernelViewParser/OperatorViewParser/CANNTimelineParser 等 Task run failed，ASCEND_PROFILER_OUTPUT 仅有 trace_view.json 或文件被截断，kernel_details.csv/op_statistic.csv/api_statistic.csv 缺失。先核对实际输出路径、各阶段/rank 的原始采集、解析日志、空间、权限（包括 EACCES）、挂载与实际目录可写性，而不是把进程正常退出当采集成功。

## 输出文件系统诊断

来源在 A2/A3 某些挂载上观察到同一份原始 *_ascend_pt 数据解析失败，复制到本地盘后通过 torch_npu.profiler.profiler.analyse(<复制后的目录>) 得到完整 CSV。保留原始采集，在同版本工具下只改变数据所在文件系统重解析，是检验这个假设的探针；内部失败机制未定位，不能宣称所有 run failed 都由盘导致，也不能据该案例排除版本/权限问题。

确认后把后续采集输出放到已验证的本地目录。Recipes function.sh 会设定 WORK_DIR，直接 export 可能被覆盖；先核对 WORK_DIR/RES_PATH 的实际拼接。若采用 res 软链接，先保存原目录与已有结果，不能覆盖非空采集目录。多个目标盘仍失败时，回到 parser 日志、环境和最小注入采集定位。

## 区分其他产物缺口

| 现象 | 优先检查 |
| --- | --- |
| kernel_details 只有基础列 | 实际 profiler level、aic_metrics、版本、record_shapes；约9/47列只是来源样例 |
| 整个输出目录为空 | step 是否推进到记录窗口、回调是否配置、输出权限和阶段是否进入 |
| communication.json / communication_matrix.json 缺失 | 是否实际采集到多卡 HCCL 通信；单卡无需生成 |
| TensorBoard 无 Profile 面板 | 解析文件是否有效及插件是否安装，而非直接判定采集失败 |

## 验证与回退

重解析后逐阶段检查 parser 错误、所需 CSV 的列和有效记录、完整 JSON 与时间窗口。成功只说明这批数据在该工具/路径下可解析，不证明所有文件系统或其他版本可用。保留原始数据、对照路径与失败日志，便于回退和复现。

相关：[采集指标](../../guides/optimization/npu_profiling_collection_and_metrics.md)、[schedule 收尾](profiler_schedule_incomplete_trace.md)。

## Evidence

- [.agents/skills/model-infer-profiling/references/troubleshooting.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/references/troubleshooting.md)
- [.agents/skills/model-infer-profiling/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/SKILL.md)
- [executor/scripts/function.sh](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/scripts/function.sh)
- [executor/core/engine/execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)
