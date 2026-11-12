---
type: Guide
title: SGLang 昇腾在线与离线性能评测的接口和指标
description: 按文本、多模态、Embedding 选择测试入口，区分 TPOT/ITL、客户端并发、token口径和示意输出。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/evaluation/performance_testing.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/benchmark/serving.py
  role: implementation
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-09T04:34:03Z'
platforms: []
---

# SGLang 昇腾在线与离线性能评测的接口和指标

## 选择匹配任务的入口

来源示例是评测方法，输出均标为示意，不应转写成某芯片的性能观测。页面没有给出这些示意输出完整硬件/软件与重复条件，因此本卡draft空平台。本次未安装工具或执行模型。

| 任务 | 服务条件与接口 | 可用测试路径 |
|---|---|---|
| 文本生成 | 正常生成服务，OpenAI chat/completions或SGLang接口 | Evalscope perf、AISBench streaming chat、benchmark.serving |
| 多模态 | mm-attention-backend ascend_attn；Evalscope/AISBench用 /v1/chat/completions，来源内置image示例的 --backend sglang 用 /generate | Evalscope random_vl、AISBench自备如MMStar数据、benchmark的image数据 |
| Embedding | 必须is-embedding，/v1/embeddings | sglang-embedding backend；Evalscope依版本核对，AISBench在该指南中不支持 |
| 离线 | Engine进程内，无HTTP服务 | benchmark.offline_throughput仅LLM，不支持多模态/Embedding |

内置 benchmark 的 sglang-oai-chat 才映射到 /v1/chat/completions，不能将三个多模态测试路径按同一接口配置。Embedding应设置random-output-len0。AISBench要求独立环境、Python3.10–3.12，在其仓根执行并配置stream/ignore_eos；名称含vllm_api的客户端配置可以指向SGLang的OpenAI接口，不表示运行的推理后端已变为vLLM。

## 固定负载与解释指标

比较性能时固定输入/输出长度（SGLang random-range-ratio1）、tokenizer、采样/ignore_eos、请求速率、并发、warmup与前缀重用。真实数据长度分布应保留供业务评估，定长随机负载只控制部分变因，不使设备执行本身变成确定性。来源random可能首次获取ShareGPT；离线环境应预置数据并显式dataset-path，不能把下载时间算成推理性能。

TPOT不含首token：每请求(E2E−TTFT)/(output_tokens−1)；ITL是流式token间隔，二者分布不必相同，output1不能据此计算普通TPOT。输出吞吐是完成输出token总数/测试持续时间，请求吞吐是成功数/持续时间；平均并发可按E2E延迟和测试时长解释，但不等于客户端最大并发。峰值瞬时吞吐也不等于整段平均吞吐。

服务token计数、客户端retokenized计数和多模态text/vision计数需分别保留；差异可能来自tokenizer与特殊token，不应直接当模型丢token。示例中AISBench多模态input tokens为0反映统计口径缺失，不能据此说视觉输入没有计算成本。报告应含成功/失败、E2E/TTFT/TPOT/ITL的均值与尾分位，避免只报峰值。

离线吞吐排除了HTTP链路，不能直接解释在线排队或网络时延。使用Profiler时另有插桩扰动，见[采集方法](sglang_ascend_doc_service_profiling.md)；来源未给可用的硬件性能基线，本卡不引用示意数字作为收益。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/evaluation/performance_testing.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/evaluation/performance_testing.mdx)（primary）
