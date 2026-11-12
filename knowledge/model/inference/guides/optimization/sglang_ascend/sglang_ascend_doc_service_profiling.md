---
type: Guide
title: SGLang 昇腾服务的 Profiler 采集、落盘与图模式边界
description: 使用 API、benchmark 或 CLI 采集 NPU trace，区分自动停止、异步解析、图模式和多节点合并限制。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/optimization/profiling.mdx
  role: primary
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-08T12:09:58Z'
platforms: []
---

# SGLang 昇腾服务的 Profiler 采集、落盘与图模式边界

## 采集契约

服务内置torch_npu Profiler。输出目录优先级为API参数、SGLANG_TORCH_PROFILER_DIR、默认/tmp；stack和shape可由API或对应环境控制。API里的activities仍写CPU/GPU，torch_npu patch把CUDA activity重定向NPU；这不是在NPU机器采集GPU事件。该页明确只支持CPU/GPU，MEM依赖CUDA内存接口而被忽略，RPD需要ROCm会报错。没有具体芯片产品证明，因此本卡draft空平台。

## 四种入口

| 入口 | 启动与停止 | 关键条件 |
|---|---|---|
| 手工API | start_profile、发送工作负载、stop_profile | stop会等待flush与解析，可能较长 |
| API步数 | start_profile带num_steps | 达到步数自动停止，无需手工stop |
| benchmark --profile | 自动启动；profile-steps传num_steps，否则结束时stop | 会创建时间戳子目录 |
| sglang.profiler CLI | 发start并等待采集完成 | 必须先启动采集再发请求，无forward step可能一直等待 |

start_step用于跳过初始step；num_steps不是请求数。先等服务收到start再发请求，之前请求不会被收录。profile_by_stage/profile_stages可以分别看prefill/decode；PD的两个worker需分别采集。CLI等待异步flush偶有阻塞时可改用API自动停止或benchmark入口。

## 输出、解析和分析

以服务日志的Profiling starts/done路径为准；每节点分别生成*_ascend_pt/ASCEND_PROFILER_OUTPUT，含trace_view.json、analysis数据库、kernel/operator_details和step_trace_time等。正常stop后服务自动解析，不需另调analyse。只有中断或重解析才用torch_npu analyse；已有输出目录可能被覆盖，应先保留原数据。

Ascend格式的merge_profiles支持不完整，合并结果可能缺失或错误，建议逐节点查看trace。关闭graph可恢复更多Python栈到算子的映射，但会改变decode性能；不能拿该trace运行当生产graph性能。graph capture需专用enable-profile-cuda-graph，输出另在graph_capture_profile。

控制请求数、输出长度和采集step防止trace过大，记录实际rank/device与温身条件。采集插桩会扰动时序；用无插桩服务另测端到端指标，再以trace解释瓶颈。本次只读来源，没有采集设备trace。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/optimization/profiling.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/optimization/profiling.mdx)（primary）
