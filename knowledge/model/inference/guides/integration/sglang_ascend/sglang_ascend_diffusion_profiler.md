---
type: Guide
title: SGLang Diffusion NPU profiling：活动、调度与trace归属
description: 说明torch_npu profiler替换、CPU/NPU双活动、warmup与停止同步，以及不能套用CUDA gzip导出命名的边界。
tags:
- task.implementation
- topic.diffusion
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/utils/profiler.py
  role: primary
created_at: '2026-11-08T12:27:27Z'
updated_at: '2026-11-08T12:27:27Z'
platforms: []
---

# SGLang Diffusion NPU profiling：活动、调度与trace归属

## 测量流程

NPU分支使用torch_npu.profiler的profile/schedule，活动包含CPU和NPU，开启record_shapes与with_stack，trace交给tensorboard_trace_handler。按请求选择全部阶段或计划去噪步骤，warmup=1，active覆盖实际步数与相关warmup；各阶段必须在同一调度契约下调用step。

停止操作只执行一次并先NPU synchronize，NPU将export_trace置False，由自己的handler导出；通用路径request模式/global rank的gzip文件名不自动适用于NPU。maybe_record_function读取进程级profiler标志，可以覆盖其他线程，不能解释为线程局部开关。

## 分析与边界

先确认warmup与正式采样步是否被包含，再按CPU等待、HCCL、FIA/量化、布局copy和编译分组比较。record_shapes/stack会增加测量开销，不应把开启profiler的E2E当作无仪器基准。保留平台、依赖、shape、并行和trace实际目录，避免不同rank覆盖。本文给出固定源码的采集机制，本次没有生成trace或性能结论。
