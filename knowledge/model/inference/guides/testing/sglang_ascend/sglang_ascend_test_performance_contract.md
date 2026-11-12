---
type: Guide
title: SGLang NPU性能门槛的单位、接受率和缓存命中判定
description: 说明bench-serving与AISBench指标解析、TPOT门槛误注释、吞吐与时延容差、投机接受长度归一化以及缓存分层命中缺失必须失败。
tags:
- task.testing
- topic.performance.analysis
- topic.speculative_decoding
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/test_npu_performance_utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/run_aisbench.sh
  role: implementation
created_at: '2026-11-08T12:20:22Z'
updated_at: '2026-11-09T04:36:38Z'
platforms: []
---

# SGLang NPU性能门槛的单位、接受率和缓存命中判定

## 比较合同

测试默认bench-serving，也可选AISBench；输入长度、输出长度、请求率、并发、warmup、数据分布和采样都需固定。run_bench_serving解析Mean TTFT/TPOT/E2E、Output token throughput、Accept length和Cache Hit Details；AISBench从Common Metric首个吞吐匹配取total_tps，时延正则明确ms。总吞吐与per-request吞吐不可混用。

assert_metrics在设置非零baseline时：TPOT<50则允许baseline+1，>=50则×1.02；TTFT/E2E×1.02，output_token_throughput×0.98。常量注释把低TPOT的+1写作second，但读取口径是ms，必须按实际数据单位解释，不能误允许1秒回退。未设置/零baseline会因truthiness跳过对应检查，不表示这个指标已验收。

accept_rate定义为浮点accept_length/--speculative-num-draft-tokens，要求严格大于baseline。设置此门槛后缺Accept length或缺draft token参数必须失败，不能静默跳过。它与接受草稿比例、correct_drafts或最终输出token计数可能不同，需与服务统计定义一起记录。

min_hit_rate_pcts只接受cache/device/host，单位为百分数，严格>阈值。当前 harness 配置只适用于 dataset_name=generated-shared-prefix：该分支才把客户端 cache_report=True 转发为 --cache-report，并需服务 --enable-cache-report。其他数据集分支（含默认random）即使接到 cache_report=True 也未转发，必须先确认/补齐客户端参数传递才能取得命中指标；缺某层行会失败，可能是容量足够无该层流量、无前缀复用或缓存禁用，而非自动假定0/100%。

## harness失败不能冒充结果

bench stdout watchdog在300秒无新输出时杀进程组，EOF后10秒仍活也清理。此函数捕获异常或非零退出后仍可能返回已解析的部分metrics，后续仅断言已设置的baseline；评审还应检查退出码、completed/failed和原日志。AISBench默认perf为temperature0/ignore_eos=True，accuracy为temperature0.01/seed1234；不同模式不能直接比。

性能数字必须附硬件/拓扑、版本、模型/量化、负载、缓存状态与统计单位。源码中的阈值是待执行门槛，本次未生成任何性能实测；通用测量失真见[测量输入与指标口径](/model/inference/optimizations/anti_patterns/perf_measurement_distortion_input_and_metric.md)。
