---
type: Concept
title: torch_npu.profiler 模型推理性能采集的使用契约与产物验收
description: 用 torch_npu.profiler 采集 PyTorch 模型推理性能：必须显式传 ExperimentalConfig(Level1+PipeUtilization) 否则 kernel_details.csv 只有 9 列且 op_statistic/api_statistic 不生成；schedule 的 prof.step() 总次数须按 wait+warmup+active+skip_first 与重复周期核算跨出 active 窗口（wait≠0 时不能只补 1 步）；框架内置(enable_profiler)与注入两路径；采后按 run failed 计数、按 export_type 区分 CSV/JSON 与 Db 产物验收。
tags: [task.debugging, topic.performance.analysis, topic.graph_execution]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/model/model-infer-profiling/SKILL.md
    role: primary
created_at: "2026-11-05T02:10:00Z"
updated_at: "2026-11-10T01:54:00Z"
platforms: [a2, a3, "950"]
aliases: [torch_npu profiler, ExperimentalConfig, ASCEND_PROFILER_OUTPUT, kernel_details.csv, enable_profiler]
---

# torch_npu.profiler 模型推理性能采集的使用契约与产物验收

用 `torch_npu.profiler` 采集 PyTorch 模型推理性能数据，产出与 Ascend 官方 TensorBoard/Profile 插件兼容的 `ASCEND_PROFILER_OUTPUT` 目录。本卡保存采集的使用契约与产物验收方法。

## 路径路由：框架内置 vs 注入采集

先判断仓库是否已有框架内置 profiler（搜 `torch_npu.profiler`、`tensorboard_trace_handler`、`enable_profiler` 配置项）：

- **框架内置**（如推理引擎已接 profiler）：只开开关 + 调参数 + 验收产物，不再注入采集代码。典型开关为配置项 `enable_profiler: True`；采集参数（active/skip_first/warmup）硬编码在框架的 profiler 封装中，按需改封装入参；
- **注入采集**：仓库没有内置 profiler（或内置产物验收不过）时，自己写采集代码。

采前确认采集范围：采哪个阶段（prefill / decode / both）与 decode 采集步数（建议 ≥10 覆盖稳态）；prefill 每 request 通常只有 1 步，active 固定为 1；第一次图编译 / JIT 必须在采集窗口外预热，否则采到的是编译时间。

## 关键契约 1：ExperimentalConfig 决定采集深度

torch_npu 默认不开详细 AIC/AIV 流水指标，必须显式传：

```python
experimental_config = torch_npu.profiler._ExperimentalConfig(
    profiler_level=torch_npu.profiler.ProfilerLevel.Level1,
    aic_metrics=torch_npu.profiler.AiCMetrics.PipeUtilization,
)
```

| 产物 | 带 ExperimentalConfig | 不带（默认） |
| --- | --- | --- |
| `kernel_details.csv` 列数 | ~47 列（含 Stream ID、Input/Output Shapes、`aic_mac_ratio`、`aic_mte2_ratio`、`aiv_vec_ratio` 等） | 9 列（基本时间/dur/block_dim） |
| `op_statistic.csv` / `api_statistic.csv` | 生成 | 缺失 |

`profiler_level` 取 Level0（基本 trace）/ Level1（推荐默认）/ Level2（更细 SoC 计数、体积更大）；`aic_metrics` 只能选一组（PipeUtilization 定位 cube/vector/mte 流水 bound；关心 HBM/L2 带宽选 Memory/L2Cache）。绝大多数优化任务用 `Level1 + PipeUtilization`。

## 关键契约 2：schedule 须跨出 active 窗口

状态在每次 `prof.step()` 转换（wait → warmup → active → 收尾）；循环结束时 profiler 还停在 RECORD 会打 `Incorrect schedule: Stop profiler while current state is RECORD` 警告并可能数据不完整。规则：**`prof.step()` 总调用次数须让 schedule 走完 wait、warmup、skip_first、active 全部阶段并多出一步触发收尾**——按 torch_npu 的 schedule 语义，完整步数为各阶段步数之和（wait 计入时为 `wait + warmup + skip_first + active + 1`；版本未把 wait 计入 step 转换时为 `skip_first + warmup + active + 1`）。反例：wait=5、warmup=1、active=2、skip_first=0 时只执行 4 次 step 仍处于等待阶段、尚未开始采集——**不能用「统一补 1 步」代替核算**，重复周期（repeat）场景还要乘上周期数。两种写法：MAX_STEPS 按 above 公式调够大，或循环结束后补足差额次 `prof.step()`。最终以实际采集状态确认完成（日志无 RECORD 截断警告、产物齐全），不单靠步数公式。

## 关键契约 3：产物验收（不能跳，按 export_type 分支）

框架开了采集开关不等于拿到可用数据——离线解析（CANN msprof）可能失败。**验收条件随 `export_type` 而变**：导出 CSV/JSON 时按下表验收；工具配置为仅导出 Db 时，正常产物是数据库文件（无 CSV/JSON），不能按「无 CSV」误判为采集失败或触发重采——先核对本次运行的 export_type 再选验收分支。

`export_type` 为 CSV/JSON（或默认）时：

| 验收项 | 期望 | 不符合时 |
| --- | --- | --- |
| 运行日志中 `run failed` 计数 | 0 | 非 0 → 解析失败，先换输出目录 |
| 每个采集阶段都有 `prof/<phase>/.../ASCEND_PROFILER_OUTPUT/` | 存在 | 缺失 → 该阶段未落盘，视同失败 |
| `kernel_details.csv` 列数 | ~47 | 只有 9 → 没开 Level1+PipeUtilization |
| `op_statistic.csv` / `api_statistic.csv` | 存在 | 缺失 → 解析失败 |
| `trace_view.json` | 合法 JSON、以 `]` 结尾 | 截断 → 解析失败 |

`export_type` 为 Db-only 时：验收产物为数据库文件生成且非空、`run failed` 计数为 0；CSV/JSON 缺失属预期，不构成失败信号。

「全部 parser run failed + 无 CSV + trace_view 截断」这组症状最常见的原因是 **profiling 输出目录所在的文件系统/盘**（数据盘/网络盘/特定 bind-mount 会让离线解析产不出 CSV），不是框架代码、权限或版本——把输出换到另一个文件系统（尤其本地盘）重试即可；换盘仍不行才回退注入采集。验证方法：把失败的原始数据 cp 到另一盘再 `torch_npu.profiler.profiler.analyse(<dir>)`，能解析出 CSV 即坐实。

## 失效边界

- 来源技能以 cann-recipes-infer 为示例载体，框架内置路径的参数点位（profiler_context.py 等）是该框架的具体实现，迁移到其他仓库时按「框架内置 vs 注入」通用判据重新路由；
- 多卡时每个 rank 各采一份；产物目录与日志同级；
- 指标字段口径与瓶颈判读的算子侧方法见[性能分析指南](../../ops/ascendc/guides/performance/index.md)；kernel_details.csv 的按层拆解方法见[性能拆解工具卡](model_perf_breakdown_component_split.md)。
