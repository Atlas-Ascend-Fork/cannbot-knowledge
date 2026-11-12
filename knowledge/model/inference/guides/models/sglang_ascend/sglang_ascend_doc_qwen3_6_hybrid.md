---
type: Guide
title: Qwen3.6 在 A3 的多模态与混合状态缓存配置
description: 合并 27B 和 35B-A3B 的 BF16/W8A8、NEXTN、ViT graph、extra_buffer 与超长输入案例。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_6_35b_a3b.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_6_27b.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_6_27b.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_6_35b_a3b.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/Qwen/Qwen3.6.mdx
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/autoregressive/qwen36-deployment.jsx
  role: supporting
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T12:38:11Z'
platforms:
- a3
---

# Qwen3.6 在 A3 的多模态与混合状态缓存配置

## 版本和精度边界

两教程以SGLang v0.5.16编写、采用CANN9.1 A3 B105验证构建；不能推导任意后续版本可兼容。27B是dense hybrid GDN/attention，35B-A3B为hybrid MoE。教程推荐的ModelSlim W8A8权重约36.45GB/39.81GB，可从单64GB die起步，但最佳实践多用TP2或TP4。35B最佳实践的性能行全部标BF16且命令没有quantization，不能将其数值归给教程链接的W8A8权重。

## 先按输入形态选配方

图像混部启用multimodal/ascend_attn、BF16主计算和SSM状态、NEXTN3/1/4。ViT graph通过`SGLANG_VIT_ENABLE_CUDA_GRAPH=1`启用，与LLM decode graph是不同配置；27B的1024²方案还启用DP encoder，1080p方案不含同一开关。prefill-delayer的passes、queue ratio和delay-ms会改变请求排队，需同时观察TTFT和吞吐。

随机长文本通常禁用Radix，限制max-running并单独规划Mamba状态；共享前缀则保留Radix，使用`mamba-radix-cache-strategy extra_buffer`。27B BF16 64K前缀方案max-running20、mamba-cache160；35B 128K前缀方案103/85，64K方案40/200。来源中状态槽不总等于请求上限，不能以单个比例推导实现分配规则，须查实际状态分配与驱逐。27B 128K W8A8 TP4方案没有NEXTN，不能从同页其他命令补开。

35B超长输入254000使用TP2，984000扩到TP4并设置context1010000和允许覆盖更长context；这些运行参数不证明模型原生训练窗口、准确率或百万token质量。

## 上游观测

下表均报告TPOT50ms，另行标出的超长行例外。IMAGE为单图+30文本token；未列明的warmup未知。来源没有独立重复与误差，本次未测。

| 模型/精度 | 输入/输出与资源 | 请求条件 |
|---|---|---|
| 27B BF16，TP2 | 1024²/1024；1080p/256 | 并发60/请求240；并发42/请求152、warmup38 |
| 27B BF16，TP2 | 前缀57600+6400/1000 | 1组20请求/并发20 |
| 27B W8A8，TP2 | 3500/1500；64000/1000 | 54/216；6/12 |
| 27B W8A8，TP4 | 128000/1000；16000/1000；64000/1000 | 4/16；37/37、warmup4；6/24 |
| 35B BF16，TP2 | 1024²/1024；1080p/256 | 120/120、warmup120；42/42、warmup42 |
| 35B BF16，TP2 | 128000/1000；3500/1500；64000/1000 | 3/3；122/122；10/40 |
| 35B BF16，TP2 | 前缀115200+12800/1000；58982+6554/1024 | 并发103/请求412；40/40 |
| 35B BF16，TP2 | 254000/1000，TPOT16.1ms | 1/1、warmup1、seed1 |
| 35B BF16，TP4 | 984000/1000，TPOT40.91ms | 1/1、warmup1、seed1 |

真实缓存命中率需测服务侧；生成90%共享前缀不能代替这一观测。不同精度、设备数、并发、warmup和输出长度的行不能当同工作负载A/B实验。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_6_35b_a3b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_6_35b_a3b.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_6_27b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_6_27b.mdx)（constraint）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_6_27b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_6_27b.mdx)（constraint）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_6_35b_a3b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_6_35b_a3b.mdx)（constraint）

## Cookbook基线生成器与场景配方分开

该生成器的A3分支只提供BF16的27B（权重约54GB）与35B-A3B（约70GB），一物理卡2die→TP2、两卡4die→TP4，nnodes1、static0.7、SSM BF16、ascend attention。MTP开关默认开启，输出NEXTN3/1/4；reasoning/tool parser可选qwen3/qwen3_coder，HTTP30000。27B/35B容量数字不含KV、Mamba状态和运行缓冲。

NPU分支隐藏Mamba-cache UI并不意味着缓存不支持：基线不强制传mamba-radix-cache-strategy，交给安装版本默认；需要前缀缓存时沿完整Ascend配方选extra_buffer。多模态另加enable-multimodal/mm-attention-backend ascend_attn。生成器没有复制本文场景的max-running、graph、prefill延迟器和工作负载，因此引用的50ms/超长输入数值只属于上文完整配方，不是基线命令的测量。成功加载也不代表生成精度通过。

- [docs/cookbook/autoregressive/Qwen/Qwen3.6.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/Qwen/Qwen3.6.mdx)（supporting）
- [docs/src/snippets/autoregressive/qwen36-deployment.jsx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/autoregressive/qwen36-deployment.jsx)（supporting）
