---
type: Guide
title: SGLang NPU公共压测工具的预热、完成数与泄漏日志边界
description: 说明run_bench_serving默认内层1请求预热及可选额外16请求压测、完成数断言、后台任务生命周期，以及内存泄漏测试只扫描日志不能替代显存/页账审计。
tags:
- task.testing
- topic.performance.analysis
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/test_ascend_utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/benchmark/serving.py
  role: implementation
created_at: '2026-11-08T12:21:44Z'
updated_at: '2026-11-09T04:36:38Z'
platforms: []
---

# SGLang NPU公共压测工具的预热、完成数与泄漏日志边界

公共run_bench_serving启动服务，构造benchmark参数，need_warmup 时复制同参数仅将 num_prompts 改16，额外先跑一次完整 benchmark。get_benchmark_args 未设置 warmup_requests，内层 run_benchmark 默认补为1，并在正式计时前发出这1个预热请求；因此未启用 need_warmup 也仍有内层默认预热。随后正式 run_benchmark，finally清理服务，最终assert completed==num_prompts，区别只解析部分stdout性能数字的E2E wrapper。

可选background_task通过start_event/stop_event覆盖整个正式 run_benchmark 调用（包括内层预热），不是仅覆盖 benchmark_start_time 之后的测量窗口；任务结束等待完成，比较有无后台流量时应记录其配置，不能把它遗漏为随机性能波动。get_benchmark_args设random_range_ratio=0.0，和另一E2E测试默认1的长度分布不同，即使同input/output目标也不能直接比。

run_and_check_memory_leak设置chunk/overlap/radix条件并跑workload，收集日志，要求出现Uvicorn running、不含leak，必要时含Abort；它不直接证明无缓慢HBM/Host泄漏，也没有完整页所有权计数。需同时追踪稳态可用显存、活请求/缓存页、Host注册和重复请求后的资源归还。

attention monitor hook只记录某层输入/输出沿末维sum的前5项，不是逐元素精度对拍；日志采集本身可能增加同步和开销，性能测量应单独进行。本次未调用这些工具或运行工作负载。
