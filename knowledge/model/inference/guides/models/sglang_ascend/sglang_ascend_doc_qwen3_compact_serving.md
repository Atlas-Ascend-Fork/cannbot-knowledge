---
type: Guide
title: Qwen3 小中规模模型在 A3 的延迟与并发配方
description: 比较 8B、30B-A3B 和 32B 的容量起点、EAGLE3、graph、请求负载及 A2 证据边界。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_30b_a3b.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_30b_a3b.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_32b.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_32b.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_8b.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_8b.mdx
  role: constraint
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/Qwen3%20Examples.mdx
  role: primary
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T12:09:58Z'
platforms:
- a2
- a3
---

# Qwen3 小中规模模型在 A3 的延迟与并发配方

## 共同先决条件

三份教程均限定SGLang v0.5.18/CANN9.0 A3镜像；后续版本没有被这些教程覆盖。ModelSlim W8A8与独立EAGLE3 draft需要成组选择，draft设unquant。容量起点不包含目标并发、完整KV和graph开销：8B W8A8约11.27GB，30B-A3B BF16/W8A8约61.08/31.29GB，教程称可从单64GB die起步；32B BF16约65.54GB需TP2，W8A8约42.77GB可容纳于单die。精确工作集仍应实测。

本卡的a2范围只对应32B最佳实践的明确A2条目；其余型号与配置没有从A3外推到A2。该A2条目保留了与A3类似的TP4命令，却写2物理卡，且教程环境仍是A3镜像；不能据此宣称同一镜像/资源计数完整适配A2，须按实际硬件核对。

## 调参的语义

低延迟方案常扩大TP、限制max-running与graph batch，并使用更长draft；吞吐方案扩大运行请求数与图覆盖。比如8B低延迟是TP2、graph1、EAGLE3 4/1/5；其吞吐方案改TP1、max-running70、EAGLE3 3/1/4、chunk16384。30B-A3B的6K方案TP2/max-running16、EAGLE3 4/1/5，3.5K方案用3/1/4且max-running162。32B BF16低延迟扩到TP16，W8A8吞吐为TP4、graph覆盖至101、max-running101。这些配置改变了资源和调度，不能从指标差推导单一技术收益。

32B W8A8命令含`SGLANG_NPU_USE_DEEPGEMM=1`，只是该来源脚本的设置，不等同GPU DeepGEMM接口或所有平台实现支持。三者均有禁用Radix的随机负载配方；有共享前缀流量时应重新评估缓存，而不是照搬。

## 上游结果与异常口径

| 模型/精度/平台 | 工作负载（输入/输出，并发/请求） | 报告TPOT |
|---|---|---|
| 8B W8A8 A3 | RANDOM3500/1500，1/4，seed1 | 5ms |
| 8B W8A8 A3 | RANDOM3500/1500，64/256，seed1 | 37ms |
| 8B W8A8 A3 | 6K/1.5K，16/16 | 11.79ms |
| 30B-A3B W8A8 A3 | RANDOM3500/1500，1/1，seed1 | 10ms |
| 同模型 | 同长度，160/640，seed1 | 50ms |
| 同模型 | RANDOM6144/1500，16/16 | 10.25ms |
| 32B BF16 A3，8卡 | RANDOM18000/4000，1/1，seed1 | 6ms |
| 32B W8A8 A3，2卡 | RANDOM3584/1536，100/400，seed1 | 50ms |
| 32B W8A8 A2，页面称2卡 | 同长度/并发/请求 | 55ms |

30B-A3B BF16一行另报告10000ms，命令为1000/100、并发162/请求624；数值看起来异常但来源没有更正依据，本卡不把它作为可信基线计算W8A8加速比。所有表行缺独立重复次数、误差与完整warmup信息，本次没有测量。应先保存实际设备、权重、版本与生效graph批次，再同负载比较TTFT、TPOT、吞吐和HBM。


## 旧版 Qwen3 入门命令

旧仓A3例子使用Qwen32B TP4，EAGLE3额外设steps1/topk1/draft2，与当前低延迟/吞吐配方不同。其Qwen30B-A3B MoE用TP4并设BF16 dispatch；Qwen235 BF16用TP16；Qwen3-VL8B用TP4、multimodal和ascend_attn。它们没有正式性能数字。旧32B draft下载链接和启动参数中的模型标识不同，应核对实际draft与target tokenizer/checkpoint，而非把示例路径当已匹配。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_30b_a3b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_30b_a3b.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_30b_a3b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_30b_a3b.mdx)（constraint）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_32b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_32b.mdx)（constraint）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_32b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_32b.mdx)（constraint）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_8b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_8b.mdx)（constraint）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_8b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_8b.mdx)（constraint）
- [sgl_docs：docs/hardware-platforms/ascend-npus/Qwen3 Examples.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/Qwen3%20Examples.mdx)（primary）
