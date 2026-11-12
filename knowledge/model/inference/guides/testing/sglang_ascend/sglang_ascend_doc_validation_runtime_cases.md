---
type: Guide
title: SGLang NPU图、调度和内存回归的实际检查范围
description: 说明TP/FIA/图精度、禁chunk和overlap组合、warmup及17GiB启动内存门槛，识别未使用的性能字段。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/memory_and_scheduling/test_npu_no_chunked_prefill.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/optimization_debug/test_npu_graph_tp1_bf16.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/optimization_debug/test_npu_graph_tp2_bf16.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/test_npu_no_overlap_scheduler.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/test_npu_warmups.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/runtime_opts/test_npu_tp1_bf16.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/runtime_opts/test_npu_tp2_bf16.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/runtime_opts/test_npu_tp2_fia_bf16.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/test_npu_memory_consumption.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/npu_eval_accuracy_kit.py
  role: implementation
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-09T04:35:53Z'
platforms:
- a3
---

# SGLang NPU图、调度和内存回归的实际检查范围

## 图与FIA质量用例

固定提交面向A3的测试定义，没有本次执行结果。Qwen2.5-7B禁图基本用例TP1 GSM8K≥0.84，TP2≥0.85；TP2 FIA额外disable-Radix与ASCEND_USE_FIA=true。图模式TP1/TP2目标均0.85。图模式始终执行1319题、5shot、max512、parallel128的完整评测；runtime_opts三个禁图用例仅在 GITHUB_EVENT_NAME=pull_request 且 GITHUB_WORKFLOW_REF 不含 nightly-test-npu.yml 时改 smoke，其余（含 PR 触发的 nightly）完整评测，见[共同契约](sglang_ascend_test_gsm8k_contract.md)。

TEST_MODEL_MATRIX的latency150/180、output_throughput30/20没有在这些test方法中用于assert，不能将其写成已验收的时延吞吐门槛。图模式和禁图测试没有共同运行输出，不构成图加速收益。

## 调度组合与启动smoke

no-chunked-prefill使用Llama3.1-8B、禁图/Radix、chunk=-1，MMLU64题/32线程要求≥0.65，另检查10个请求的补全。no-overlap通过共同run_mmlu_test遍历Radix开/关×chunk128/-1四组合，不能从其docstring扩展为任意chunk大小或并发。

warmups用MiniCPM-o TP4配置voice_chat，检查server_info/log与Paris补全，未评估语音质量或warmup时长。关闭某项后仍能请求成功，只是功能smoke，不能解释为关闭它更快。

## 启动内存17GiB门槛

Qwen3-30B-A3B W8A8 TP2，static0.8、max-total-tokens1024、disable-Radix/graph（虽然同时提供graph batch1）。测试在当前调用设备分别读取torch.npu.mem_get_info，以服务启动后占用减启动前占用，换算`/(1<<30)`，要求增量≤17.0 GiB。它不是跨全部rank求和，不包含长请求峰值，也不是模型权重精确大小。

默认可见设备0,1；端口由可见设备字符串的第一个字符推导，是该测试环境约定。比较部署内存时记录设备空闲基线、其它进程、权重和总token预算；不能把17GiB当该模型在任意配置的内存上限。

## Evidence

- [test/registered/npu/basic_function/memory_and_scheduling/test_npu_no_chunked_prefill.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/memory_and_scheduling/test_npu_no_chunked_prefill.py)（primary）
- [test/registered/npu/basic_function/optimization_debug/test_npu_graph_tp1_bf16.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/optimization_debug/test_npu_graph_tp1_bf16.py)（supporting）
- [test/registered/npu/basic_function/optimization_debug/test_npu_graph_tp2_bf16.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/optimization_debug/test_npu_graph_tp2_bf16.py)（supporting）
- [test/registered/npu/basic_function/parameter/test_npu_no_overlap_scheduler.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/test_npu_no_overlap_scheduler.py)（supporting）
- [test/registered/npu/basic_function/parameter/test_npu_warmups.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/test_npu_warmups.py)（supporting）
- [test/registered/npu/basic_function/runtime_opts/test_npu_tp1_bf16.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/runtime_opts/test_npu_tp1_bf16.py)（supporting）
- [test/registered/npu/basic_function/runtime_opts/test_npu_tp2_bf16.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/runtime_opts/test_npu_tp2_bf16.py)（supporting）
- [test/registered/npu/basic_function/runtime_opts/test_npu_tp2_fia_bf16.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/runtime_opts/test_npu_tp2_fia_bf16.py)（supporting）
- [test/registered/npu/test_npu_memory_consumption.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/test_npu_memory_consumption.py)（supporting）
